import math
from enum import Enum


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


class Gesture(Enum):
    Default = 0
    INDEX_PINCH = 1
    MIDDLE_PINCH = 2
    RING_PINCH = 3


def isPinch(hand, finger_number, sensitivity):
    wrist = hand.landmark[0]
    middle_mcp = hand.landmark[9]
    thumb = hand.landmark[4]
    hand_size = distance(wrist, middle_mcp)

    finger = hand.landmark[finger_number]
    # print(f"distance: {distance(thumb, finger) / hand_size}")
    return distance(thumb, finger) / hand_size < sensitivity


def isMiddlePinch(hand) -> bool:
    return isPinch(hand, 12, 0.15)


def isIndexPinch(hand) -> bool:
    return isPinch(hand, 8, 0.18)


def isRingPinch(hand) -> bool:
    return isPinch(hand, 16, 0.15)


def detectGesture(hand):
    if isIndexPinch(hand):
        return Gesture.INDEX_PINCH
    if isMiddlePinch(hand):
        return Gesture.MIDDLE_PINCH
    if isRingPinch(hand):
        return Gesture.RING_PINCH
    return Gesture.Default
