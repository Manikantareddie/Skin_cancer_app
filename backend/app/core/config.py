from pathlib import Path
from typing import List, Union
import json
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Skin Cancer Detection & CDSS"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "https://skin-cancer-app-three.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    # Regex to automatically accept all Vercel production and preview domains
    ALLOWED_ORIGIN_REGEX: str = r"^https:\/\/.*\.vercel\.app$"

    # Model & Storage Settings
    MODEL_REPO_ID: str = "reddysorgs/skin-cancer-cdss-model"
    MODEL_FILENAME: str = "final_resnet_texture_model.pth"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODEL_DIR: Path = DATA_DIR / "models"
    DEVICE: str = "cpu"

    # NVIDIA NIM / API Configuration
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("MODEL_DIR", mode="before")
    @classmethod
    def parse_model_dir(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    def get_allowed_origins(self) -> List[str]:
        """Resolves allowed origins list, stripping trailing slashes and whitespace."""
        raw_list = []
        if isinstance(self.ALLOWED_ORIGINS, list):
            raw_list = self.ALLOWED_ORIGINS
        elif isinstance(self.ALLOWED_ORIGINS, str):
            val = self.ALLOWED_ORIGINS.strip()
            if val.startswith("[") and val.endswith("]"):
                try:
                    raw_list = json.loads(val)
                except Exception:
                    raw_list = [orig.strip() for orig in val.strip("[]").split(",") if orig.strip()]
            else:
                raw_list = [orig.strip() for orig in val.split(",") if orig.strip()]
        else:
            raw_list = ["https://skin-cancer-app-three.vercel.app", "http://localhost:5173"]

        cleaned = []
        for o in raw_list:
            if isinstance(o, str):
                cleaned_o = o.strip().rstrip("/")
                if cleaned_o and cleaned_o not in cleaned:
                    cleaned.append(cleaned_o)
        return cleaned


settings = Settings()
