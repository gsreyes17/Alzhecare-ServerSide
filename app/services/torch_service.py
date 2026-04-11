from pathlib import Path
from typing import Any, Dict, List

import pickle
import torch
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from torch import nn
from torchvision import transforms

from app.core.config import get_settings


class CapsuleNet(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, 3, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.fc = nn.Linear(128 * 4 * 4, 256)
        self.classifier = nn.Linear(256, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return self.classifier(x)


class MambaNet(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.fc = nn.Linear(32 * 4 * 4, 256)
        self.classifier = nn.Linear(256, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return self.classifier(x)


class EnsembleModel(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.caps = CapsuleNet(num_classes)
        self.mamba = MambaNet(num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out1 = self.caps(x)
        out2 = self.mamba(x)
        return (out1 + out2) / 2


class TorchService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_path = self._resolve_path(settings.torch_model_path)
        self.classes_path = self._resolve_path(settings.torch_label_classes_path)
        self.device = self._resolve_device(settings.torch_device)

        self.translations = {
            "very mild demented": "Demencia muy leve",
            "very mild dementia": "Demencia muy leve",
            "mild demented": "Demencia leve",
            "mild dementia": "Demencia leve",
            "non demented": "Sin demencia",
            "non dementia": "Sin demencia",
            "non-demented": "Sin demencia",
            "moderate demented": "Demencia moderada",
            "moderate dementia": "Demencia moderada",
        }

        self.model: EnsembleModel | None = None
        self.classes: List[str] = []
        self.transform: transforms.Compose | None = None
        self._load_error: str | None = None

        try:
            self._load_components()
        except Exception as exc:
            self._load_error = str(exc)

    def _resolve_path(self, value: str) -> Path:
        candidate = Path(value)
        if candidate.is_absolute():
            return candidate
        project_root = Path(__file__).resolve().parents[2]
        return project_root / candidate

    def _resolve_device(self, configured_device: str) -> torch.device:
        normalized = configured_device.strip().lower()
        if normalized == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if normalized == "cuda" and not torch.cuda.is_available():
            return torch.device("cpu")
        return torch.device(normalized)

    def _load_components(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"No se encontro el modelo en {self.model_path}")
        if not self.classes_path.exists():
            raise FileNotFoundError(f"No se encontro el archivo de clases en {self.classes_path}")

        with self.classes_path.open("rb") as f:
            loaded_classes = pickle.load(f)

        self.classes = [str(item) for item in loaded_classes]
        if not self.classes:
            raise ValueError("El archivo de clases esta vacio")

        self.model = EnsembleModel(num_classes=len(self.classes)).to(self.device)

        state_dict = torch.load(self.model_path, map_location=self.device)
        if isinstance(state_dict, dict) and "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        self.model.load_state_dict(state_dict)
        self.model.eval()

        self.transform = transforms.Compose(
            [
                transforms.Resize((128, 128)),
                transforms.ToTensor(),
            ]
        )

    def _normalize_class_name(self, class_name: str) -> str:
        return " ".join(class_name.strip().lower().replace("_", " ").replace("-", " ").split())

    def _translate_class(self, class_name: str) -> str:
        normalized = self._normalize_class_name(class_name)
        return self.translations.get(normalized, class_name)

    def _analyze_image_sync(self, image_path: str) -> Dict[str, Any]:
        if self._load_error:
            raise HTTPException(
                status_code=500,
                detail=f"No fue posible inicializar el modelo Torch: {self._load_error}",
            )

        if not self.model or not self.transform:
            raise HTTPException(status_code=500, detail="Modelo Torch no disponible")

        try:
            image = Image.open(image_path).convert("RGB")
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                predicted_prob, predicted_idx = torch.max(probabilities, dim=1)

            idx = int(predicted_idx.item())
            confidence = float(predicted_prob.item())
            class_name = self.classes[idx]
            result_label = self._translate_class(class_name)

            all_probabilities = probabilities.squeeze(0).detach().cpu().tolist()
            raw = {
                "engine": "torch-local",
                "device": str(self.device),
                "model_path": str(self.model_path),
                "predicted_index": idx,
                "probabilities": [
                    {"class_name": self.classes[i], "confidence": float(all_probabilities[i])}
                    for i in range(len(self.classes))
                ],
            }

            return {
                "class_name": class_name,
                "result_label": result_label,
                "confidence": confidence,
                "raw": raw,
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error en inferencia Torch: {exc}") from exc

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        return await run_in_threadpool(self._analyze_image_sync, image_path)


torch_service = TorchService()
