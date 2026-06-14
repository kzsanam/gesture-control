import time

import pyautogui

from hand_mouse.app.states import ActionEnum, Gesture


class ActionRunner:
    screen_w, screen_h = pyautogui.size()

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    prev_scroll_y, prev_x, prev_y = None, 0, 0
    mouse_x = 0
    mouse_y = 0

    SMOOTHING = 0.2
    DEADZONE = 0.00025
    MOVE_ACCELERATION = 8

    def right_click(self):
        print("RIGHT CLICK")
        pyautogui.rightClick()

    def left_click(self):
        print("CLICK")
        pyautogui.click()

    def drag(self):
        print("DRAGGING")
        pyautogui.mouseDown()

    def move(self, hand, screen_w, screen_h):
        index = hand.landmark[8]

        x = index.x
        y = index.y

        if self.prev_x == 0 and self.prev_y == 0:
            self.prev_x = x

            self.prev_y = y
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
            self.mouse_x = int(self.mouse_x + d_x * self.screen_w * self.MOVE_ACCELERATION)
            self.mouse_y = int(self.mouse_y + d_y * self.screen_h * self.MOVE_ACCELERATION)

        # clipping
        self.mouse_x = max(0, min(self.mouse_x, self.screen_w - 1))
        self.mouse_y = max(0, min(self.mouse_y, self.screen_h - 1))

        pyautogui.moveTo(self.mouse_x, self.mouse_y)

    SCROLL_SENSITIVITY = 200
    SCROLL_DEAD_LINE = 0.002
    def scroll(self, hand):
        print("SCROLL")
        middle = hand.landmark[12]
        if self.prev_scroll_y is None:
            self.prev_scroll_y = middle.y

        dy = middle.y - self.prev_scroll_y

        print(f"scroll: {dy}")
        if abs(dy) > self.SCROLL_DEAD_LINE:
            pyautogui.scroll(int(dy * self.SCROLL_SENSITIVITY))

        self.prev_scroll_y = middle.y

    CLICK_TIME = 0.2
    DEBOUNCE_FRAMES = 4
    pinch_start_time = 0
    first_click_start = 0
    right_click_start = 0
    action_enum = ActionEnum.IDLE
    prev_action_enum = ActionEnum.IDLE
    _pending_gesture = None
    _pending_count = 0

    def _debounce(self, gesture) -> Gesture:
        if gesture != Gesture.Default:
            self._pending_count = 0
            return gesture
        self._pending_count += 1
        if self._pending_count >= self.DEBOUNCE_FRAMES:
            return Gesture.Default
        return self._pending_gesture or Gesture.Default

    def _select_action(self, gesture) -> ActionEnum:
        now = time.time()
        action_out = self.action_enum
        match gesture:
            case Gesture.INDEX_PINCH:
                if self.action_enum != ActionEnum.MOVE:
                    if self.action_enum != ActionEnum.HOLD:
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
                if now - self.right_click_start > self.CLICK_TIME:
                    action_out = ActionEnum.RIGHT_CLICK
                    self.right_click_start = now
                else:
                    action_out = ActionEnum.IDLE
            case Gesture.Default:
                if self.action_enum == ActionEnum.HOLD:
                    if now - self.pinch_start_time <= self.CLICK_TIME*5:
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
        self.prev_action_enum = self.action_enum
        debounced = self._debounce(gesture)
        self.action_enum = self._select_action(debounced)
        # self.action_enum = self._select_action(gesture)
        match self.action_enum:
            case ActionEnum.IDLE:
                if (self.prev_action_enum == ActionEnum.MOVE):
                    pyautogui.mouseUp()
            case ActionEnum.CLICK:
                self.left_click()
            case ActionEnum.MOVE:
                if (self.prev_action_enum != self.action_enum):
                    self.prev_x = 0
                    self.prev_y = 0
                self.move(hand, self.screen_w, self.screen_h)
            case ActionEnum.HOLD:
                pass
            case ActionEnum.SCROLL:
                if (self.prev_action_enum != self.action_enum):
                    self.prev_scroll_y = None
                self.scroll(hand)
            case ActionEnum.DRAG:
                self.drag()
            case ActionEnum.RIGHT_CLICK:
                self.right_click()
