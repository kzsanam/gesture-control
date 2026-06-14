from hand_mouse.app.gesture_recognition.gesture_recognition import GestureRecognition
from hand_mouse.app.states import ActionEnum, Gesture


class GeometryGestureRecognition(GestureRecognition):
    prev_hand = None

    def is_pinch(self, hand, finger_number, sensitivity):
        if self.prev_hand is None:
            self.prev_hand = hand
        wrist = hand.landmark[0]
        middle_mcp = hand.landmark[9]
        thumb = hand.landmark[4]
        hand_size = self.distance(wrist, middle_mcp)

        finger = hand.landmark[finger_number]

        # this part is using prev hand to improve gesture recognition while releasing move
        if self.prev_hand is None:
            self.prev_hand = hand
        prev_finger = self.prev_hand.landmark[finger_number]
        prev_thumb = self.prev_hand.landmark[4]
        self.prev_hand = hand

        prev_dist = self.distance(prev_thumb, prev_finger)
        dist = self.distance(thumb, finger)

        normalized_delta = (prev_dist - dist) / hand_size  # negative = opening
        # hand is opening while move and we do not want to move it too much afterwards
        # not sure if it is really effective though:(
        if normalized_delta < -0.1 and self.prev_action == ActionEnum.MOVE:
            return False

        return self.distance(thumb, finger) / hand_size < sensitivity

    def is_middle_pinch(self, hand) -> bool:
        return self.is_pinch(hand, 12, 0.15)

    def is_index_pinch(self, hand) -> bool:
        return self.is_pinch(hand, 8, 0.18)

    def is_ring_pinch(self, hand) -> bool:
        return self.is_pinch(hand, 16, 0.15)

    def detect_gesture(self, hand):
        if self.is_index_pinch(hand):
            return Gesture.INDEX_PINCH
        if self.is_middle_pinch(hand):
            return Gesture.MIDDLE_PINCH
        if self.is_ring_pinch(hand):
            return Gesture.RING_PINCH
        return Gesture.Default
