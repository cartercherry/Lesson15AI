##########################################################################################
# lesson 15 STT move pan tilt cam up,down, left,right, or quit                           #
#  5/16/26                                                                               #
##########################################################################################

import cv2
from picamera2 import Picamera2
from time import sleep
from contextlib import contextmanager
from vosk import Model, KaldiRecognizer, SetLogLevel
import board
import busio
import adafruit_pca9685
import pyaudio
import json
import os
import sys
from adafruit_servokit import ServoKit

numbersDict={'zero':0, 'one': 1, 'to': 2, 'three': 3,'for':4, 'five':5, 'six':6, 'seven':7, 'eight':8,\
             'nine':9, 'ten':10, 'twenty':20}

piCam = Picamera2(1)   # module 3 cam, use 0 for v2.1 cam 
W = 1280
H = 720 
RES = (W,H)  #resolution
piCam.preview_configuration.main.size = RES
piCam.preview_configuration.main.format = "RGB888"
piCam.preview_configuration.main.align()
piCam.configure("preview")
piCam.start()
cv2.namedWindow('Video', cv2.WINDOW_AUTOSIZE)
window_moved = False

panAngle = 90
tiltAngle = 90
# Initialize the PCA9685 board
# It defaults to I2C bus 1 and address 0x40
print("Initializing PCA9685 board...")
kit = ServoKit(channels=16)

#If  servos hum or jitter at the extremes (0 or 180), 
# you can fine-tune their pulse width ranges here. Standard is typically 500 to 2500.
kit.servo[0].set_pulse_width_range(400, 2600)
kit.servo[1].set_pulse_width_range(400, 2600)

kit.servo[0].angle = panAngle
kit.servo[1].angle = tiltAngle



# Silences C-level ALSA warnings
@contextmanager
def ignore_alsa_warnings():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    sys.stderr.flush()
    os.dup2(devnull, sys.stderr.fileno())
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(old_stderr)

# Setup STT Engine
SetLogLevel(-1)
MODEL_PATH = "/opt/vosk_models/vosk-model-small-en-us-0.15"

print("Loading offline AI Voice Model... Please wait.")
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

with ignore_alsa_warnings():
    p = pyaudio.PyAudio()

device_index = None
for i in range(p.get_device_count()):
    dev_info = p.get_device_info_by_index(i)
    if 'Snowball' in dev_info.get('name', ''):  #microphone
        device_index = i
        break

if device_index is None:
    print("Warning: Snowball not found by name. Falling back to default.")

stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=4000)

stream.start_stream()
print("\n*** Voice Control Active! ***")
print("Press Ctrl+C to exit.\n")

try:
    while True:
        frame = piCam.capture_array() 
        frame = cv2.flip(frame, -1)
        cv2.imshow("Video",frame) 
        if not window_moved:
                cv2.waitKey(1)
                cv2.moveWindow('Video', 0, 50)
                window_moved = True

                # 6. The Event Loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quit signal received.")
                break
        data = stream.read(4000, exception_on_overflow=False)  # STT started
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            if 'quit' in text:
                break
            splitText = text.split()
            print(splitText)   #####DEBUG#####
            if splitText:
                if splitText[0] in ['up', 'down', 'left', 'right']:
                    print(splitText[1])  #DEBUG
                    match splitText[0]:
                        case 'up':
                            #print('in up',splitText[1])  #DEBUG##
                            if splitText[1] in numbersDict:
                                tiltAngle -= numbersDict[splitText[1]]
                            else:
                                tiltAngle -= 5
                            tiltAngle = max(0, min(tiltAngle, 180))
                            kit.servo[1].angle = tiltAngle
                        case 'down':
                            if splitText[1] in numbersDict:
                                tiltAngle += numbersDict[splitText[1]]
                            else:
                                tiltAngle += 5
                            tiltAngle = max(0, min(tiltAngle, 180))
                            kit.servo[1].angle = tiltAngle
                        case 'left':
                            if splitText[1] in numbersDict:
                                panAngle += numbersDict[splitText[1]]
                            else:
                                panAngle += 5
                            panAngle = max(0, min(panAngle, 180))
                            kit.servo[0].angle = panAngle
                        case 'right':
                            if splitText[1] in numbersDict:
                                panAngle -= numbersDict[splitText[1]]
                            else:
                                panAngle -= 5
                            panAngle = max(0, min(panAngle, 180))
                            kit.servo[0].angle = panAngle
    #print('breaking out of while loop')   
except KeyboardInterrupt:
    print('\nexiting...')
finally:
    print('terminated')
    kit.servo[0].angle = None
    kit.servo[1].angle = None
    cv2.destroyAllWindows()
    #cleanup here






