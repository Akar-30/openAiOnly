import time
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import base64
from openai import OpenAI
from pydub import AudioSegment
import requests
import requests
import os
from dotenv import load_dotenv
 
# Kurdish API key 
load_dotenv()

PAWAN_API = os.getenv("PAWAN_API_KEY")

def kurdish_transcription(audio_file):
    # Since the file is already in MP3 format, no need to convert
    mp3_file = audio_file
    url = "https://api.platform.krd/v1/audio/transcriptions"
    headers = {
        "Authorization": "Bearer " + PAWAN_API
    }
    files = {
        "file": open(mp3_file, "rb")
    }
    data = {
        "model": "asr-large-beta",
        "response_format": "json",
        "noise_remover": "false",
        "language": "en"
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print(f"Error: {response.status_code}")
        return None


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

# Example usage

text = ".ەوارسان یتەبیات یروتلوک و دنەمەڵوەد یووژێم ،یواخاش و ناوج یتشورس ەب ەکەچوان .ایروس و ایکروت ،نارێئ ،قارێع کەو ادکێتاڵو دنەچ رەسەب ەووب شەباد ،تساڕەوان یتاڵەهژۆڕ ەتێوەکەد ەک ەیەروەگ یروتلوک و یفارگوج یکەیەچوان ناتسدروک"


    
if __name__ == "__main__":
    audio_file = "uploads/Recording-en.mp3"  # Ensure this path is correct
    # transcription = kurdish_transcription(audio_file)
    # print(transcription)
    try:
        audio_data = generate_speech(PAWAN_API, text, language="ckb")
        
        # Save the audio file
        with open(f"output.mp3", "wb") as f:
            f.write(audio_data)
        print(f"Audio saved to output.mp3")
    except Exception as e:
        print(f"Error: {e}")