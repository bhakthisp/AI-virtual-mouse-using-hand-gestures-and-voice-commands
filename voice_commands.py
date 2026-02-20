import os
import warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")

import speech_recognition as sr
import pyautogui
import time
from datetime import datetime

class VoiceController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.running = True
        
        # BETTER Voice Commands (exact matches + fuzzy)
        self.commands = {
            'click': ['click', 'left click', 'press'],
            'right_click': ['right click', 'right', 'context'],
            'double_click': ['double click', 'double'],
            'scroll_up': ['scroll up', 'up', 'scrollup'],
            'scroll_down': ['scroll down', 'down', 'scrolldown'],
            'drag': ['drag', 'hold', 'grab'],
            'volume_up': ['volume up', 'louder', 'volumeup'],
            'volume_down': ['volume down', 'quieter', 'volumedown'],
            'mute': ['mute', 'silence'],
            'hello': ['hello', 'hi', 'hey'],
            'quit': ['quit', 'exit', 'stop', 'bye']
        }
        
        self.last_command_time = 0
        self.cooldown = 1.0
        
        # ROBUST microphone calibration
        print("🎤 Calibrating microphone (speak loudly)...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.recognizer.energy_threshold = 300  # Lower threshold
            print("Microphone calibrated!")
        except Exception as e:
            print(f"Calibration warning: {e}")
    
    def matches_command(self, text, keywords):
        """Fuzzy matching for voice commands"""
        text = text.lower().strip()
        return any(word in text for word in keywords)
    
    def execute_command(self, command_text):
        """Execute recognized voice command"""
        print(f"🗣️  HEARD: '{command_text}'")
        
        for action, keywords in self.commands.items():
            if self.matches_command(command_text, keywords):
                current_time = time.time()
                if current_time - self.last_command_time < self.cooldown:
                    return True  # Cooldown active
                
                self.last_command_time = current_time
                
                try:
                    if action == 'quit':
                        self.running = False
                        print("Voice control stopped!")
                        return False
                    
                    elif action == 'click':
                        pyautogui.click()
                        print("LEFT CLICK")
                    elif action == 'right_click':
                        pyautogui.rightClick()
                        print("RIGHT CLICK")
                    elif action == 'double_click':
                        pyautogui.doubleClick()
                        print("DOUBLE CLICK")
                    elif action == 'scroll_up':
                        pyautogui.scroll(5)
                        print("SCROLL UP")
                    elif action == 'scroll_down':
                        pyautogui.scroll(-5)
                        print("SCROLL DOWN")
                    elif action == 'drag':
                        pyautogui.mouseDown()
                        time.sleep(0.1)
                        pyautogui.mouseUp()
                        print("DRAG")
                    elif action == 'volume_up':
                        pyautogui.press('volumeup')
                        print("VOLUME UP")
                    elif action == 'volume_down':
                        pyautogui.press('volumedown')
                        print("VOLUME DOWN")
                    elif action == 'mute':
                        pyautogui.press('volumemute')
                        print("MUTE")
                    elif action == 'hello':
                        pyautogui.write('Hello!')
                        print("TYPED: Hello!")
                    
                    return True
                except Exception as e:
                    print(f"Action error: {e}")
                    return True
        
        print("Unknown command (try: click, scroll up, volume up, quit)")
        return True
    
    def listen_once(self):
        """Single listen attempt with NO CRASH"""
        try:
            print("👂 Listening... (3 seconds)", end=" ")
            with self.microphone as source:
                # NON-BLOCKING listen with timeout
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2)
            
            command = self.recognizer.recognize_google(audio).lower()
            return self.execute_command(command)
            
        except sr.WaitTimeoutError:
            return True  # Silent fail - no speech
        except sr.UnknownValueError:
            return True  # Couldn't understand
        except sr.RequestError as e:
            print(f"\nGoogle API error: {e}")
            return True
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return True
    
    def run(self):
        print("🎤 VOICE CONTROL v2.0 - INDUSTRIAL GRADE")
        print("Commands: click | right click | scroll up/down | volume up/down | mute | quit")
        print("=" * 70)
        
        try:
            while self.running:
                self.listen_once()
                time.sleep(0.3)  # Brief pause between attempts
                
        except KeyboardInterrupt:
            print("\nVoice control stopped by user (Ctrl+C)")
        finally:
            self.running = False
            print("Voice controller shutdown clean!")

if __name__ == "__main__":
    voice = VoiceController()
    voice.run()
