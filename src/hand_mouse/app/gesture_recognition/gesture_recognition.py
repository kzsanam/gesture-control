import math
from abc import ABC, abstractmethod

from hand_mouse.app.states import ActionEnum


class GestureRecognition(ABC):
    prev_action = ActionEnum.IDLE

    def set_prev_action(self, prev_action):
        self.prev_action = prev_action

    @abstractmethod
    def detect_gesture(self, hand):
        pass

    def distance(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
