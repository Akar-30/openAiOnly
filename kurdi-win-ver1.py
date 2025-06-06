import io
import re
import time
import sounddevice as sd
import soundfile as sf
import numpy as np
import speech_recognition as sr
from pydub import AudioSegment
import requests
import anthropic
import json
import os
from dotenv import load_dotenv

# Initialize recognizer
recognizer = sr.Recognizer()

# Kurdish API key
load_dotenv()

PAWAN_API = os.getenv("PAWAN_API_KEY")
api_key_claude = os.getenv("CLAUDE_API")


    
# Define the wake words
wake_words = ["sana", "ava", "sara", "hey", "hi", "suli", "sully", "siri"]

# Send the audio to the kurdish api
def kurdish_transcribe_audio(api_key, audio_file, model="asr-large-beta", language="ckb", noise_remover=False):
    """
    Transcribe speech from an audio file using the API.
    
    :param api_key: Your API key
    :param audio_file: Path to the audio file
    :param model: ASR model to use (default="asr-large-beta")
    :param language: Language of the audio (default="en")
    :param noise_remover: Whether to enable noise removal (default=False)
    :return: Transcription result in JSON format
    """
    url = "https://api.platform.krd/v1/audio/transcriptions"
    
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    files = {
        'file': ('audio_file.wav', open(audio_file, 'rb'), 'audio/wav')
    }
    
    data = {
        'model': model,
        'response_format': 'json',
        'noise_remover': str(noise_remover).lower(),
        'language': language
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content}")
    except Exception as err:
        print(f"Other error occurred: {err}")

