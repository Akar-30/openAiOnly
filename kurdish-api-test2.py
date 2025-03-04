import requests
import os
from dotenv import load_dotenv
 
# Kurdish API key 
load_dotenv()

PAWAN_API = os.getenv("PAWAN_API_KEY")


def transcribe_audio(api_key, audio_file, model="asr-large-beta", language="ckb", noise_remover=False):
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
        'file': ('audio_file.mp3', open(audio_file, 'rb'), 'audio/mp3')
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

# Example usage
audio_file = "uploads/kurdi-trump.mp3"

try:
    transcription_result = transcribe_audio(PAWAN_API, audio_file)
    if transcription_result:
        transcription = transcription_result["text"]
        final_transcription = transcription[::-1]
        print("Transcription result:", final_transcription)
except Exception as e:
    print(f"Error: {e}")