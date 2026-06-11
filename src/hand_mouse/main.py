import queue
import threading

import cv2
import mediapipe as mp

from hand_mouse.actions import ActionRunner
from hand_mouse.gestures import detectGesture


def camera_thread(frame_queue: queue.Queue, stop_event: threading.Event):
    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        while not stop_event.is_set():
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            hand = None
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                for idx in [8, 4, 12, 16]:
                    lm = hand.landmark[idx]
                    cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 10, (0, 0, 255), -1)

            try:
                frame_queue.put_nowait((frame, hand))
            except queue.Full:
                pass  # drop stale frame, control thread will get the next one

            cv2.imshow("Hand Mouse", frame)
            if cv2.waitKey(1) == 27:
                stop_event.set()

    cap.release()
    cv2.destroyAllWindows()


def control_thread(frame_queue: queue.Queue, stop_event: threading.Event):
    runner = ActionRunner()

    while not stop_event.is_set():
        try:
            _frame, hand = frame_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if hand is not None:
            gesture = detectGesture(hand)
            runner.run(gesture, hand)


def main():
    stop_event = threading.Event()
    frame_queue = queue.Queue(maxsize=1)

    cam = threading.Thread(target=camera_thread, args=(frame_queue, stop_event), daemon=True)
    ctrl = threading.Thread(target=control_thread, args=(frame_queue, stop_event), daemon=True)

    cam.start()
    ctrl.start()

    cam.join()
    stop_event.set()
    ctrl.join()


if __name__ == "__main__":
    main()
