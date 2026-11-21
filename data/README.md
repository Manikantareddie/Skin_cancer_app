# Data Directory

This directory contains local model weights and non-sensitive test assets.

## Directory Structure

```text
data/
├── models/
│   └── final_resnet_texture_model.pth   # Locally cached PyTorch weights (gitignored)
├── samples/
│   ├── sample_benign.png                # Synthetic non-sensitive lesion test image
│   └── sample_malignant.png             # Synthetic non-sensitive lesion test image
└── README.md
```

## Model Checkpoint

- **Hugging Face Repository:** [reddysorgs/skin-cancer-cdss-model](https://huggingface.co/reddysorgs/skin-cancer-cdss-model)
- **File:** `final_resnet_texture_model.pth`
- **Architecture:** ResNet-18 Image Backbone + 12-Feature Handcrafted Texture Fusion
- **Caching Mechanism:** Automatically downloaded via `huggingface_hub.hf_hub_download` on first startup or through `POST /api/v1/model/load`, cached in `data/models/`.
- **Git Policy:** `.pth` model checkpoints are strictly excluded in `.gitignore`.

## Test Assets

Sample images in `data/samples/` are non-sensitive synthetic images generated for smoke testing the pre-inference gate and end-to-end inference pipeline.
