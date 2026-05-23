"""Feature extraction for occupancy MLP (cloud inference)."""
from datetime import datetime, timezone
import math


FEATURE_NAMES = ["motion", "hour_sin", "hour_cos", "is_weekend"]


def build_features(motion: bool, received_at: datetime | None = None) -> list[float]:
    """
    Build input vector for the MLP.

    ESP32 sends only motion; the API adds time context at inference time.
    """
    if received_at is None:
        received_at = datetime.now(timezone.utc)

    hour = received_at.hour
    hour_rad = 2 * math.pi * hour / 24.0
    is_weekend = 1.0 if received_at.weekday() >= 5 else 0.0

    return [
        1.0 if motion else 0.0,
        math.sin(hour_rad),
        math.cos(hour_rad),
        is_weekend,
    ]
