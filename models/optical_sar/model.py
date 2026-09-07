import torch
import torch.nn as nn


class OpticalEncoder(nn.Module):

    def __init__(self, feature_dim=128):

        super().__init__()

        self.encoder = nn.Sequential(

            nn.Conv2d(
                3,
                32,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(32),

            nn.ReLU(),

            nn.MaxPool2d(2),

            nn.Conv2d(
                32,
                64,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(64),

            nn.ReLU(),

            nn.MaxPool2d(2),

            nn.Conv2d(
                64,
                128,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(128),

            nn.ReLU(),

            nn.AdaptiveAvgPool2d((1, 1))
        )

        self.projection = nn.Linear(
            128,
            feature_dim
        )


    def forward(self, x):

        x = self.encoder(x)

        x = torch.flatten(
            x,
            start_dim=1
        )

        x = self.projection(x)

        return x


class SAREncoder(nn.Module):

    def __init__(self, feature_dim=128):

        super().__init__()

        self.encoder = nn.Sequential(

            nn.Conv2d(
                2,
                32,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(32),

            nn.ReLU(),

            nn.MaxPool2d(2),

            nn.Conv2d(
                32,
                64,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(64),

            nn.ReLU(),

            nn.MaxPool2d(2),

            nn.Conv2d(
                64,
                128,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(128),

            nn.ReLU(),

            nn.AdaptiveAvgPool2d((1, 1))
        )

        self.projection = nn.Linear(
            128,
            feature_dim
        )


    def forward(self, x):

        x = self.encoder(x)

        x = torch.flatten(
            x,
            start_dim=1
        )

        x = self.projection(x)

        return x


class OpticalSARModel(nn.Module):

    def __init__(
        self,
        feature_dim=128,
        fused_dim=128
    ):

        super().__init__()

        self.optical_encoder = OpticalEncoder(
            feature_dim
        )

        self.sar_encoder = SAREncoder(
            feature_dim
        )

        self.fusion = nn.Sequential(

            nn.Linear(
                feature_dim * 2,
                fused_dim
            ),

            nn.ReLU(),

            nn.Linear(
                fused_dim,
                fused_dim
            )
        )


    def forward(
        self,
        optical,
        sar
    ):

        optical_features = (
            self.optical_encoder(optical)
        )

        sar_features = (
            self.sar_encoder(sar)
        )

        combined = torch.cat(
            [
                optical_features,
                sar_features
            ],
            dim=1
        )

        fused_features = self.fusion(
            combined
        )

        return {
            "optical_features": optical_features,
            "sar_features": sar_features,
            "fused_features": fused_features
        }