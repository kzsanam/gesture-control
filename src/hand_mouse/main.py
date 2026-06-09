import cv2
import mediapipe as mp
import pyautogui
import math
import time


def distance(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)


def clamp(v, min_v, max_v):
    return max(min_v, min(v, max_v))


def main():
    CLICK_THRESHOLD = 0.03
    CONTROL_MARGIN = 0.4
    SMOOTHING = 0.25
    CLICK_COOLDOWN = 0.25
    DOUBLE_CLICK_WINDOW = 0.3

    SCROLL_SENSITIVITY = 10
    SCROLL_MODE_THRESHOLD = 0.05

    cap = cv2.VideoCapture(0)
    screen_w, screen_h = pyautogui.size()

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    prev_x, prev_y = 0, 0
    prev_scroll_y = None

    last_click = 0
    pending_click_time = None

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

            now = time.time()

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]

                index = hand.landmark[8]
                middle = hand.landmark[12]
                thumb = hand.landmark[4]

                # ---------------------------
                # SCROLL MODE DETECTION
                # ---------------------------
                scroll_mode = distance(index, middle) < 0 #SCROLL_MODE_THRESHOLD

                if scroll_mode:
                    # use vertical movement of index finger
                    if prev_scroll_y is not None:
                        dy = index.y - prev_scroll_y

                        if abs(dy) > 0.002:
                            pyautogui.scroll(int(-dy * SCROLL_SENSITIVITY * 100))

                    prev_scroll_y = index.y

                else:
                    prev_scroll_y = None

                    # ---------------------------
                    # MOUSE MOVE
                    # ---------------------------
                    x = (index.x - CONTROL_MARGIN) / (1 - 2 * CONTROL_MARGIN)
                    y = (index.y - CONTROL_MARGIN) / (1 - 2 * CONTROL_MARGIN)

                    x = clamp(x, 0.0, 1.0)
                    y = clamp(y, 0.0, 1.0)

                    smooth_x = prev_x + SMOOTHING * (x - prev_x)
                    smooth_y = prev_y + SMOOTHING * (y - prev_y)

                    prev_x, prev_y = smooth_x, smooth_y

                    mouse_x = int(smooth_x * screen_w)
                    mouse_y = int(smooth_y * screen_h)

                    pyautogui.moveTo(mouse_x, mouse_y)

                    # ---------------------------
                    # CLICK + DOUBLE CLICK
                    # ---------------------------
                    dist = distance(thumb, index)

                    if dist < CLICK_THRESHOLD and now - last_click > CLICK_COOLDOWN:

                        if pending_click_time and (now - pending_click_time <= DOUBLE_CLICK_WINDOW):
                            pyautogui.doubleClick()
                            pending_click_time = None
                        else:
                            pyautogui.click()
                            pending_click_time = now

                        last_click = now

                # debug point
                mp_draw.draw_landmarks(
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS,
                )

                cv2.circle(frame, (int(index.x * w), int(index.y * h)), 10, (0, 0, 255), -1)
                cv2.circle(frame, (int(thumb.x * w), int(thumb.y * h)), 10, (0, 0, 255), -1)
                cv2.circle(frame, (int(middle.x * w), int(middle.y * h)), 10, (0, 0, 255), -1)

            cv2.imshow("Hand Mouse", frame)

            if cv2.waitKey(1) == 27:
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()