# Generate speech from text using the API
def generate_speech(api_key, text, language="ckb", voice="default"):
    """
    Generate speech from text using the API.
    
    :param api_key: Your API key
    :param text: Text to convert to speech
    :param language: Language code (e.g., 'en', 'ckb')
    :param voice: Voice to use (default="default")
    :return: Audio data
    """
    url = "https://api.platform.krd/v1/audio/speech"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'audio/mp3'
    }
    
    data = {
        'model': 'tts-mini-exp',
        'input': text,
        'language': language,
        'voice': voice,
        'response_format': 'mp3',
        'speed': 1.3,
        'sample_rate': 16000
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    return response.content

# Function to control LEDs (simulated with print statements)
def control_led(command):
    print(f"Received command: {command}")
    if command == "LIVING_ROOM_LIGHTS_ON":
        print('Turning on living room lights')
    elif command == "LIVING_ROOM_LIGHTS_OFF":
        print('Turning off living room lights')
    elif command == "KITCHEN_LIGHTS_ON":
        print('Turning on kitchen lights')
    elif command == "KITCHEN_LIGHTS_OFF":
        print('Turning off kitchen lights')
    elif command == "BATHROOM_LIGHTS_ON":
        print('Turning on bathroom lights')
    elif command == "BATHROOM_LIGHTS_OFF":
        print('Turning off bathroom lights')
    elif command == "BEDROOM_LIGHTS_ON":
        print('Turning on bedroom lights')
    elif command == "BEDROOM_LIGHTS_OFF":
        print('Turning off bedroom lights')
    elif command == "LIGHTS_ON":
        print('Turning on all lights')
    elif command == "LIGHTS_OFF":
        print('Turning off all lights')
    else:
        print("Command not recognized or not able to perform.")
        print("command: ",command)

def save_audio(audio, filename):
    audio_data = audio.get_wav_data()
    audio_segment = AudioSegment(data=audio_data)
    
    # # Skip the first 1 second
    # trimmed_audio_segment = audio_segment[700:]
    
    # # Export the trimmed audio segment to a file
    # trimmed_audio_segment.export(filename, format="wav")
    audio_segment.export(filename, format="wav")

def listen_for_wake_word():
    with sr.Microphone() as source:
        print("Listening for wake word...")
        while True:
            # Listen for audio input
            audio = recognizer.listen(source, phrase_time_limit=35)
            try:
                # Recognize speech using Google Web Speech API
                speech_text = recognizer.recognize_google(audio).lower()
                # print(f"Recognized: {speech_text}")
                
                # Check if any wake word is in the recognized speech
                if any(word in speech_text for word in wake_words):
                    print("Wake word detected!")
                    save_audio(audio, "uploads/recording.wav")
                    return "uploads/recording.wav"
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")



def kurdish_resposnse_parsing(audio_file):
    try:
        transcription_result = kurdish_transcribe_audio(PAWAN_API, audio_file)
        if transcription_result:
            transcription = transcription_result["text"]
            final_transcription = transcription[::-1]
            print("Transcription result:", final_transcription)
            return final_transcription
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def send_text_to_anthropic(api_key_claude, kurdish_text):
    client = anthropic.Anthropic(api_key=api_key_claude)
    
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=5000,
        temperature=1,
        system="You are an AI assistant named \"سولی\" or \"Suli,\" derived from the city of Sulaymaniyah in Kurdistan. You speak Kurdish and have a joyful personality that delights users with your sweet words when interacting with them.\n\nConvert any input regarding smart home controls into a predefined command from the specified list and support multiple languages.\n\nIdentify and match each user's request to the appropriate command for controlling lights within various rooms of the home. If the instruction is unclear, not achievable, or if it isn't a smart home command, use the respective commands for those situations.\n\n# Steps\n\n1. Analyze the input text to identify the room and action (ON/OFF) intended by the user, regardless of the input language.\n2. Match the determined room and action with one of the specified commands.\n3. If the input does not clearly indicate a specific room, use LIGHTS_ON or LIGHTS_OFF for general commands.\n4. If the instruction is unclear, use the command UNCLEAR_INSTRUCTION.\n5. If the requested action is not possible, use the command NOT_ABLE_TO_DO.\n6. If the input is not related to smart home instructions, indicate this in the output.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string selected from the specified command list.\n- A concise text that reflects the demand in the same language as the input, suitable for fast and small talk AI. For non-smart home instructions, directly answer the question when possible.\n\nIf the input isn't related to smart home instructions, the output should be:\n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"[Concise answer in the input language or direct answer]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"Turn off the lights in the living room.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"Turning off living room lights.\"\n}\n```\n\n**Example 2:**\n\n- **Input:** \"Ich möchte das Licht in der Küche einschalten.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"Licht in der Küche einschalten.\"\n}\n```\n\n**Example 3:**\n\n- **Input:** \"Quiero encender las luces en todas partes.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIGHTS_ON\",\n  \"message\": \"Enciende todas las luces.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"Can you set the mood lighting?\"\n- **Output:** \n```json\n{\n  \"command\": \"UNCLEAR_INSTRUCTION\",\n  \"message\": \"Instruction unclear.\"\n}\n```\n\n**Example 5:**\n\n- **Input:** \"What's the weather like today?\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Checking the weather.\"\n}\n```\n\n**Example 6:**\n\n- **Input:** \"What is the area of the Kurdistan Region\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Kurdistan Region covers about 40,643 square kilometers.\"\n}\n```\n\n# Notes\n\n- Consider synonyms or variations of \"turn on\" and \"turn off\" to determine the correct command.\n- Anticipate variations in phrasing or language that may affect room identification.\n- If no room is specified, assume the instruction refers to all lights.\n- If conditions or systems limit the ability to perform an action, opt for the NOT_ABLE_TO_DO response.\n- Ensure input language is detected and maintained in the output message.",
        messages=[
            {
                "role": "user",
                "content": kurdish_text
            }
        ]
    )
    
    # print(message.content)
    return message.content[0]

def extract_values(json_string):
    try:
        # Use regular expressions to extract command and message
        command_match = re.search(r'"command":\s*"([^"]+)"', json_string)
        message_match = re.search(r'"message":\s*"([^"]+)"', json_string)
        
        command = command_match.group(1) if command_match else ""
        message = message_match.group(1) if message_match else ""
        
        return command, message
    except re.error as e:
        print("Regex error:", e)
        return None, None

if __name__ == "__main__":
    while True:
        audio_file = listen_for_wake_word()
        if audio_file:
            kurdish_response = kurdish_resposnse_parsing(audio_file)
            response = send_text_to_anthropic(api_key_claude, kurdish_response)
            response_text = response.text  # Extract the text attribute from the TextBlock object
            command,  message = extract_values(response_text)
            control_led(command)
            # message = message[::-1]
            print(f"message: {message}")
        try:
            audio_data = generate_speech(PAWAN_API, message, language="ckb")
            
            # Save the audio file
            with open(f"output.mp3", "wb") as f:
                f.write(audio_data)
            print(f"Audio saved to output.mp3")
            # Play the audio file
            audio_array, _ = sf.read(io.BytesIO(audio_data), dtype='int16')
            sd.play(audio_array, samplerate=16000)
            sd.wait()
            # os.remove("output.mp3")
        except Exception as e:
            print(f"Error: {e}")
