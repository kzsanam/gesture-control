"""
Collect gesture training data.

Controls:
  0 - label: default (no pinch)
  1 - label: index pinch
  2 - label: middle pinch
  3 - label: ring pinch
  s - start/stop recording for current label
  q - quit and save
"""

import csv
import math
import os

import cv2
import mediapipe as mp

from hand_mouse.features import extract_features

LABELS = {
    ord("0"): "default",
    ord("1"): "index_pinch",
    ord("2"): "middle_pinch",
    ord("3"): "ring_pinch",
}

PINCH_FINGERS = {
    "index_pinch": 8,
    "middle_pinch": 12,
    "ring_pinch": 16,
}

PINCH_ON = 0.2  # record pinch when normalized dist < this
PINCH_OFF = 0.15  # record default when ALL normalized dists > this


def _pinch_distance(hand, finger_idx) -> float:
    wrist = hand.landmark[0]
    middle_mcp = hand.landmark[9]
    hand_size = math.sqrt((wrist.x - middle_mcp.x) ** 2 + (wrist.y - middle_mcp.y) ** 2)
    thumb = hand.landmark[4]
    tip = hand.landmark[finger_idx]
    dist = math.sqrt((thumb.x - tip.x) ** 2 + (thumb.y - tip.y) ** 2)
    return dist / (hand_size + 1e-6)


def _should_record(label, hand) -> bool:
    if label in PINCH_FINGERS:
        return _pinch_distance(hand, PINCH_FINGERS[label]) < PINCH_ON
    return all(_pinch_distance(hand, idx) > PINCH_OFF for idx in PINCH_FINGERS.values())


OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../../../data/landmarks.csv")


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    rows = []
    current_label = "default"
    recording = False

    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            hand = None
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            if recording and hand is not None and _should_record(current_label, hand):
                rows.append([current_label] + extract_features(hand))

            accepting = hand is not None and _should_record(current_label, hand)
            status_color = (
                (0, 200, 0)
                if (recording and accepting)
                else (0, 100, 200) if recording else (0, 0, 200)
            )
            cv2.putText(
                frame,
                f"Label: {current_label}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )
            status = (
                "RECORDING"
                if (recording and accepting)
                else "PAUSED" if not recording else "RECORDING (rejected)"
            )
            cv2.putText(
                frame,
                f"{status}  samples: {len(rows)}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                status_color,
                2,
            )
            cv2.putText(
                frame,
                "0-3: select label  s: toggle record  q: quit+save",
                (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )

            cv2.imshow("Collect", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            elif key == ord("s"):
                recording = not recording
            elif key in LABELS:
                current_label = LABELS[key]
                recording = False

    cap.release()
    cv2.destroyAllWindows()

    if rows:
        n_features = len(rows[0]) - 1
        fieldnames = ["label"] + [f"f{i}" for i in range(n_features)]
        write_header = not os.path.exists(OUTPUT_PATH)
        with open(OUTPUT_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            for row in rows:
                writer.writerow(dict(zip(fieldnames, row, strict=True)))
        print(f"Saved {len(rows)} samples to {OUTPUT_PATH}")
    else:
        print("No samples collected.")


if __name__ == "__main__":
    main()
