import os
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np

from ml.features import build_features

LABELS = {0: "empty", 1: "occupied"}

_DEFAULT_MODEL = Path(__file__).resolve().parent.parent / "models" / "occupancy_mlp.pkl"

_model_bundle = None
_model_path = None


def _resolve_model_path() -> Path:
    env_path = os.getenv("ML_MODEL_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_MODEL


def load_model(model_path: Path | None = None) -> bool:
    """Load MLP from disk. Returns True if loaded successfully."""
    global _model_bundle, _model_path

    path = model_path or _resolve_model_path()
    if not path.is_file():
        return False

    _model_bundle = joblib.load(path)
    _model_path = path
    return True


def is_loaded() -> bool:
    return _model_bundle is not None


def get_model_info() -> dict:
    if not is_loaded():
        return {"loaded": False, "path": str(_resolve_model_path())}
    return {
        "loaded": True,
        "path": str(_model_path),
        "features": _model_bundle.get("feature_names", []),
        "accuracy": _model_bundle.get("accuracy"),
    }


def predict_occupancy(motion: bool, received_at: datetime | None = None) -> dict:
    """
    Run MLP inference. Returns prediction label, LED command, and confidence.
    """
    if not is_loaded() and not load_model():
        raise FileNotFoundError(
            f"ML model not found at {_resolve_model_path()}. Run: python train_model.py"
        )

    model = _model_bundle["model"]
    features = np.array([build_features(motion, received_at)], dtype=np.float64)

    class_id = int(model.predict(features)[0])
    proba = model.predict_proba(features)[0]
    confidence = float(proba[class_id])

    prediction = LABELS.get(class_id, "empty")
    led_command = prediction == "occupied"

    return {
        "prediction": prediction,
        "led_command": led_command,
        "confidence": round(confidence, 4),
        "model": "MLP",
    }
