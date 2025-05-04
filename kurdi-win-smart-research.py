import re
import os
import requests
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()
PAWAN_API = os.getenv("PAWAN_API_KEY")
api_key_claude = os.getenv("CLAUDE_API")

# Initialize recognizer
recognizer = sr.Recognizer()

# Define wake words
wake_words = ["sana", "ava", "sara", "hey", "hi", "suli", "sully", "siri"]

def save_audio(audio, filename):
    audio_data = audio.get_wav_data()
    audio_segment = AudioSegment(data=audio_data)
    audio_segment.export(filename, format="wav")

def listen_for_wake_word():
    with sr.Microphone() as source:
        print("Listening for wake word...")
        while True:
            audio = recognizer.listen(source, phrase_time_limit=35)
            try:
                speech_text = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {speech_text}")
                if any(word in speech_text for word in wake_words):
                    print("Wake word detected!")
                    save_audio(audio, "uploads/recording.wav")
                    return "uploads/recording.wav"
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

def kurdish_transcribe_audio(api_key, audio_file, model="asr-large-beta", language="ckb"):
    url = "https://api.platform.krd/v1/audio/transcriptions"
    headers = {'Authorization': f'Bearer {api_key}'}
    files = {'file': ('audio_file.wav', open(audio_file, 'rb'), 'audio/wav')}
    data = {'model': model, 'response_format': 'json', 'language': language}
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as err:
        print(f"Error: {err}")

def kurdish_resposnse_parsing(audio_file):
    try:
        transcription_result = kurdish_transcribe_audio(PAWAN_API, audio_file)
        if transcription_result:
            transcription = transcription_result["text"]
            return transcription[::-1]
    except Exception as e:
        print(f"Error: {e}")
        return None

def send_text_to_anthropic(api_key_claude, kurdish_text):
    client = anthropic.Anthropic(api_key=api_key_claude)
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=5000,
        temperature=1,
        system="You are an AI assistant named \"سولی\" or \"Suli,\" derived from the city of Sulaymaniyah in Kurdistan. Your task is to convert smart home control requests into predefined commands and support multiple languages.\n\nAnalyze user input to identify smart home control intentions, especially for controlling lights in different rooms. If the request is not a smart home command, reflect that in the output.\n\n# Steps\n\n1. Analyze the input text to determine the room and action (ON/OFF) intended by the user, regardless of the input language.\n2. Match the room and action with an appropriate command from the predefined list.\n3. Use `LIGHTS_ON` or `LIGHTS_OFF` for general commands if a specific room is not mentioned.\n4. If the instruction is unclear, use `UNCLEAR_INSTRUCTION`.\n5. If the action is not feasible, use `NOT_ABLE_TO_DO`.\n6. If the input is unrelated to smart home commands, indicate with `NOT_SMART_HOME_INSTRUCTION`.\n\n# Output Format\n\nOutput a single command string corresponding to the user request or one of the alternative specified outcomes:\n- `LIVING_ROOM_LIGHTS_OFF`\n- `KITCHEN_LIGHTS_ON`\n- `BEDROOM_1_LIGHTS_ON`\n- `BEDROOM_2_LIGHTS_OFF`\n- `BATHROOM_LIGHTS_ON`\n- `GUEST_ROOM_LIGHTS_ON`\n- `HOT_KITCHEN_LIGHTS_ON`\n- `COLD_KITCHEN_LIGHTS_OFF`\n- `DINING_ROOM_LIGHTS_ON`\n- `LAUNDRY_ROOM_LIGHTS_OFF`\n- `GARAGE_LIGHTS_ON`\n- `LIGHTS_ON`\n- `UNCLEAR_INSTRUCTION`\n- `NOT_SMART_HOME_INSTRUCTION`\n- Etc. based on the described task.\n\n# Examples\n\n- **Input:** \"Turn off the lights in the living room.\"\n  - **Output:** `LIVING_ROOM_LIGHTS_OFF`\n\n- **Input:** \"Ich möchte das Licht in der Küche einschalten.\"\n  - **Output:** `KITCHEN_LIGHTS_ON`\n\n- **Input:** \"What's the weather like today?\"\n  - **Output:** `NOT_SMART_HOME_INSTRUCTION`\n  \n- **Input:** \"گڵۆپی ژووری  نوستنی یەکەم بکەرەوە\"\n  - **Output:** `BEDROOM_1_LIGHTS_ON`\n\n# Notes\n\n- Consider synonyms for \"turn on\" and \"turn off\" when recognizing commands.\n- Anticipate language and phrasing variations that may affect room identification.\n- If no specific room is mentioned, assume the command refers to all lights.\n- Recognize conditions or system limitations with `NOT_ABLE_TO_DO`.\n- Maintain the input language for context when generating responses.",
        messages=[{"role": "user", "content": kurdish_text}]
    )
    return message.content[0]

def extract_values(json_string):
    try:
        command_match = re.search(r'"command":\s*"([^"]+)"', json_string)
        message_match = re.search(r'"message":\s*"([^"]+)"', json_string)
        command = command_match.group(1) if command_match else ""
        message = message_match.group(1) if message_match else ""
        return command, message
    except re.error as e:
        print("Regex error:", e)
        return None, None

def control_led(command):
    print(f"Received command: {command}")
    if command == "LIGHTS_ON":
        print('Turning on all lights')
    elif command == "LIGHTS_OFF":
        print('Turning off all lights')
    else:
        print("Command not recognized or not able to perform.")

if __name__ == "__main__":
    while True:
        audio_file = listen_for_wake_word()
        if audio_file:
            kurdish_response = kurdish_resposnse_parsing(audio_file)
            response = send_text_to_anthropic(api_key_claude, kurdish_response)
            # command, message = extract_values(response)
            control_led(response.text)
            print(f"message: {response.text}")