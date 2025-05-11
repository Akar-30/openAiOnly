import io
import os
import re
import RPi.GPIO as GPIO
import time
from dotenv import load_dotenv
import requests
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import base64
import numpy as np
from openai import OpenAI
from pydub import AudioSegment
import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Initialize GPIO and other components
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define GPIO pins for each room and status LEDs
LED_PINS = {
    "LIVING_ROOM": 17,  # GPIO 17
    "KITCHEN": 27,      # GPIO 27
    "BATHROOM": 22,     # GPIO 22
    "BEDROOM": 23       # GPIO 23
}
GREEN_LED_PIN = 24  # GPIO 24 for green LED
RED_LED_PIN = 25    # GPIO 25 for red LED

# Setup GPIO pins as output
for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Setup GPIO pins for status LEDs as output
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
GPIO.output(GREEN_LED_PIN, GPIO.LOW)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.output(RED_LED_PIN, GPIO.LOW)

# Initialize recognizer
recognizer = sr.Recognizer()

# Initialize client with API key
# Kurdish API key
load_dotenv()

PAWAN_API = os.getenv("PAWAN_API_KEY")
api_key_claude = os.getenv("CLAUDE_API")
api_key = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_USERNAME = "@KurdiAiBot"  # Replace with your bot's username
# Ensure voice_messages directory exists
VOICE_DIR = "voice_messages"
os.makedirs(VOICE_DIR, exist_ok=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me text or a voice message and I'll process it!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    This bot can process both text and voice messages.
    
    Just send me:
    - Any text message
    - A voice note
    
    I'll process it and send you back the result.
    """
    await update.message.reply_text(help_text)


def process_text(text: str) -> str:
    """Process text input and return response"""
    # Your custom processing logic here
    history=[]
    response = send_text_to_anthropic(api_key_claude, text, history)
    response_text = response.text  # Extract the text attribute from the TextBlock object
    command,  message = extract_values(response_text)
    control_led(command)
    # processed_text = f"You sent: {text}. This has been processed."
    return message


def process_voice(file_path: str) -> str:
    """Convert voice message to text and process it"""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return f"I heard: {text}"
            
    except Exception as e:
        print(f"Voice recognition error: {e}")
        return "Sorry, I couldn't understand that voice message."

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = process_text(text)
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        voice_file = await voice.get_file()
        
        # Create unique file path
        file_path = os.path.join(VOICE_DIR, f"{voice.file_id}.ogg")
        
        # Download the voice file
        await voice_file.download_to_drive(file_path)
        
        # Convert the voice file to WAV format for processing
        wav_file_path = os.path.splitext(file_path)[0] + ".wav"
        audio = AudioSegment.from_file(file_path)
        audio.export(wav_file_path, format="wav")
        
        # Process the voice message
        kurdish_response = kurdish_resposnse_parsing(wav_file_path)
        response = send_text_to_anthropic(api_key_claude, kurdish_response, history)
        response_text = response.text  # Extract the text attribute from the TextBlock object
        command, message = extract_values(response_text)
        control_led(command)
        print(f"message: {message}")
        
        # Generate speech from the response message
        try:
            audio_data = generate_speech(PAWAN_API, message, language="ckb")
            
            # Save the audio file
            audio_file_path = os.path.join(VOICE_DIR, f"{voice.file_id}_response.mp3")
            with open(audio_file_path, "wb") as f:
                f.write(audio_data)
            print(f"Audio saved to {audio_file_path}")
            
            # Send the audio and text response back to the user
            await update.message.reply_text(message)
            await update.message.reply_audio(audio=open(audio_file_path, "rb"))
            
            # Optional: Remove the files after processing
            os.remove(file_path)
            os.remove(wav_file_path)
            os.remove(audio_file_path)
        
        except Exception as e:
            print(f"Error generating or sending audio: {e}")
            await update.message.reply_text("Sorry, I couldn't generate the audio response. Please try again.")
    
    except Exception as e:
        print(f"Error processing voice message: {e}")
        await update.message.reply_text("Sorry, I couldn't process that voice message. Please try again.")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")
    await update.message.reply_text("An error occurred. Please try again.")


client = OpenAI(api_key=api_key)
    


# Define the wake words
wake_words = ["sari","siri", "Sari", "hy", "hey", "hi", "Sari", "Sari", "haile", "Hasari", "ei", "eye", "el"]

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

def generate_speech_chatgpt(message):
    try:
        # Generate speech and save it to a file
        speech_file_path = "output.mp3"
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="nova",
            input=message,
            speed=1.4,
            instructions="Please speak in a clear and friendly Kurdish tone.",
            
        )
        response.stream_to_file(speech_file_path)
        print(f"Audio saved to {speech_file_path}")
        
        # Play the audio file
        audio = AudioSegment.from_file(speech_file_path)
        # Increase the sample rate to improve audio quality
        audio = audio.set_frame_rate(24000)
        # Play the audio file
        sd.play(np.array(audio.get_array_of_samples()), samplerate=audio.frame_rate)
        sd.wait()
    except Exception as e:
        print(f"Error generating speech: {e}")


# Function to control LEDs
def control_led(command):
    print(f"Received command: {command}")
    GPIO.output(RED_LED_PIN, GPIO.LOW)  # Turn off red LED initially
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
        GPIO.output(RED_LED_PIN, GPIO.HIGH)  # Turn on red LED for failed command

def save_audio(audio, filename):
    audio_data = audio.get_wav_data()
    audio_segment = AudioSegment(data=audio_data)
    
    # Skip the first 1 second
    trimmed_audio_segment = audio_segment[700:]
    
    # Export the trimmed audio segment to a file
    trimmed_audio_segment.export(filename, format="wav")

def listen_for_wake_word():
    with sr.Microphone() as source:
        print("Listening for wake word...")
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)  # Turn on green LED when listening
        while True:
            # Listen for audio input
            audio = recognizer.listen(source, phrase_time_limit=15)
            try:
                # Recognize speech using Google Web Speech API
                speech_text = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {speech_text}")
                
                # Check if any wake word is in the recognized speech
                if any(word in speech_text for word in wake_words):
                    print("Wake word detected!")
                    GPIO.output(GREEN_LED_PIN, GPIO.LOW)  # Turn off green LED after detection
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
    
def send_text_to_anthropic(api_key_claude, kurdish_text, conversation_history):
    client = anthropic.Anthropic(api_key=api_key_claude)

    if conversation_history.__len__() > 13:
        conversation_history.pop(0)
        conversation_history.pop(0)

    # Add the new user message to history
    conversation_history.append({"role": "user", "content": kurdish_text})
    print("Conversation history:", conversation_history)
    # Validate conversation history
    for message in conversation_history:
        if "role" not in message or "content" not in message:
            raise ValueError(f"Invalid message format: {message}. Each message must have 'role' and 'content'.")

    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=5000,
            temperature=1,
            # system="You are an AI assistant named \"سولی\" or \"Suli,\" derived from the city of Sulaymaniyah in Kurdistan. You speak Kurdish and have a joyful personality that delights users with your sweet words when interacting with them. Your Kurdish words are local and cultural words.\n\nConvert any input regarding smart home controls into a predefined command from the specified list.\n\nIdentify and match each user's request to the appropriate command for controlling lights within various rooms of the home. If the instruction is unclear, not achievable, or if it isn't a smart home command, use the respective commands for those situations.\n\n# Steps\n\n1. Analyze the input text to identify the room and action (ON/OFF) intended by the user, regardless of the input language.\n2. Match the determined room and action with one of the specified commands.\n3. If the input does not clearly indicate a specific room, use LIGHTS_ON or LIGHTS_OFF for general commands.\n4. If the instruction is unclear, use the command UNCLEAR_INSTRUCTION.\n5. If the requested action is not possible, use the command NOT_ABLE_TO_DO.\n6. If the input is not related to smart home instructions, indicate this in the output.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string selected from the specified command list.\n- A concise text that reflects the demand in the same language as the input, suitable for fast and small talk AI. For non-smart home instructions, directly answer the question when possible.\n\nIf the input isn't related to smart home instructions, the output should be:\n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"[Concise answer in the input language or direct answer]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"Turn off the lights in the living room.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"Turning off living room lights.\"\n}\n```\n\n**Example 2:**\n\n- **Input:** \"Ich möchte das Licht in der Küche einschalten.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"Licht in der Küche einschalten.\"\n}\n```\n\n**Example 3:**\n\n- **Input:** \"Quiero encender las luces en todas partes.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIGHTS_ON\",\n  \"message\": \"Enciende todas las luces.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"Can you set the mood lighting?\"\n- **Output:** \n```json\n{\n  \"command\": \"UNCLEAR_INSTRUCTION\",\n  \"message\": \"Instruction unclear.\"\n}\n```\n\n**Example 5:**\n\n- **Input:** \"What's the weather like today?\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Checking the weather.\"\n}\n```\n\n**Example 6:**\n\n- **Input:** \"What is the area of the Kurdistan Region\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Kurdistan Region covers about 40,643 square kilometers.\"\n}\n```\n\n# Notes\n\n- Consider synonyms or variations of \"turn on\" and \"turn off\" to determine the correct command.\n- Anticipate variations in phrasing or language that may affect room identification.\n- If no room is specified, assume the instruction refers to all lights.\n- If conditions or systems limit the ability to perform an action, opt for the NOT_ABLE_TO_DO response.\n- Ensure input language is detected and maintained in the output message.",
            # system = "You are an AI assistant named \"ساری\" or \"Sari\". You speak Kurdish using daily, local, and cultural vocabulary. Your applications include smart home control instructions, language learning and translation, and providing the latest information on the web.\n\nConvert any input regarding smart home controls, education, or web information requests into a predefined command from the specified list. Identify and match each user's request to the appropriate command. If the instruction is unclear, not achievable, or doesn't fit any application, use the respective commands for those situations.\n\n# Steps\n\n1. Analyze the input text to identify its context: smart home control, language learning, translation, education, or web information request.\n2. For smart home controls, identify the room and action (ON/OFF) regardless of the input language.\n3. Match the determined context with one of the specified commands.\n4. If the input does not clearly indicate a specific context, use UNCLEAR_INSTRUCTION or NOT_ABLE_TO_DO.\n5. Translate words or sentences when language learning or translation is required, and use the command EDUCATION.\n6. Provide the latest news, weather or stock information, and use the command WEB.\n7. If the input doesn't fit any of the applications, indicate this in the output.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string from the specified command list.\n- A concise text that reflects the request in the same language as the input, suitable for fast and small talk AI. For instructions not related to any application, directly answer the question when possible.\n\nIf the input isn't related to any application area, the output should be:\n```json\n{\n  \"command\": \"NOT_APPLICATION_RELATED\",\n  \"message\": \"[Concise answer in the input language or direct answer]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"گڵۆپەکانی ژووری دانیشتن بکوژێنەوە.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"گڵۆپەکانی ژووری دانیشتن دەکوژێنمەوە.\"\n}\n```\n\n**Example 2:**\n\n- **Input:** \"دەمەوێت ڕووناکی چێشتخانە هەڵبکەم.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"ڕووناکی چێشتخانە هەڵدەکەم.\"\n}\n```\n\n**Example 3:**\n\n- **Input:** \"سڵاو، وەربگێڕە بۆ فەڕەنسی.\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"وەرگێڕانی 'سڵاو' بۆ فەڕەنسی: 'bonjour'.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"ئەمڕۆ کەش و هەوا چۆنە؟\"\n- **Output:** \n```json\n{\n  \"command\": \"WEB\",\n  \"message\": \"ئەمڕۆ هەوا خۆر و ٣٢ پلە سەنتیگرادە.\"\n}\n```\n\n**Example 5:**\n\n- **Input:** \"کۆتا یاری ڕیاڵ مەدرید چۆن بوو؟\"\n- **Output:** \n```json\n{\n  \"command\": \"WEB\",\n  \"message\": \"ڕیاڵ مەدرید یاریەکەی لە بارشەلۆنە بردەوە بە ئنجامی ٢ بە ١\"\n}\n```\n\n**Example 6:**\n\n- **Input:** \"نرخی بتکۆین چەندە؟\"\n- **Output:** \n```json\n{\n  \"command\": \"WEB\",\n  \"message\": \"فۆتۆسینسێز پڕۆسەیەکە کە ڕووەکەکان بەکاریدەهێنن بۆ گۆڕینی تیشکی خۆر بۆ وزە.\"\n}\n```\n\n**Example 7:**\n\n- **Input:** \"پێناسەی فۆتۆسینسێز چییە؟\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"بتکۆین ئێستا بە ١٠١٢٣٠ دۆلار مامەڵەی پێوە دەکرێت.\"\n}\n```\n\n\n**Example 8:**\n\n- **Input:** \"ناوی پایتەختەکانی وڵاتانی سکەندەناڤیا چین؟\"\n- **Output:*پایتەختەکانی وڵاتانی سکەندەناڤیا: ستۆکهۆڵم (سوید)، ئۆسلۆ (نەرویج)، کۆپنهاگن (دانیمارک)، هێلسنکی (فینلەند)، ڕیکیاڤیک (ئایسلەند).* \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"\"\n}\n```\n\n\n**Example 9:**\n\n- **Input:** \"تایبەتمەندییەکانی ڕۆمانی کلاسیکی کوردی چین؟\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"ڕۆمانی کلاسیکی کوردی تایبەتمەندی گێڕانەوەی کەلتووری نەتەوەیی، کێشە کۆمەڵایەتییەکان، خەباتی نەتەوەیی، و وێنەکێشانی سروشتی کوردستانی هەیە.\"\n}\n```\n\n\n**Example 10:**\n\n- **Input:** \"هاوکێشەی ئاینشتاین E=mc² چی دەگەیەنێت؟\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"هاوکێشەی E=mc² ئەوە دەگەیەنێت کە وزە (E) یەکسانە بە بارستە (m) جار خێرایی ڕووناکی بە توانی دوو (c²)، واتە وزە و بارستە دەکرێت بگۆڕدرێن بۆ یەکتری.\"\n}\n```\n\n\n**Example 11:**\n\n- **Input:** \"تکایە ئەم ڕستەیە وەربگێڕە بۆ زمانی ئینگلیزی: کوردستان وڵاتێکی جوانە بە سروشتێکی دڵڕفێن.\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"وەرگێڕان: 'Kurdistan is a beautiful country with enchanting nature.'\"\n}\n```\n\n\n**Example 12:**\n\n- **Input:** \"ئەم پەیامە وەربگێڕە بۆ ئینگلیزی: من خوێندکارم و دەمەوێت زمانی ئینگلیزی فێربم بۆ ئەوەی بتوانم لە دەرەوەی وڵات درێژە بە خوێندن بدەم.\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"وەرگێڕان: 'I am a student and I want to learn English so that I can continue my studies abroad.'\"\n}\n```\n\n# Notes\n\n- Anticipate variations in phrasing or language for all application areas.\n- Use the EDUCATION command for language learning or translation and WEB for general web inquiries.\n- Maintain the input language in the output response where applicable.\n- Ensure that any response about specific information like weather or stock prices is direct and reflects the specific request.",
            # system = "Convert any input regarding smart home controls into a predefined command from the specified list, taking input in Kurdish and ensuring outputs are polite and culturally considerate in the Kurdish language.\n\nIdentify and match each user's request to the appropriate command for controlling lights within various rooms of the home. If the instruction is unclear, not achievable, or if it isn't a smart home command, use the respective commands for those situations. Ensure politeness and cultural relevance in all output messages.\n\n# Steps\n\n1. Analyze the input text in Kurdish to identify the room and action (ON/OFF) intended by the user.\n2. Match the determined room and action with one of the specified commands.\n3. If the input does not clearly indicate a specific room, use LIGHTS_ON or LIGHTS_OFF for general commands.\n4. If the instruction is unclear, use the command UNCLEAR_INSTRUCTION.\n5. If the requested action is not possible, use the command NOT_ABLE_TO_DO.\n6. If the input is not related to smart home instructions, indicate this in the output with a polite Kurdish response.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string selected from the specified command list.\n- A polite and culturally considerate text in Kurdish that reflects the demand. For non-smart home instructions, directly answer the question politely when possible.\n\nIf the input isn't related to smart home instructions, the output should be:\n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"[Polite answer in Kurdish]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"گڵۆپەکانی ژووری دانیشتن بکوژێنەوە.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"گڵۆپەکانی ژووری دانیشتن دەکوژێنمەوە.\"\n}\n\n```\n\n**Example 2:**\n\n- **Input:** \"دەمەوێت ڕووناکی چێشتخانە هەڵبکەم.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"ڕووناکی چێشتخانە هەڵدەکەم.\"\n}\n\n```\n\n**Example 3:**\n\n- **Input:** \"هەموو گڵۆپەکانم بۆ ڕۆشن بکەرەوە\"\n- **Output:** \n```json\n{\n  \"command\": \"LIGHTS_ON\",\n  \"message\": \" هەموو گڵۆپەکانم ڕۆشن کردەوە.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"ناوی پایتەختەکانی وڵاتانی سکەندەناڤیا چین؟\"\n- **Output:*پایتەختەکانی وڵاتانی سکەندەناڤیا: ستۆکهۆڵم (سوید)، ئۆسلۆ (نەرویج)، کۆپنهاگن (دانیمارک)، هێلسنکی (فینلەند)، ڕیکیاڤیک (ئایسلەند).* \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"\"\n}\n\n```\n\n**Example 5:**\n\n*Input:** \"تایبەتمەندییەکانی ڕۆمانی کلاسیکی کوردی چین؟\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"ڕۆمانی کلاسیکی کوردی تایبەتمەندی گێڕانەوەی کەلتووری نەتەوەیی، کێشە کۆمەڵایەتییەکان، خەباتی نەتەوەیی، و وێنەکێشانی سروشتی کوردستانی هەیە.\"\n}\n\n```\n\n**Example 6:**\n\n- **Input:** \"دەتوانیت گڵۆپی ژووری نوستن بکوژێنیتەوە\"\n- **Output:** \n```json\n{\n  \"command\": \"BEDROOM_LIGHTS_OFF\",\n  \"message\": \"بەڵێ، گلۆپی ژووری نووستنم کوژاندەوە\"\n}\n```\n\n# Notes\n\n- Consider synonyms or variations of \"turn on\" and \"turn off\" in Kurdish to determine the correct command.\n- Anticipate variations in phrasing or language in Kurdish that may affect room identification.\n- If no room is specified, assume the instruction refers to all lights.\n- If conditions or systems limit the ability to perform an action, opt for the NOT_ABLE_TO_DO response.\n- Ensure Kurdish language is used and maintained in the output message with politeness and cultural sensitivity.",
            system = "Convert any input regarding smart home controls into a predefined command from the specified list, taking input in Kurdish and ensuring outputs are polite and culturally considerate in the Kurdish language.\n\nIdentify and match each user's request to the appropriate command for controlling lights within the four rooms: LIVING_ROOM, KITCHEN, BEDROOM, and BATHROOM. If the instruction is unclear, not achievable, or if it isn't a smart home command, use the respective commands for those situations. Ensure politeness and cultural relevance in all output messages.\n\n# Steps\n\n1. Analyze the input text in Kurdish to identify the room and action (ON/OFF) intended by the user.\n2. Match the determined room and action with one of the specified commands.\n3. If the input does not clearly indicate a specific room, use LIGHTS_ON or LIGHTS_OFF for general commands.\n4. If the instruction is unclear, use the command UNCLEAR_INSTRUCTION.\n5. If the requested action is not possible, use the command NOT_ABLE_TO_DO.\n6. If the input is not related to smart home instructions, indicate this in the output with a polite Kurdish response.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string selected from the specified command list.\n- A polite and culturally considerate text in Kurdish that reflects the demand. For non-smart home instructions, directly answer the question politely when possible.\n\nIf the input isn't related to smart home instructions, the output should be:\n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"[Polite answer in Kurdish]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"گڵۆپەکانی ژووری دانیشتن بکوژێنەوە.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"گڵۆپەکانی ژووری دانیشتن دەکوژێنمەوە.\"\n}\n\n```\n\n**Example 2:**\n\n- **Input:** \"دەمەوێت ڕووناکی چێشتخانە هەڵبکەم.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"ڕووناکی چێشتخانە هەڵدەکەم.\"\n}\n\n```\n\n**Example 3:**\n\n- **Input:** \"هەموو گڵۆپەکانم بۆ ڕۆشن بکەرەوە\"\n- **Output:** \n```json\n{\n  \"command\": \"LIGHTS_ON\",\n  \"message\": \" هەموو گڵۆپەکانم ڕۆشن کردەوە.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"ناوی پایتەختەکانی وڵاتانی سکەندەناڤیا چین؟\"\n- **Output:*پایتەختەکانی وڵاتانی سکەندەناڤیا: ستۆکهۆڵم (سوید)، ئۆسلۆ (نەرویج)، کۆپنهاگن (دانیمارک)، هێلسنکی (فینلەند)، ڕیکیاڤیک (ئایسلەند).* \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"\"\n}\n\n```\n\n**Example 5:**\n\n*Input:** \"تایبەتمەندییەکانی ڕۆمانی کلاسیکی کوردی چین؟\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"ڕۆمانی کلاسیکی کوردی تایبەتمەندی گێڕانەوەی کەلتووری نەتەوەیی، کێشە کۆمەڵایەتییەکان، خەباتی نەتەوەیی، و وێنەکێشانی سروشتی کوردستانی هەیە.\"\n}\n\n```\n\n**Example 6:**\n\n- **Input:** \"دەتوانیت گڵۆپی ژووری نوستن بکوژێنیتەوە\"\n- **Output:** \n```json\n{\n  \"command\": \"BEDROOM_LIGHTS_OFF\",\n  \"message\": \"بەڵێ، گلۆپی ژووری نووستنم کوژاندەوە.\"\n}\n```\n\n# Notes\n\n- Consider synonyms or variations of \"turn on\" and \"turn off\" in Kurdish to determine the correct command.\n- Anticipate variations in phrasing or language in Kurdish that may affect room identification.\n- If no room is specified, assume the instruction refers to all lights.\n- If conditions or systems limit the ability to perform an action, opt for the NOT_ABLE_TO_DO response.\n- Ensure Kurdish language is used and maintained in the output message with politeness and cultural sensitivity.",
 
            messages=conversation_history
        )

        response = message.content[0]
        command, kurdi_message = extract_values(response.text)

        # Add Claude's response to history
        if kurdi_message.strip():  # Ensure the message content is not empty
            conversation_history.append({"role": "assistant", "content": response})
        else:
            print("Warning: Skipping appending an empty assistant message.")
            conversation_history.pop()
        print("Conversation history:", conversation_history)
        return response

    except anthropic.BadRequestError as e:
        print(f"Anthropic API error: {e}")
        return None

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
    history=[]  # Initialize conversation history
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Error handler
    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)
    while True:
        audio_file = listen_for_wake_word()
        if audio_file:
            kurdish_response = kurdish_resposnse_parsing(audio_file)
            response = send_text_to_anthropic(api_key_claude, kurdish_response, history)
            response_text = response.text  # Extract the text attribute from the TextBlock object
            command,  message = extract_values(response_text)
            control_led(command)
            # message = message[::-1]
            print(f"message: {message}")
        try:
            audio_data = generate_speech(PAWAN_API, message, language="ckb")
            # audio_data = generate_speech_chatgpt(message)
            
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
