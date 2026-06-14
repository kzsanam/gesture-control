import os
import pickle

from hand_mouse.app.gestures import Gesture

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../../data/gesture_model.pkl")

with open(MODEL_PATH, "rb") as f:
    _data = pickle.load(f)

_model = _data["model"]
_label_encoder = _data["label_encoder"]


_LABEL_MAP = {
    "default": Gesture.Default,
    "index_pinch": Gesture.INDEX_PINCH,
    "middle_pinch": Gesture.MIDDLE_PINCH,
    "ring_pinch": Gesture.RING_PINCH,
}


def _extract_features(hand) -> list[float]:
    wrist = hand.landmark[0]
    middle_mcp = hand.landmark[9]
    scale = ((wrist.x - middle_mcp.x) ** 2 + (wrist.y - middle_mcp.y) ** 2) ** 0.5

    features = []
    for lm in hand.landmark:
        features.append((lm.x - wrist.x) / (scale + 1e-6))
        features.append((lm.y - wrist.y) / (scale + 1e-6))
        features.append((lm.z - wrist.z) / (scale + 1e-6))
    return features


def detectGesture(hand) -> Gesture:
    features = _extract_features(hand)
    label_idx = _model.predict([features])[0]
    label = _label_encoder.inverse_transform([label_idx])[0]
    return _LABEL_MAP.get(label, Gesture.Default)
