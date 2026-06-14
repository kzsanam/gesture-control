from enum import Enum


class Gesture(Enum):
    Default = 0
    INDEX_PINCH = 1
    MIDDLE_PINCH = 2
    RING_PINCH = 3


class ActionEnum(Enum):
    IDLE = 0
    CLICK = 1
    MOVE = 2
    HOLD = 3
    SCROLL = 4
    DRAG = 5
    RIGHT_CLICK = 6
