from flask import Flask, jsonify, render_template, request
import threading
import time
import cv2
import mediapipe as mp
import pyautogui
import numpy as np

app = Flask(__name__)

# Global states
hand_state = {'state': 'STOPPED', 'ti_dist': 100, 'is_fist': False}
voice_state = {'status': 'STOPPED', 'command': 'None'}
mouse_position = {'x': 0, 'y': 0, 'screen_w': 1920, 'screen_h': 1080}
hand_running = False
cap = None

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/status')
def status():
    return jsonify({'hand': hand_state, 'voice': voice_state, 'mouse': mouse_position}) 
@app.route('/start', methods=['POST'])
def start_systems():
    global hand_running, cap, hand_state
    
    print("START BUTTON PRESSED!")
    
    if not hand_running:
        hand_running = True
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("NO CAMERA!")
            hand_state['state'] = 'NO_CAMERA'
            return jsonify({'error': 'camera'})
        
        print("CAMERA READY!")
        hand_state['state'] = 'STARTING'
        
        # Start hand tracking in separate thread
        hand_thread = threading.Thread(target=hand_tracking_loop, daemon=True)
        hand_thread.start()
        
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop_systems():
    global hand_running, cap
    print("STOP BUTTON PRESSED!")
    
    hand_running = False
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    
    hand_state = {'state': 'STOPPED', 'ti_dist': 100, 'is_fist': False}
    print("ALL STOPPED")
    return jsonify({'status': 'stopped'})

def hand_tracking_loop():
    global hand_state, cap, hand_running
    
    print("🎥 LIVE CAMERA - SHOW HAND!")
    
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    
    while hand_running:
        success, frame = cap.read()
        if not success:
            hand_state['state'] = 'CAMERA_ERROR'
            break
            
        # Mirror effect
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        # Always update state
        hand_state['state'] = 'RUNNING'
        hand_state['ti_dist'] = 100
        hand_state['is_fist'] = False
        mouse_position['x'] = 0      # ← ADD THESE 3 LINES
        mouse_position['y'] = 0
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Thumb tip (4) vs Index tip (8)
                thumb = hand_landmarks.landmark[4]
                index = hand_landmarks.landmark[8]
                
                # Distance calculation
                dist = int(np.sqrt((thumb.x-index.x)**2 + (thumb.y-index.y)**2) * 200)
                hand_state['ti_dist'] = max(0, min(100, dist))
                
                # Mouse follows index finger
                h, w, _ = frame.shape
                screen_w, screen_h = pyautogui.size()
                mouse_x = int(index.x * screen_w)
                mouse_y = int(index.y * screen_h)
                pyautogui.moveTo(mouse_x, mouse_y)

                # UPDATE LIVE MOUSE POSITION ← ADD THESE 4 LINES
                global mouse_position
                mouse_position['x'] = mouse_x
                mouse_position['y'] = mouse_y
                mouse_position['screen_w'] = screen_w
                mouse_position['screen_h'] = screen_h

                # Fist = CLICK
                if hand_state['ti_dist'] < 25:
                    hand_state['is_fist'] = True
                    pyautogui.click()
                    print(f"CLICK! Distance: {dist}")
                
                # Draw hand landmarks
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        # Show live camera feed
        cv2.imshow('AI Virtual Mouse - Live Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        time.sleep(0.03)  # 30 FPS
    
    # Cleanup
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    hand_state['state'] = 'STOPPED'
    print("TRACKING STOPPED")

if __name__ == '__main__':
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    print("AI VIRTUAL MOUSE v3.0 SELF-CONTAINED")
    print("Dashboard: http://localhost:8080")
    print("Ctrl+C to quit")
    app.run(host='0.0.0.0', port=8080, debug=True)
