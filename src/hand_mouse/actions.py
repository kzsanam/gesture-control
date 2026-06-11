import time
from enum import Enum

import pyautogui

from hand_mouse.gestures import Gesture


class ActionEnum(Enum):
    IDLE = 0
    CLICK = 1
    MOVE = 2
    HOLD = 3
    SCROLL = 4
    DRAG = 5
    RIGHT_CLICK = 6


class ActionRunner:
    screen_w, screen_h = pyautogui.size()

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    prev_scroll_y, prev_x, prev_y = None, 0, 0
    mouse_x = 0
    mouse_y = 0

    SMOOTHING = 0.2
    DEADZONE = 0.0005

    def rightClick(self):
        print("RIGHT CLICK")
        pyautogui.rightClick()
        time.sleep(0.2)

    def leftClick(self):
        print("CLICK")
        pyautogui.click()

    def drag(self):
        print("DRAGGING")
        pyautogui.mouseDown()

    def move(self, hand, screen_w, screen_h):
        index = hand.landmark[8]

        if self.prev_x == 0 and self.prev_y == 0:
            self.prev_x = index.x
            self.prev_y = index.y

        x = index.x
        y = index.y

        smooth_x = self.prev_x + self.SMOOTHING * (x - self.prev_x)
        smooth_y = self.prev_y + self.SMOOTHING * (y - self.prev_y)

        d_x = smooth_x - self.prev_x
        d_y = smooth_y - self.prev_y

        if abs(d_x) < self.DEADZONE:
            d_x = 0

        if abs(d_y) < self.DEADZONE:
            d_y = 0

        self.prev_x = smooth_x
        self.prev_y = smooth_y

        if self.mouse_x == 0 and self.mouse_y == 0:
            self.mouse_x = max(0, int(smooth_x * self.screen_w))
            self.mouse_y = max(0, int(smooth_y * self.screen_h))
        else:
            self.mouse_x = int(self.mouse_x + d_x * self.screen_w * 8)
            self.mouse_y = int(self.mouse_y + d_y * self.screen_h * 8)

        pyautogui.moveTo(self.mouse_x, self.mouse_y)

    SCROLL_SENSITIVITY = 500
    DEAD_LINE = 0.002
    def scroll(self, hand):
        print("SCROLL")
        middle = hand.landmark[12]
        if self.prev_scroll_y is None:
            self.prev_scroll_y = middle.y

        dy = middle.y - self.prev_scroll_y

        print(f"scroll: {dy}")
        if abs(dy) > self.DEAD_LINE:
            pyautogui.scroll(int(dy * self.SCROLL_SENSITIVITY))

        self.prev_scroll_y = middle.y

    CLICK_TIME = 0.2
    pinch_start_time = 0
    first_click_start = 0
    actionEnum = ActionEnum.IDLE
    prevActionEnum = ActionEnum.IDLE

    def _selectAction(self, gesture) -> ActionEnum:
        now = time.time()
        action_out = self.actionEnum
        match gesture:
            case Gesture.INDEX_PINCH:
                if self.actionEnum != ActionEnum.MOVE:
                    if self.actionEnum != ActionEnum.HOLD:
                        self.pinch_start_time = now
                        action_out = ActionEnum.HOLD
                    else:
                        if now - self.pinch_start_time > self.CLICK_TIME:
                            if now - self.first_click_start > 2 * self.CLICK_TIME:
                                action_out = ActionEnum.MOVE
                            else:
                                action_out = ActionEnum.DRAG
            case Gesture.MIDDLE_PINCH:
                action_out = ActionEnum.SCROLL
            case Gesture.RING_PINCH:
                action_out = ActionEnum.RIGHT_CLICK
            case Gesture.Default:
                if self.actionEnum == ActionEnum.HOLD:
                    if now - self.pinch_start_time <= self.CLICK_TIME:
                        self.first_click_start = now
                        action_out = ActionEnum.CLICK
                    else:
                        action_out = ActionEnum.IDLE
                else:
                    # if action == Action.DRAG:
                    #     action = Action.RELEASE_DRAG
                    # else:
                    action_out = ActionEnum.IDLE
                self.pinch_start_time = 0
        return action_out

    def run(self, gesture, hand):
        self.prevActionEnum = self.actionEnum
        self.actionEnum = self._selectAction(gesture)
        match self.actionEnum:
            case ActionEnum.IDLE:
                pass
            case ActionEnum.CLICK:
                self.leftClick()
            case ActionEnum.MOVE:
                if (self.prevActionEnum != self.actionEnum):
                    self.prev_x = 0
                    self.prev_y = 0
                self.move(hand, self.screen_w, self.screen_h)
            case ActionEnum.HOLD:
                pass
            case ActionEnum.SCROLL:
                if (self.prevActionEnum != self.actionEnum):
                    self.prev_scroll_y = None
                self.scroll(hand)
            case ActionEnum.DRAG:
                self.drag()
            case ActionEnum.RIGHT_CLICK:
                self.rightClick()
