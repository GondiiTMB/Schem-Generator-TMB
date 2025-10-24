from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import torch
from torch import nn


class ResidualBlock3D(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv3d(channels, channels, kernel_size=3, padding=1)
        self.norm1 = nn.BatchNorm3d(channels)
        self.conv2 = nn.Conv3d(channels, channels, kernel_size=3, padding=1)
        self.norm2 = nn.BatchNorm3d(channels)
        self.activation = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        residual = x
        out = self.activation(self.norm1(self.conv1(x)))
        out = self.norm2(self.conv2(out))
        out += residual
        return self.activation(out)


class TextConditionedVAE(nn.Module):
    def __init__(
        self,
        *,
        vocab_size: int,
        text_dim: int,
        latent_dim: int = 128,
    ) -> None:
        super().__init__()
        channels = 32
        self.embedding = nn.Linear(vocab_size, channels)
        self.encoder = nn.Sequential(
            nn.Conv3d(channels, 64, kernel_size=3, padding=1),
            nn.BatchNorm3d(64),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv3d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm3d(128),
            nn.LeakyReLU(0.2, inplace=True),
            ResidualBlock3D(128),
            nn.Conv3d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm3d(256),
            nn.LeakyReLU(0.2, inplace=True),
            ResidualBlock3D(256),
        )
        self.flatten = nn.AdaptiveAvgPool3d(1)
        self.fc_mu = nn.Linear(256 + text_dim, latent_dim)
        self.fc_logvar = nn.Linear(256 + text_dim, latent_dim)
        self.fc_decode = nn.Linear(latent_dim + text_dim, 256)
        self.decoder = nn.Sequential(
            nn.ConvTranspose3d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm3d(128),
            nn.LeakyReLU(0.2, inplace=True),
            ResidualBlock3D(128),
            nn.ConvTranspose3d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm3d(64),
            nn.LeakyReLU(0.2, inplace=True),
            ResidualBlock3D(64),
            nn.Conv3d(64, vocab_size, kernel_size=3, padding=1),
        )

    def encode(self, x: torch.Tensor, text: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        embed = self.embedding(x)
        features = self.encoder(embed)
        pooled = self.flatten(features).squeeze(-1).squeeze(-1).squeeze(-1)
        merged = torch.cat([pooled, text], dim=-1)
        mu = self.fc_mu(merged)
        logvar = self.fc_logvar(merged)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor, text: torch.Tensor) -> torch.Tensor:
        merged = torch.cat([z, text], dim=-1)
        features = self.fc_decode(merged)
        features = features.unsqueeze(-1).unsqueeze(-1).unsqueeze(-1)
        out = self.decoder(features)
        return out

    def forward(self, x: torch.Tensor, text: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:  # type: ignore[override]
        mu, logvar = self.encode(x, text)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z, text)
        return recon, mu, logvar


@dataclass
class ModelBundle:
    model: TextConditionedVAE
    vocab_size: int
    text_dim: int

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": self.model.state_dict(),
            "vocab_size": self.vocab_size,
            "text_dim": self.text_dim,
        }, path)

    @classmethod
    def load(cls, path: Path, latent_dim: int = 128) -> "ModelBundle":
        checkpoint = torch.load(path, map_location="cpu")
        model = TextConditionedVAE(
            vocab_size=checkpoint["vocab_size"],
            text_dim=checkpoint["text_dim"],
            latent_dim=latent_dim,
        )
        model.load_state_dict(checkpoint["state_dict"])
        return cls(model=model, vocab_size=checkpoint["vocab_size"], text_dim=checkpoint["text_dim"])
