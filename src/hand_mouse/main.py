import math
import time
from abc import ABC, abstractmethod
from enum import Enum

import cv2
import mediapipe as mp
import pyautogui


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


# class Gesture(ABC):

#     @abstractmethod
#     def isTrue(self) -> bool:
#         pass


# class Pinch(Gesture):
#     def isTrue(self, hand):
#         wrist = hand.landmark[0]
#         middle_mcp = hand.landmark[9]
#         thumb = hand.landmark[4]
#         hand_size = distance(wrist, middle_mcp)

#         middle = hand.landmark[12]
#         return distance(thumb, middle) / hand_size < 0.17


def isMiddlePinch(hand) -> bool:
    middle = hand.landmark[12]
    wrist = hand.landmark[0]
    middle_mcp = hand.landmark[9]
    thumb = hand.landmark[4]
    hand_size = distance(wrist, middle_mcp)

    return distance(thumb, middle) / hand_size < 0.15


def isPinch(hand) -> bool:
    index = hand.landmark[8]
    thumb = hand.landmark[4]
    wrist = hand.landmark[0]
    middle_mcp = hand.landmark[9]

    hand_size = distance(wrist, middle_mcp)

    pinch_ratio = distance(thumb, index) / hand_size
    return pinch_ratio < 0.15


def isRingPinch(hand) -> bool:
    ring = hand.landmark[16]
    thumb = hand.landmark[4]
    wrist = hand.landmark[0]
    middle_mcp = hand.landmark[9]

    hand_size = distance(wrist, middle_mcp)

    pinch_ratio = distance(thumb, ring) / hand_size
    return pinch_ratio < 0.2

class Gesture(Enum):
    Default = 0
    INDEX_PINCH = 1
    MIDDLE_PINCH = 2
    RING_PINCH = 3

class Action(Enum):
    IDLE = 0
    CLICK = 1
    MOVE = 2
    HOLD = 3
    SCROLL = 4
    DRAG = 5
    RIGHT_CLICK = 6

def detectGesture(hand):
    if isPinch(hand):
        return Gesture.INDEX_PINCH
    if isMiddlePinch(hand):
        return Gesture.MIDDLE_PINCH
    if isRingPinch(hand):
        return Gesture.RING_PINCH
    return Gesture.Default

def selectAction(gesture, action, pinch_start_time, first_click_start) -> Action:
    now = time.time()
    action_out = action
    match gesture:
        case Gesture.INDEX_PINCH:
            if action != Action.MOVE:
                if action != Action.HOLD:
                    pinch_start_time = now
                    action_out = Action.HOLD
                else:
                    if now - pinch_start_time > 0.2:
                        if now - first_click_start > 0.4:
                            action_out = Action.MOVE
                        else:
                            action_out = Action.DRAG
        case Gesture.MIDDLE_PINCH:
            action_out = Action.SCROLL
        case Gesture.RING_PINCH:
            action_out = Action.RIGHT_CLICK
        case Gesture.Default:
            if action == Action.HOLD:
                if now - pinch_start_time <= 0.2:
                    first_click_start = now
                    action_out = Action.CLICK
                else:
                    action_out = Action.IDLE
            else:
                # if action == Action.DRAG:
                #     action = Action.RELEASE_DRAG
                # else:
                action_out = Action.IDLE
            pinch_start_time = 0

    return action_out, pinch_start_time, first_click_start


def main():
    CLICK_THRESHOLD = 0.06
    SMOOTHING = 0.2

    SCROLL_SENSITIVITY = 500
    SCROLL_MODE_THRESHOLD = 0.05
    DEADZONE = 0.0005

    cap = cv2.VideoCapture(0)
    screen_w, screen_h = pyautogui.size()

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    prev_x, prev_y = 0, 0
    action = Action.IDLE
    mouse_x = 0
    mouse_y = 0
    pinch_start_time = 0
    first_click_start = 0
    prev_scroll_y = 0

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
                action, pinch_start_time, first_click_start = selectAction(
                    gesture, action, pinch_start_time, first_click_start
                )
                print(f"ACTION: {action}")
                # right click
                if action == Action.RIGHT_CLICK:
                    print("RIGHT CLICK")
                    pyautogui.rightClick()
                    time.sleep(0.2)

                # click
                if action == Action.CLICK:
                    print("CLICKING")
                    pyautogui.click()

                # drag
                if action == Action.DRAG:
                    print("DRAGGING")
                    pyautogui.mouseDown()

                # control mouse
                if action == Action.MOVE:  # or action == Action.CLICK_AND_CONTROL:
                    # print("CONTROLLING")
                    if prev_x == 0 and prev_y == 0:
                        prev_x = index.x
                        prev_y = index.y
                        # prev_x = (index.x + thumb.x)/2
                        # prev_y = (index.y + thumb.x)/2

                    x = index.x
                    y = index.y

                    smooth_x = prev_x + SMOOTHING * (x - prev_x)
                    smooth_y = prev_y + SMOOTHING * (y - prev_y)

                    d_x, d_y = smooth_x - prev_x, smooth_y - prev_y
                    if abs(d_x) < DEADZONE:
                        d_x = 0
                    if abs(d_y) < DEADZONE:
                        d_y = 0
                    prev_x, prev_y = smooth_x, smooth_y

                    if mouse_x == 0 and mouse_y == 0:
                        mouse_x = max(0, int(smooth_x * screen_w))
                        mouse_y = max(0, int(smooth_y * screen_h))
                    else:
                        mouse_x = int(mouse_x + d_x * screen_w * 8)
                        mouse_y = int(mouse_y + d_y * screen_h * 8)
                    pyautogui.moveTo(mouse_x, mouse_y)
                else:
                    prev_x, prev_y = 0, 0

                # scroll
                if action == Action.SCROLL:
                    print("SCROLL")
                    if prev_scroll_y is None:
                        prev_scroll_y = middle.y

                    dy = middle.y - prev_scroll_y

                    print(f"scroll: {dy}")

                    if abs(dy) > 0.002:
                        pyautogui.scroll(int(dy * SCROLL_SENSITIVITY))

                    prev_scroll_y = middle.y
                else:
                    prev_scroll_y = None

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
