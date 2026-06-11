import cv2
import mediapipe as mp

from hand_mouse.actions import ActionRunner
from hand_mouse.gestures import detectGesture


def main():
    cap = cv2.VideoCapture(0)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    actionRunner = ActionRunner()

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        while True:
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]

                index = hand.landmark[8]
                middle = hand.landmark[12]
                thumb = hand.landmark[4]

                gesture = detectGesture(hand)
                actionRunner.run(gesture, hand)

                # debug point
                mp_draw.draw_landmarks(
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS,
                )

                cv2.circle(
                    frame, (int(index.x * w), int(index.y * h)), 10, (0, 0, 255), -1
                )
                cv2.circle(
                    frame, (int(thumb.x * w), int(thumb.y * h)), 10, (0, 0, 255), -1
                )
                cv2.circle(
                    frame, (int(middle.x * w), int(middle.y * h)), 10, (0, 0, 255), -1
                )
                cv2.circle(
                    frame,
                    (int(hand.landmark[16].x * w), int(hand.landmark[16].y * h)),
                    10,
                    (0, 0, 255),
                    -1,
                )
            cv2.imshow("Hand Mouse", frame)

            if cv2.waitKey(1) == 27:
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
