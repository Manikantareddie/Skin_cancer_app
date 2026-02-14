import torch
import torch.nn.functional as F
import cv2
import numpy as np


class GradCAM:
    def __init__(self, model, target_layer):
        """
        model        : CNNWithTexture model
        target_layer : last convolution layer (Conv2d)
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(self.save_gradient)
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]


    def generate(self, image_tensor, texture_tensor, class_idx=None):
        """
        image_tensor   : (1, 3, 224, 224)
        texture_tensor : (1, 12)
        class_idx      : target class (optional)
        """
        self.model.zero_grad()

        outputs = self.model(image_tensor, texture_tensor)

        if class_idx is None:
            class_idx = torch.argmax(outputs, dim=1).item()

        score = outputs[0, class_idx]
        score.backward()

        # Global Average Pooling on gradients
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)

        # Weighted sum of activations
        cam = torch.sum(weights * self.activations, dim=1)

        cam = F.relu(cam)
        cam = cam.squeeze().cpu().numpy()

        # Normalize heatmap
        cam -= cam.min()
        cam /= (cam.max() + 1e-8)

        return cam



def overlay_heatmap_on_image(
    original_image,
    cam,
    alpha=0.4
):
    """
    original_image : PIL Image or numpy array (H, W, 3)
    cam            : Grad-CAM output (Hc, Wc) values in [0,1]
    alpha          : heatmap transparency
    """

    # Convert PIL → numpy if needed
    if not isinstance(original_image, np.ndarray):
        original_image = np.array(original_image)

    # Resize CAM to image size
    cam_resized = cv2.resize(
        cam,
        (original_image.shape[1], original_image.shape[0])
    )

    # Convert to 0–255
    heatmap = np.uint8(255 * cam_resized)

    # Apply color map (medical-style)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    # Convert BGR → RGB
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    # Overlay heatmap on original image
    overlay = cv2.addWeighted(
        original_image,
        1 - alpha,
        heatmap,
        alpha,
        0
    )

    return overlay
