import cv2
import mediapipe as mp
from utils import VolumeController, take_screenshot, open_app, speak
import time

class GestureDetector:
    def __init__(self):
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.volume = VolumeController()
        self.prev_action = None
        self.last_time = time.time()

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        if not results.multi_hand_landmarks:
            return

        hand_landmarks = results.multi_hand_landmarks[0]
        h, w, _ = frame.shape
        landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        gesture = None

        # Basic hand geometry for gestures
        if thumb_tip[1] < index_tip[1] and thumb_tip[1] < middle_tip[1]:
            gesture = "thumbs_up"
        elif thumb_tip[1] > index_tip[1] and thumb_tip[1] > middle_tip[1]:
            gesture = "thumbs_down"
        elif abs(index_tip[0] - middle_tip[0]) > 60:
            gesture = "victory"
        elif abs(index_tip[0] - thumb_tip[0]) < 40 and abs(index_tip[1] - thumb_tip[1]) < 40:
            gesture = "fist"

        # Avoid repeating same gesture
        now = time.time()
        if gesture and (gesture != self.prev_action or now - self.last_time > 1.5):
            self.handle_gesture(gesture)
            self.prev_action = gesture
            self.last_time = now

    def handle_gesture(self, gesture):
        if gesture == "thumbs_up":
            self.volume.volume_up()
        elif gesture == "thumbs_down":
            self.volume.volume_down()
        elif gesture == "victory":
            take_screenshot()
        elif gesture == "fist":
            speak("Listening for voice command...")
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                audio = r.listen(source)
            try:
                command = r.recognize_google(audio)
                from utils import process_command
                process_command(command)
            except:
                speak("Sorry, I didn’t get that.")
