import os
import pickle

from hand_mouse.app.gesture_recognition.gesture_recognition import GestureRecognition
from hand_mouse.app.states import Gesture


class MLGestureRecognition(GestureRecognition):
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../../../data/gesture_model.pkl")

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


    def _extract_features(self, hand) -> list[float]:
        wrist = hand.landmark[0]
        middle_mcp = hand.landmark[9]
        scale = ((wrist.x - middle_mcp.x) ** 2 + (wrist.y - middle_mcp.y) ** 2) ** 0.5

        features = []
        for lm in hand.landmark:
            features.append((lm.x - wrist.x) / (scale + 1e-6))
            features.append((lm.y - wrist.y) / (scale + 1e-6))
            features.append((lm.z - wrist.z) / (scale + 1e-6))
        return features


    def detect_gesture(self, hand) -> Gesture:
        features = self._extract_features(hand)
        proba = self._model.predict_proba([features])[0]
        label_idx = proba.argmax()
        confidence = proba[label_idx]
        label = self._label_encoder.inverse_transform([label_idx])[0]
        print(f"{label} ({confidence:.2f})")
        # make index pinch more sestitive
        if label == "index_pinch" and confidence < 0.8:
            label = "default"
        return self._LABEL_MAP.get(label, Gesture.Default)
