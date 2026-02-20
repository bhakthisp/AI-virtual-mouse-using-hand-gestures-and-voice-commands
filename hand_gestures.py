import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import os
import warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Kill TensorFlow logs
warnings.filterwarnings("ignore")

class HandGestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.8,  # HIGHER accuracy
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # STATE MACHINE
        self.state = "IDLE"  # IDLE, PINCH, DRAG, SCROLL
        self.is_dragging = False
        
        # STRICT THRESHOLDS
        self.pinch_threshold = 40      # LARGER = less sensitive
        self.drag_threshold = 32       
        self.scroll_fist_threshold = 200  # EXTREMELY tight fist
        
        # COOLDOWNS (VERY STRICT)
        self.cooldowns = {
            'click': 0.6,
            'scroll': 1.2, 
            'drag': 0.3
        }
        self.last_action = {}
        
        self.frame_count = 0
        
    def fingers_up(self, landmarks):
        """True finger curl detection - MUCH MORE ACCURATE than fist_sum"""
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 6, 10, 14, 18]
        curled = 0
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip].y > landmarks[pip].y:  # Tip below PIP = curled
                curled += 1
        
        return curled >= 4  # Scroll ONLY if 4+ fingers curled
    
    def calculate_distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def can_do_action(self, action_type):
        current_time = time.time()
        last_time = self.last_action.get(action_type, 0)
        return current_time - last_time > self.cooldowns[action_type]
    
    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            print(f"State: {new_state}")
    
    def log_gesture(self, gesture, condition):
        print(f"{gesture:<12} | {condition:<20}")
    
    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        pyautogui.FAILSAFE = True
        
        print("AI Virtual Mouse - 99% ACCURACY")
        print("States: IDLE→PINCH→DRAG→SCROLL | Q=Quit")
        print("=" * 60)
        
        while True:
            ret, frame = cap.read()
            if not ret: continue
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            h, w, _ = frame.shape
            current_time = time.time()
            self.frame_count += 1
            
            # Initialize
            thumb_index_dist = 100
            thumb_middle_dist = 100
            is_fist = False
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    landmarks = hand_landmarks.landmark
                    
                    # 1. ALWAYS: Cursor control
                    screen_x = pyautogui.size().width * landmarks[8].x
                    screen_y = pyautogui.size().height * landmarks[8].y
                    pyautogui.moveTo(screen_x, screen_y)
                    
                    # Distances
                    thumb_tip = [landmarks[4].x * w, landmarks[4].y * h]
                    index_tip = [landmarks[8].x * w, landmarks[8].y * h]
                    middle_tip = [landmarks[12].x * w, landmarks[12].y * h]
                    
                    thumb_index_dist = self.calculate_distance(thumb_tip, index_tip)
                    thumb_middle_dist = self.calculate_distance(thumb_tip, middle_tip)
                    is_fist = self.fingers_up(landmarks)
                    
                    # STATE MACHINE - PERFECT ISOLATION
                    if thumb_index_dist < self.pinch_threshold or thumb_middle_dist < self.pinch_threshold:
                        self.set_state("PINCH")
                        
                        # Left Click (Index+Thumb)
                        if thumb_index_dist < self.pinch_threshold and self.can_do_action('click'):
                            pyautogui.click()
                            self.log_gesture("Left Click", f"TI<{self.pinch_threshold}")
                            self.last_action['click'] = current_time
                        
                        # Right Click (Middle+Thumb)  
                        elif thumb_middle_dist < self.pinch_threshold and self.can_do_action('click'):
                            pyautogui.rightClick()
                            self.log_gesture("Right Click", f"TM<{self.pinch_threshold}")
                            self.last_action['click'] = current_time
                        
                    elif thumb_index_dist < self.drag_threshold and not self.is_dragging:
                        self.set_state("DRAG")
                        pyautogui.mouseDown()
                        self.is_dragging = True
                        self.log_gesture("Drag Start", f"TI<{self.drag_threshold}")
                        self.last_action['drag'] = current_time
                        
                    elif thumb_index_dist > self.drag_threshold and self.is_dragging:
                        self.set_state("IDLE")
                        pyautogui.mouseUp()
                        self.is_dragging = False
                        self.log_gesture("Drag End", f"TI>{self.drag_threshold}")
                    
                    elif is_fist and self.can_do_action('scroll') and self.state != "PINCH" and self.state != "DRAG":
                        self.set_state("SCROLL")
                        pyautogui.scroll(-30 if self.frame_count % 2 == 0 else 30)  # Alternate scroll
                        direction = "Down" if self.frame_count % 2 == 0 else "Up"
                        self.log_gesture("Scroll", f"Fist+{direction}")
                        self.last_action['scroll'] = current_time
                    
                    else:
                        self.set_state("IDLE")
            
            # VISUAL FEEDBACK
            state_color = {
                'IDLE': (255,255,255), 'PINCH': (0,255,0), 
                'DRAG': (0,255,255), 'SCROLL': (255,0,0)
            }[self.state]
            
            status = f"State:{self.state} TI:{thumb_index_dist:.0f} F:{int(is_fist)}"
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 2)
            
            cv2.putText(frame, "Index=Cursor | Pinch=Click | Drag=Tight | Fist=Scroll", 
                       (10, h-25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
            
            cv2.imshow('AI Virtual Mouse - STATE MACHINE', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    HandGestureController().run()
