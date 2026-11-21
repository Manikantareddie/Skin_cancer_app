import base64
import io
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import torch
from huggingface_hub import hf_hub_download

from backend.app.core.config import settings
from backend.app.ml.gradcam import GradCAM, overlay_heatmap_on_image
from backend.app.ml.model import ResNetTextureFusion
from backend.app.ml.utils import extract_texture_features, preprocess_image
from backend.app.schemas.analysis import ModelStatusResponse, PredictionResult


class ModelService:
    _instance: Optional["ModelService"] = None

    def __init__(self):
        self.model: Optional[ResNetTextureFusion] = None
        self.gradcam: Optional[GradCAM] = None
        self.model_path: Optional[str] = None
        self.is_loaded: bool = False
        self.device = torch.device(settings.DEVICE)

    @classmethod
    def get_instance(cls) -> "ModelService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self, force_reload: bool = False) -> None:
        """Loads the ResNetTextureFusion model checkpoint with local caching in data/models/."""
        if self.is_loaded and not force_reload:
            return

        settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        local_target_path = settings.MODEL_DIR / settings.MODEL_FILENAME

        if local_target_path.exists():
            resolved_path = str(local_target_path)
        else:
            # Download from Hugging Face Hub and cache locally in data/models
            downloaded_path = hf_hub_download(
                repo_id=settings.MODEL_REPO_ID,
                filename=settings.MODEL_FILENAME,
            )
            # Copy to project's data/models directory for persistent local caching
            shutil.copy2(downloaded_path, str(local_target_path))
            resolved_path = str(local_target_path)

        # Instantiate model architecture
        model = ResNetTextureFusion()
        state_dict = torch.load(resolved_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()

        self.model = model
        # Target the last BasicBlock in ResNet-18 layer4 for Grad-CAM
        self.gradcam = GradCAM(model, model.backbone.layer4[-1])
        self.model_path = resolved_path
        self.is_loaded = True

    def get_status(self) -> ModelStatusResponse:
        return ModelStatusResponse(
            is_loaded=self.is_loaded,
            model_path=self.model_path,
            device=str(self.device),
            architecture="ResNet18 + 12-Feature Texture Fusion",
        )

    def predict(
        self, pil_image: Image.Image
    ) -> Tuple[PredictionResult, str, Image.Image]:
        """
        Runs model inference and Grad-CAM generation.
        Returns (PredictionResult, heatmap_base64, heatmap_pil_image).
        """
        if not self.is_loaded or self.model is None or self.gradcam is None:
            self.load_model()

        assert self.model is not None
        assert self.gradcam is not None

        # Preprocess image and extract texture features using original logic
        image_tensor = preprocess_image(pil_image).to(self.device)
        texture_tensor = extract_texture_features(pil_image).to(self.device)

        # Run model inference
        with torch.no_grad():
            outputs = self.model(image_tensor, texture_tensor)
            probs = torch.softmax(outputs, dim=1)
            confidence, pred = torch.max(probs, dim=1)

        label_map = {0: "Benign", 1: "Malignant"}
        predicted_label = label_map[pred.item()]
        confidence_score = float(confidence.item() * 100)
        benign_probability = float(probs[0, 0].item() * 100)
        malignant_probability = float(probs[0, 1].item() * 100)

        if malignant_probability >= 70:
            model_risk_label, model_risk_class = "HIGH RISK", "high"
        elif malignant_probability >= 35:
            model_risk_label, model_risk_class = "MODERATE RISK", "mid"
        else:
            model_risk_label, model_risk_class = "LOW RISK", "low"

        # Generate Grad-CAM activation map
        cam = self.gradcam.generate(image_tensor, texture_tensor)
        heatmap_overlay = overlay_heatmap_on_image(pil_image, cam)
        heatmap_pil = Image.fromarray(heatmap_overlay)

        # Convert overlay to base64 data URL for frontend
        buffer = io.BytesIO()
        heatmap_pil.save(buffer, format="PNG")
        b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        heatmap_data_url = f"data:image/png;base64,{b64_str}"

        prediction_result = PredictionResult(
            predicted_label=predicted_label,
            confidence_score=confidence_score,
            benign_probability=benign_probability,
            malignant_probability=malignant_probability,
            model_risk_label=model_risk_label,
            model_risk_class=model_risk_class,
        )

        return prediction_result, heatmap_data_url, heatmap_pil


model_service = ModelService.get_instance()
