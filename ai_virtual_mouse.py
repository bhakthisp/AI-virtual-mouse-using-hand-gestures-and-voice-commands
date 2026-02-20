from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import time
import os
import psutil

app = Flask(__name__)

# Status tracking
hand_status = {"state": "STOPPED", "ti_dist": 100, "is_fist": False}
voice_status = {"status": "STOPPED", "command": "None"}
systems_running = False

hand_process = None
voice_process = None

def kill_python_processes():
    """Kill any existing Python processes on port 5000"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                for cmd in proc.info['cmdline'] or []:
                    if '5000' in cmd or 'hand_gestures.py' in cmd or 'voice_commands.py' in cmd:
                        proc.kill()
                        print(f"🗑️ Killed PID {proc.info['pid']}")
        except:
            pass

def start_hand():
    global hand_process, hand_status
    try:
        kill_python_processes()
        hand_process = subprocess.Popen(['python', 'hand_gestures.py'])
        hand_status["state"] = "RUNNING"
        print("🖐️ Hand gestures STARTED!")
    except Exception as e:
        print(f"❌ Hand error: {e}")
        hand_status["state"] = "ERROR"

def start_voice():
    global voice_process, voice_status
    try:
        voice_process = subprocess.Popen(['python', 'voice_commands.py'])
        voice_status["status"] = "RUNNING"
        print("🗣️ Voice commands STARTED!")
    except Exception as e:
        print(f"❌ Voice error: {e}")
        voice_status["status"] = "ERROR"

def stop_all():
    global hand_process, voice_process
    try:
        if hand_process:
            hand_process.terminate()
            hand_process.wait(timeout=2)
        if voice_process:
            voice_process.terminate()
            voice_process.wait(timeout=2)
        hand_status["state"] = "STOPPED"
        voice_status["status"] = "STOPPED"
        print("🛑 ALL STOPPED")
    except:
        pass

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/start', methods=['POST'])
def start():
    global systems_running
    if not systems_running:
        systems_running = True
        threading.Thread(target=start_hand, daemon=True).start()
        time.sleep(1)
        threading.Thread(target=start_voice, daemon=True).start()
    return 'OK'

@app.route('/stop', methods=['POST'])
def stop():
    global systems_running
    systems_running = False
    threading.Thread(target=stop_all, daemon=True).start()
    return 'OK'

@app.route('/status')
def status():
    return {
        'hand': hand_status,
        'voice': voice_status,
        'running': systems_running
    }

if __name__ == "__main__":
    kill_python_processes()  # Clean start
    print("🚀 AI MASTER CONTROLLER v2.0")
    print("📱 Dashboard: http://localhost:8080")  # CHANGED PORT!
    print("🖐️ Starting on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)
