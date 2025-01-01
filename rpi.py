import RPi.GPIO as GPIO
import pyaudio
import wave
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY2'))

# GPIO setup
BUTTON_PIN = 18
LED_PINS = {
    "LIVING_ROOM_LIGHTS_ON": 17,
    "LIVING_ROOM_LIGHTS_OFF": 27,
    "KITCHEN_LIGHTS_ON": 22,
    "KITCHEN_LIGHTS_OFF": 23,
    "BATHROOM_LIGHTS_ON": 24,
    "BATHROOM_LIGHTS_OFF": 25,
    "BEDROOM_LIGHTS_ON": 5,
    "BEDROOM_LIGHTS_OFF": 6,
    "LIGHTS_ON": [17, 22, 24, 5],
    "LIGHTS_OFF": [27, 23, 25, 6]
}

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in LED_PINS.values():
    if isinstance(pin, list):
        for p in pin:
            GPIO.setup(p, GPIO.OUT)
    else:
        GPIO.setup(pin, GPIO.OUT)

# Audio recording setup
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

audio = pyaudio.PyAudio()

def record_audio():
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print("Recording...")
    frames = []

    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")
    stream.stop_stream()
    stream.close()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def send_audio_to_api():
    with open(WAVE_OUTPUT_FILENAME, "rb") as audio_file:
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

    return response.choices[0].message.content

def control_leds(command):
    if command in LED_PINS:
        if isinstance(LED_PINS[command], list):
            for pin in LED_PINS[command]:
                GPIO.output(pin, GPIO.HIGH if "ON" in command else GPIO.LOW)
        else:
            GPIO.output(LED_PINS[command], GPIO.HIGH if "ON" in command else GPIO.LOW)
    else:
        print("Command not recognized.")

try:
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            record_audio()
            command = send_audio_to_api()
            print(f"Received command: {command}")
            control_leds(command)
finally:
    GPIO.cleanup()
    audio.terminate()