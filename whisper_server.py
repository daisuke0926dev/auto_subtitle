import os
import time
from flask import Flask, jsonify, request, redirect
import whisper
import obsws_python as obs
import re
import threading
import pw

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'m4a','mp3','wav'}
OBS_PASSWORD = pw.OBS_PASSWORD
TARGET_SOURCE_NAME = '音声認識の字幕'
CSS_TEMPLATE_PATH = 'static/subtitle.css'
WHISPER_MODEL_NAME = 'tiny' # tiny, base, small, medium
WHISPER_DEVICE = 'cpu' # cpu, cuda

with open(CSS_TEMPLATE_PATH) as f:
   CSS_TEMPLATE = f.read()

def send_jimaku(text):
    css = re.sub(' content: .*;', ' content: "' + text + '";', CSS_TEMPLATE)
    try:
        obscl.set_input_settings(TARGET_SOURCE_NAME, {'css': css}, True)
    except Exception as e:
        print(e)

print("connecting obs-websocket")
try:
    obscl = obs.ReqClient(host='localhost', port=4455, password=OBS_PASSWORD)
    send_jimaku('')
except Exception as e:
    print(e)

print('loading whisper model', WHISPER_MODEL_NAME, WHISPER_DEVICE)
whisper_model = whisper.load_model(WHISPER_MODEL_NAME, device=WHISPER_DEVICE)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__, static_url_path='/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

lock = threading.Lock()

@app.route('/')
def index():
   return redirect('/index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
   time_sta = time.perf_counter()
   print('start transcribe ' + str(time_sta))
   file = request.files['file']
   ext = file.filename.rsplit('.', 1)[1].lower()
   if ext and ext in ALLOWED_EXTENSIONS:
       filename = str(int(time.time())) + '.' + ext
       saved_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
       file.save(saved_filename)
       lock.acquire()
       result = whisper_model.transcribe(saved_filename, fp16=False, language='ja')
       lock.release()
       print('time='+ str(time.perf_counter() - time_sta))
       print(result)
       send_jimaku(result['text'])
       return result, 200

   result={'error':'something wrong'}
   print(result)
   return result, 400

app.run(host='localhost', port=9000)
