from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
import time
import subprocess
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

running_thread = None
stop_thread = False

def run_script_continuous(script_name):
    global stop_thread
    stop_thread = False
    try:
        # Open a subprocess to run the script
        process = subprocess.Popen(['python3', script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            if stop_thread:
                process.terminate()
                break

            output = process.stdout.readline()
            if output:
                socketio.emit('script_output', {'output': output})
            else:
                break

        # Capture remaining output
        for output in process.stdout.readlines():
            socketio.emit('script_output', {'output': output})
        for output in process.stderr.readlines():
            socketio.emit('script_output', {'output': output})

    except Exception as e:
        socketio.emit('script_output', {'output': str(e)})

@app.route('/')
def index():
    # List available Python files
    files = [f for f in os.listdir('.') if f.endswith('.py')]
    return render_template('index.html', files=files)

@socketio.on('start_script')
def start_script(data):
    global running_thread
    filename = data['filename']
    if running_thread and running_thread.is_alive():
        emit('script_output', {'output': 'A script is already running.'})
    else:
        running_thread = threading.Thread(target=run_script_continuous, args=(filename,))
        running_thread.start()

@socketio.on('stop_script')
def stop_script():
    global stop_thread
    stop_thread = True
    if running_thread:
        running_thread.join()
        emit('script_output', {'output': 'Script stopped.'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
