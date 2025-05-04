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
        system="You are an AI assistant named \"سولی\" or \"Suli,\" derived from the city of Sulaymaniyah in Kurdistan. \n\nConvert any input regarding smart home controls into a predefined command from the specified list and support multiple languages.\n\nIdentify and match each user's request to the appropriate command for controlling lights within various rooms of the home. If the instruction is unclear, not achievable, or if it isn't a smart home command, use the respective commands for those situations.\n\n# Steps\n\n1. Analyze the input text to identify the room and action (ON/OFF) intended by the user, regardless of the input language.\n2. Match the determined room and action with one of the specified commands.\n3. If the input does not clearly indicate a specific room, use LIGHTS_ON or LIGHTS_OFF for general commands.\n4. If the instruction is unclear, use the command UNCLEAR_INSTRUCTION.\n5. If the requested action is not possible, use the command NOT_ABLE_TO_DO.\n6. If the input is not related to smart home instructions, indicate this in the output.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string selected from the specified command list.\n- A concise text that reflects the demand in the same language as the input, suitable for fast and small talk AI. For non-smart home instructions, directly answer the question when possible.\n\nIf the input isn't related to smart home instructions, the output should be:\n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"[Concise answer in the input language or direct answer]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"Turn off the lights in the living room.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"Turning off living room lights.\"\n}\n```\n\n**Example 2:**\n\n- **Input:** \"Ich möchte das Licht in der Küche einschalten.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"Licht in der Küche einschalten.\"\n}\n```\n\n**Example 3:**\n\n- **Input:** \"Quiero encender las luces en todas partes.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIGHTS_ON\",\n  \"message\": \"Enciende todas las luces.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"Can you set the mood lighting?\"\n- **Output:** \n```json\n{\n  \"command\": \"UNCLEAR_INSTRUCTION\",\n  \"message\": \"Instruction unclear.\"\n}\n```\n\n**Example 5:**\n\n- **Input:** \"What's the weather like today?\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Checking the weather.\"\n}\n```\n\n**Example 6:**\n\n- **Input:** \"What is the area of the Kurdistan Region\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Kurdistan Region covers about 40,643 square kilometers.\"\n}\n```\n\n# Notes\n\n- Consider synonyms or variations of \"turn on\" and \"turn off\" to determine the correct command.\n- Anticipate variations in phrasing or language that may affect room identification.\n- If no room is specified, assume the instruction refers to all lights.\n- If conditions or systems limit the ability to perform an action, opt for the NOT_ABLE_TO_DO response.\n- Ensure input language is detected and maintained in the output message.",
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
            command, message = extract_values(response)
            control_led(command)
            print(f"message: {message}")