
import os
import subprocess
import threading
from flask import Flask, request, jsonify
import time
import json

app = Flask(__name__)
port = int(os.environ.get('WHISPER_PORT', 8801))

# --- Configuration ---
# Path to the C++ whisper executable, relative to the root of the project.
whisper_executable_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'build', 'whisper'))
# Arguments for the whisper executable to run in service mode.
whisper_args = [
    # Add arguments like '--encoder', './models/small-encoder.axmodel' if they are not in the default location.
]

# Load arguments from arguments.json if it exists
try:
    arguments_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'arguments.json'))
    if os.path.exists(arguments_json_path):
        with open(arguments_json_path, 'r') as f:
            args_config = json.load(f)
            # Map the arguments from the JSON file
            for key, value in args_config.items():
                whisper_args.append(f'--{key}')
                whisper_args.append(str(value))
        print(f'Loaded arguments from {arguments_json_path}')
    else:
        print(f'No arguments.json found at {arguments_json_path}, using default arguments')
except Exception as e:
    print(f'Error loading arguments.json: {e}')
# --- End Configuration ---

whisper_process = None
is_busy = False
stdout_buffer = ''
stdout_lock = threading.Lock()

def start_whisper_process():
    global whisper_process
    print('Starting whisper C++ service...')
    try:
        whisper_process = subprocess.Popen(
            [whisper_executable_path] + whisper_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        )
        
        # Thread to handle stdout
        stdout_thread = threading.Thread(target=handle_stdout, args=(whisper_process,))
        stdout_thread.daemon = True
        stdout_thread.start()

        # Thread to handle stderr
        stderr_thread = threading.Thread(target=handle_stderr, args=(whisper_process,))
        stderr_thread.daemon = True
        stderr_thread.start()

        print('Whisper C++ service started.')
    except Exception as e:
        print(f"Failed to start whisper C++ service: {e}")
        whisper_process = None

def handle_stdout(process):
    global stdout_buffer
    while True:
        try:
            line = process.stdout.readline()
            if not line:
                break
            with stdout_lock:
                stdout_buffer += line
            print(f"[Whisper STDOUT]: {line.strip()}")
        except Exception as e:
            print(f"Error reading stdout: {e}")
            break


def handle_stderr(process):
    while True:
        try:
            line = process.stderr.readline()
            if not line:
                break
            print(f"[Whisper STDERR]: {line.strip()}")
        except Exception as e:
            print(f"Error reading stderr: {e}")
            break


@app.route('/recognize', methods=['POST'])
def recognize():
    global is_busy, stdout_buffer

    data = request.get_json()
    file_path = data.get('filePath')

    if not file_path:
        return jsonify({'error': 'Missing "filePath" in request body.'}), 400

    if not whisper_process or whisper_process.poll() is not None:
        return jsonify({'error': 'Whisper service is not running.'}), 503

    if is_busy:
        return jsonify({'error': 'Service is busy. Please try again later.'}), 429

    is_busy = True
    with stdout_lock:
        stdout_buffer = ''  # Clear buffer

    print(f"Sending path to whisper service: {file_path}")

    try:
        whisper_process.stdin.write(file_path + '\n')
        whisper_process.stdin.flush()
    except Exception as e:
        is_busy = False
        return jsonify({'error': f'Failed to write to whisper process: {e}'}), 500


    # Wait for the result with a timeout
    start_time = time.time()
    while time.time() - start_time < 120:  # 2-minute timeout
        with stdout_lock:
            if 'Result:' in stdout_buffer:
                try:
                    result_line = [line for line in stdout_buffer.split('\n') if 'Result:' in line][0]
                    result = result_line.split('Result:', 1)[1].strip()
                    
                    response = {
                        'filePath': file_path,
                        'recognition': result,
                    }
                    
                    is_busy = False
                    return jsonify(response)
                except IndexError:
                    # Result line is not complete yet, continue waiting
                    pass
        time.sleep(0.1) # sleep for 100ms
    
    is_busy = False
    return jsonify({'error': 'Request timed out.'}), 504

def monitor_whisper_process():
    global whisper_process
    while True:
        if whisper_process and whisper_process.poll() is not None:
            print(f"Whisper C++ service exited with code {whisper_process.poll()}. Restarting...")
            start_whisper_process()
        time.sleep(1)

if __name__ == '__main__':
    start_whisper_process()
    monitor_thread = threading.Thread(target=monitor_whisper_process)
    monitor_thread.daemon = True
    monitor_thread.start()
    app.run(host='0.0.0.0', port=port)
