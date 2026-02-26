import torch
import torch.nn as nn
import torchvision.models as models


class ResNetTextureFusion(nn.Module):
    def __init__(self):
        super(ResNetTextureFusion, self).__init__()

        # Pretrained ResNet18 backbone
        self.backbone = models.resnet18(weights=None)

        # Remove final FC
        self.backbone.fc = nn.Identity()  # Output = 512 features

        # Texture branch
        self.tex_fc = nn.Linear(12, 64)

        # Fusion classifier
        self.classifier = nn.Sequential(
            nn.Linear(512 + 64, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 2)
        )

    def forward(self, image, texture):
        img_feat = self.backbone(image)   # [B, 512]
        tex_feat = self.tex_fc(texture)   # [B, 64]

        fused = torch.cat([img_feat, tex_feat], dim=1)

        return self.classifier(fused)
