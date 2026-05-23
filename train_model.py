"""
Antrenează MLP pentru clasificare occupied / empty (Varianta 2 - AI în Cloud).

Rulează o dată (sau când reantrenezi):
    python train_model.py

Generează: models/occupancy_mlp.pkl
"""
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.features import FEATURE_NAMES, build_features

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "occupancy_mlp.pkl"
RANDOM_SEED = 42


def generate_training_data(n_samples: int = 3000) -> tuple[np.ndarray, np.ndarray]:
    """
    Date sintetice care simulează parcarea + senzor PIR.
    În producție, înlocuiești cu evenimente reale din Azure (etichetate manual).
    """
    rng = np.random.default_rng(RANDOM_SEED)
    X, y = [], []

    for _ in range(n_samples):
        motion = bool(rng.integers(0, 2))
        hour = int(rng.integers(0, 24))
        weekday = int(rng.integers(0, 7))
        base = datetime(2026, 5, 19 + weekday, hour, 0, 0, tzinfo=timezone.utc)

        if motion:
            occupied = rng.random() < 0.93
        else:
            night = hour < 6 or hour >= 23
            p_empty = 0.92 if night else 0.78
            occupied = rng.random() > p_empty

        label = 1 if occupied else 0
        X.append(build_features(motion, base))
        y.append(label)

    return np.array(X, dtype=np.float64), np.array(y, dtype=np.int64)


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    X, y = generate_training_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=(16, 8),
                    activation="relu",
                    solver="adam",
                    max_iter=500,
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("=== MLP Occupancy Classifier ===")
    print(f"Samples: {len(X)} | Test accuracy: {accuracy:.2%}")
    print(classification_report(y_test, y_pred, target_names=["empty", "occupied"]))
    print(f"Features: {FEATURE_NAMES}")

    bundle = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "labels": {0: "empty", 1: "occupied"},
        "accuracy": round(float(accuracy), 4),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\nModel salvat: {MODEL_PATH}")


if __name__ == "__main__":
    main()
