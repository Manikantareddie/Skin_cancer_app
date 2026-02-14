import torch
import torch.nn as nn

class CNNWithTexture(nn.Module):
    def __init__(self):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.img_fc = nn.Linear(128 * 28 * 28, 256)
        self.tex_fc = nn.Linear(12, 64)

        self.classifier = nn.Sequential(
            nn.ReLU(),
            nn.Linear(320, 128),
            nn.ReLU(),
            nn.Linear(128, 2)
        )

    def forward(self, image, texture):
        x = self.cnn(image)
        x = x.view(x.size(0), -1)
        x = self.img_fc(x)

        t = self.tex_fc(texture)
        return self.classifier(torch.cat([x, t], dim=1))


from model import CNNWithTexture

model = CNNWithTexture()
print(model.cnn)
