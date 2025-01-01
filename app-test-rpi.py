from openai import OpenAI
import os
import base64
import RPi.GPIO as GPIO
import time
import sounddevice as sd
import soundfile as sf

# Initialize client with API key
client = OpenAI(api_key='sk-NsA')

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Define GPIO pins for each room (using BOARD numbering)
LED_PINS = {
  "LIVING_ROOM": 11,  # GPIO 17 -> Pin 11
  "KITCHEN": 13,      # GPIO 27 -> Pin 13
  "BATHROOM": 15,     # GPIO 22 -> Pin 15
  "BEDROOM": 16       # GPIO 23 -> Pin 16
}

# Define GPIO pin for the push button
BUTTON_PIN = 18  # GPIO 24 -> Pin 18

# Setup GPIO pins as output
for pin in LED_PINS.values():
  GPIO.setup(pin, GPIO.OUT)
  GPIO.output(pin, GPIO.LOW)

# Setup GPIO pin for the button as input with pull-down resistor
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Function to control LEDs
def control_led(command):
  print(f"Received command: {command}")
  if command == "LIVING_ROOM_LIGHTS_ON":
    GPIO.output(LED_PINS["LIVING_ROOM"], GPIO.HIGH)
    print('Turning on living room lights')
  elif command == "LIVING_ROOM_LIGHTS_OFF":
    GPIO.output(LED_PINS["LIVING_ROOM"], GPIO.LOW)
    print('Turning off living room lights')
  elif command == "KITCHEN_LIGHTS_ON":
    GPIO.output(LED_PINS["KITCHEN"], GPIO.HIGH)
    print('Turning on kitchen lights')
  elif command == "KITCHEN_LIGHTS_OFF":
    GPIO.output(LED_PINS["KITCHEN"], GPIO.LOW)
    print('Turning off kitchen lights')
  elif command == "BATHROOM_LIGHTS_ON":
    GPIO.output(LED_PINS["BATHROOM"], GPIO.HIGH)
    print('Turning on bathroom lights')
  elif command == "BATHROOM_LIGHTS_OFF":
    GPIO.output(LED_PINS["BATHROOM"], GPIO.LOW)
    print('Turning off bathroom lights')
  elif command == "BEDROOM_LIGHTS_ON":
    GPIO.output(LED_PINS["BEDROOM"], GPIO.HIGH)
    print('Turning on bedroom lights')
  elif command == "BEDROOM_LIGHTS_OFF":
    GPIO.output(LED_PINS["BEDROOM"], GPIO.LOW)
    print('Turning off bedroom lights')
  elif command == "LIGHTS_ON":
    for pin in LED_PINS.values():
      GPIO.output(pin, GPIO.HIGH)
    print('Turning on all lights')
  elif command == "LIGHTS_OFF":
    for pin in LED_PINS.values():
      GPIO.output(pin, GPIO.LOW)
    print('Turning off all lights')
  else:
    print("Command not recognized or not able to perform.")

# Function to record audio
def record_audio(filename, duration, fs=44100):
  print("Recording audio...")
  recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
  sd.wait()  # Wait until recording is finished
  sf.write(filename, recording, fs)
  print("Recording saved to", filename)

# Function to handle button press
def button_callback(channel):
  global recording, recording_start_time
  if recording:
    # Stop recording
    recording_duration = time.time() - recording_start_time
    record_audio('uploads/recording.mp3', recording_duration)
    recording = False
    # Send the recording to the API
    with open('uploads/recording.mp3', 'rb') as audio_file:
      audio_bytes = audio_file.read()
      audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    response = client.chat.completions.create(
      model="gpt-4o-mini-audio-preview-2024-12-17",
      messages=[
        {
          "role": "system",
          "content": [
            {
              "text": "Convert any input regarding smart home controls into a predefined command from the specified list.\n\nIdentify and match each user's request to the appropriate command for controlling lights within various rooms of the home. If the instruction is unclear or not achievable, use the respective commands for those situations.\n\n# Steps\n\n1. Analyze the input text to identify the room and action (ON/OFF) intended by the user.\n2. Match the determined room and action with one of the specified commands.\n3. If the input does not clearly indicate a specific room, use LIGHTS_ON or LIGHTS_OFF for general commands.\n4. If the instruction is unclear, use the command UNCLEAR_INSTRUCTION.\n5. If the requested action is not possible, use the command NOT_ABLE_TO_DO.\n\n# Output Format\n\n- The output should be a single command string selected from the following, without brackets or semicolons:\n\n  - LIVING_ROOM_LIGHTS_OFF\n  - LIVING_ROOM_LIGHTS_ON\n  - KITCHEN_LIGHTS_OFF\n  - KITCHEN_LIGHTS_ON\n  - BATHROOM_LIGHTS_OFF\n  - BATHROOM_LIGHTS_ON\n  - BEDROOM_LIGHTS_OFF\n  - BEDROOM_LIGHTS_ON\n  - LIGHTS_OFF\n  - LIGHTS_ON\n  - UNCLEAR_INSTRUCTION\n  - NOT_ABLE_TO_DO\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"Turn off the lights in the living room.\"\n- **Output:** LIVING_ROOM_LIGHTS_OFF\n\n**Example 2:**\n\n- **Input:** \"I'd like the kitchen lights on please.\"\n- **Output:** KITCHEN_LIGHTS_ON\n\n**Example 3:**\n\n- **Input:** \"Make it bright everywhere!\"\n- **Output:** LIGHTS_ON\n\n**Example 4:**\n\n- **Input:** \"Can you set the mood lighting?\"\n- **Output:** UNCLEAR_INSTRUCTION\n\n# Notes\n\n- Consider using synonyms or variations of \"turn on\" and \"turn off\" to determine the correct command.\n- Anticipate variations in phrasing or language that may affect room identification.\n- If no room is specified, assume the instruction refers to all lights.\n- If conditions or systems limit the ability to perform an action, opt for the NOT_ABLE_TO_DO response.",
              "type": "text"
            }
          ]
        },
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": ""
            },
            {
              "type": "input_audio",
              "input_audio": {
                "data": audio_base64,
                "format": "mp3"
              }
            }
          ]
        }
      ],
      modalities=["text"],
      response_format={
        "type": "text"
      },
      temperature=1,
      max_completion_tokens=2048,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    command = response.choices[0].message.content
    print(f"API response command: {command}")
    control_led(command)
  else:
    # Start recording
    recording_start_time = time.time()
    recording = True
    print("Started recording...")

# Initialize recording state
recording = False
recording_start_time = 0

# Add event detection for the button
GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=button_callback, bouncetime=300)

try:
  while True:
    time.sleep(1)
except KeyboardInterrupt:
  print("Exiting program")
finally:
  GPIO.cleanup()