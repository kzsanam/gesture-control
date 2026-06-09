import pyautogui

class CursorController:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h

        self.prev_x = 0
        self.prev_y = 0
        self.smoothing = 0.25

    def move(self, x, y):
        # smoothing
        sx = self.prev_x + self.smoothing * (x - self.prev_x)
        sy = self.prev_y + self.smoothing * (y - self.prev_y)

        self.prev_x, self.prev_y = sx, sy

        pyautogui.moveTo(
            int(sx * self.screen_w),
            int(sy * self.screen_h)
        )

    def click(self):
        pyautogui.click()
