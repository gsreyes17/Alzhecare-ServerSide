from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from inference_sdk import InferenceHTTPClient

from app.core.config import get_settings


class RoboflowService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=settings.roboflow_api_key,
        )
        self.workspace = settings.roboflow_workspace
        self.workflow_id = settings.roboflow_workflow_id
        self.translations = {
            "Very_Mild_Demented": "Demencia muy leve",
            "Mild_Demented": "Demencia leve",
            "Non_Demented": "Sin demencia",
            "Moderate_Demented": "Demencia moderada",
        }

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        try:
            result = await run_in_threadpool(
                self.client.run_workflow,
                workspace_name=self.workspace,
                workflow_id=self.workflow_id,
                images={"image": image_path},
                use_cache=True,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Error calling Roboflow: {exc}") from exc

        if not result or not isinstance(result, list):
            raise HTTPException(status_code=400, detail="Invalid Roboflow response")

        payload = result[0]
        prediction = self._extract_classification(payload)
        if not prediction:
            raise HTTPException(status_code=400, detail="No classification found")

        class_name = prediction.get("class")
        confidence = float(prediction.get("confidence", 0.0))
        label = self.translations.get(class_name, class_name or "Unknown")

        return {
            "class_name": class_name,
            "result_label": label,
            "confidence": confidence,
            "raw": payload,
        }

    def _extract_classification(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cp = payload.get("classification_predictions")
        if isinstance(cp, list) and cp:
            pred_wrapper = cp[0].get("predictions", {})
            preds = pred_wrapper.get("predictions", [])
            if isinstance(preds, list) and preds:
                return preds[0]

        predictions = payload.get("predictions", {}).get("predictions", [])
        if isinstance(predictions, list) and predictions:
            return predictions[0]

        return self._find_prediction_recursive(payload)

    def _find_prediction_recursive(self, obj: Any, depth: int = 0) -> Optional[Dict[str, Any]]:
        if depth > 5:
            return None

        if isinstance(obj, dict):
            if "class" in obj and "confidence" in obj:
                return obj
            for value in obj.values():
                found = self._find_prediction_recursive(value, depth + 1)
                if found:
                    return found

        if isinstance(obj, list):
            for item in obj:
                found = self._find_prediction_recursive(item, depth + 1)
                if found:
                    return found

        return None


roboflow_service = RoboflowService()
