import io
import re
import time
from openai import OpenAI
import sounddevice as sd
import soundfile as sf
import numpy as np
import speech_recognition as sr
from pydub import AudioSegment
import requests
import anthropic
import json
import os
import noisereduce as nr
from dotenv import load_dotenv


# Initialize recognizer
recognizer = sr.Recognizer()

# Kurdish API key
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
PAWAN_API = os.getenv("PAWAN_API_KEY")
api_key_claude = os.getenv("CLAUDE_API")

client = OpenAI(api_key=api_key)
    
# Define the wake words
# wake_words = ["sara", "hey", "hi", "suli", "sully", "siri", "slow", "sule", "suley", "sulley", "sul"]
wake_words = ["lina", "lena","hy", "hey", "hi", "Lena", "Lina", "haile", "Halina"]

# Send the audio to the kurdish api
def kurdish_transcribe_audio(api_key, audio_file, language="ckb", noise_remover=False):
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
        'model': "asr-large-beta",
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
def generate_speech(message):
    try:
        # Generate speech and save it to a file
        speech_file_path = "output.mp3"
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="nova",
            input=message,
            speed=1.2,
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

# def save_audio(audio, filename):
#     audio_data = audio.get_wav_data()
#     audio_segment = AudioSegment(data=audio_data, sample_width=2, frame_rate=16000, channels=1)
    
#     # Apply noise reduction
#     audio_segment = audio_segment.low_pass_filter(3000)  # Remove high-frequency noise
#     audio_segment = audio_segment.high_pass_filter(100)  # Remove low-frequency noise
    
#     # Export the processed audio
#     audio_segment.export(filename, format="wav")

# def save_audio(audio, filename):
#     audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
#     sample_rate = audio.sample_rate  # Dynamically get the sample rate from the audio input
    
#     # Reduce noise
#     reduced_noise = nr.reduce_noise(y=audio_data, sr=sample_rate)
    
#     # Save the processed audio
#     sf.write(filename, reduced_noise, sample_rate)

def listen_for_wake_word():
    with sr.Microphone() as source:
        print("Listening for wake word...")
        recognizer.adjust_for_ambient_noise(source, duration=2)  # Increase duration to adapt to noise
        while True:
            try:
                # Listen for audio input with a longer phrase time limit
                audio = recognizer.listen(source, phrase_time_limit=35)
                # Recognize speech using Google Web Speech API
                speech_text = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {speech_text}")
                
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
            system = "You are an AI assistant named \"لینا\" or \"Lina\". You speak Kurdish using daily, local, and cultural vocabulary. Your applications include smart home control instructions, language learning and translation, and providing the latest information on the web.\n\nConvert any input regarding smart home controls, education, or web information requests into a predefined command from the specified list. Identify and match each user's request to the appropriate command. If the instruction is unclear, not achievable, or doesn't fit any application, use the respective commands for those situations.\n\n# Steps\n\n1. Analyze the input text to identify its context: smart home control, language learning, translation, education, or web information request.\n2. For smart home controls, identify the room and action (ON/OFF) regardless of the input language.\n3. Match the determined context with one of the specified commands.\n4. If the input does not clearly indicate a specific context, use UNCLEAR_INSTRUCTION or NOT_ABLE_TO_DO.\n5. Translate words or sentences when language learning or translation is required, and use the command EDUCATION.\n6. Provide the latest news, weather or stock information, and use the command WEB.\n7. If the input doesn't fit any of the applications, indicate this in the output.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string from the specified command list.\n- A concise text that reflects the request in the same language as the input, suitable for fast and small talk AI. For instructions not related to any application, directly answer the question when possible.\n\nIf the input isn't related to any application area, the output should be:\n```json\n{\n  \"command\": \"NOT_APPLICATION_RELATED\",\n  \"message\": \"[Concise answer in the input language or direct answer]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"گڵۆپەکانی ژووری دانیشتن بکوژێنەوە.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"گڵۆپەکانی ژووری دانیشتن دەکوژێنمەوە.\"\n}\n```\n\n**Example 2:**\n\n- **Input:** \"دەمەوێت ڕووناکی چێشتخانە هەڵبکەم.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"ڕووناکی چێشتخانە هەڵدەکەم.\"\n}\n```\n\n**Example 3:**\n\n- **Input:** \"سڵاو، وەربگێڕە بۆ فەڕەنسی.\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"وەرگێڕانی 'سڵاو' بۆ فەڕەنسی: 'bonjour'.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"ئەمڕۆ کەش و هەوا چۆنە؟\"\n- **Output:** \n```json\n{\n  \"command\": \"WEB\",\n  \"message\": \"ئەمڕۆ هەوا خۆر و ٣٢ پلە سەنتیگرادە.\"\n}\n```\n\n**Example 5:**\n\n- **Input:** \"کۆتا یاری ڕیاڵ مەدرید چۆن بوو؟\"\n- **Output:** \n```json\n{\n  \"command\": \"WEB\",\n  \"message\": \"ڕیاڵ مەدرید یاریەکەی لە بارشەلۆنە بردەوە بە ئنجامی ٢ بە ١\"\n}\n```\n\n**Example 6:**\n\n- **Input:** \"نرخی بتکۆین چەندە؟\"\n- **Output:** \n```json\n{\n  \"command\": \"WEB\",\n  \"message\": \"فۆتۆسینسێز پڕۆسەیەکە کە ڕووەکەکان بەکاریدەهێنن بۆ گۆڕینی تیشکی خۆر بۆ وزە.\"\n}\n```\n\n**Example 7:**\n\n- **Input:** \"پێناسەی فۆتۆسینسێز چییە؟\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"بتکۆین ئێستا بە ١٠١٢٣٠ دۆلار مامەڵەی پێوە دەکرێت.\"\n}\n```\n\n\n**Example 8:**\n\n- **Input:** \"ناوی پایتەختەکانی وڵاتانی سکەندەناڤیا چین؟\"\n- **Output:*پایتەختەکانی وڵاتانی سکەندەناڤیا: ستۆکهۆڵم (سوید)، ئۆسلۆ (نەرویج)، کۆپنهاگن (دانیمارک)، هێلسنکی (فینلەند)، ڕیکیاڤیک (ئایسلەند).* \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"\"\n}\n```\n\n\n**Example 9:**\n\n- **Input:** \"تایبەتمەندییەکانی ڕۆمانی کلاسیکی کوردی چین؟\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"ڕۆمانی کلاسیکی کوردی تایبەتمەندی گێڕانەوەی کەلتووری نەتەوەیی، کێشە کۆمەڵایەتییەکان، خەباتی نەتەوەیی، و وێنەکێشانی سروشتی کوردستانی هەیە.\"\n}\n```\n\n\n**Example 10:**\n\n- **Input:** \"هاوکێشەی ئاینشتاین E=mc² چی دەگەیەنێت؟\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"هاوکێشەی E=mc² ئەوە دەگەیەنێت کە وزە (E) یەکسانە بە بارستە (m) جار خێرایی ڕووناکی بە توانی دوو (c²)، واتە وزە و بارستە دەکرێت بگۆڕدرێن بۆ یەکتری.\"\n}\n```\n\n\n**Example 11:**\n\n- **Input:** \"تکایە ئەم ڕستەیە وەربگێڕە بۆ زمانی ئینگلیزی: کوردستان وڵاتێکی جوانە بە سروشتێکی دڵڕفێن.\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"وەرگێڕان: 'Kurdistan is a beautiful country with enchanting nature.'\"\n}\n```\n\n\n**Example 12:**\n\n- **Input:** \"ئەم پەیامە وەربگێڕە بۆ ئینگلیزی: من خوێندکارم و دەمەوێت زمانی ئینگلیزی فێربم بۆ ئەوەی بتوانم لە دەرەوەی وڵات درێژە بە خوێندن بدەم.\"\n- **Output:** \n```json\n{\n  \"command\": \"EDUCATION\",\n  \"message\": \"وەرگێڕان: 'I am a student and I want to learn English so that I can continue my studies abroad.'\"\n}\n```\n\n# Notes\n\n- Anticipate variations in phrasing or language for all application areas.\n- Use the EDUCATION command for language learning or translation and WEB for general web inquiries.\n- Maintain the input language in the output response where applicable.\n- Ensure that any response about specific information like weather or stock prices is direct and reflects the specific request.",
            messages=conversation_history
        )

        response = message.content[0].text
        command, kurdi_message = extract_values(response)

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

def listen_for_command():
    """
    Listens for audio input and validates its duration. If the audio is longer than 1.5 seconds,
    it saves the audio to a file and returns the file path.

    :return: Path to the saved audio file if valid audio is detected, otherwise None.
    """
    with sr.Microphone() as source:
        print("Listening for a valid sound...")
        recognizer.adjust_for_ambient_noise(source, duration=2)  # Adjust for ambient noise
        while True:  # Limit listening to 60 seconds
            try:
                # Use a timeout for the listen method to ensure it doesn't block indefinitely
                audio = recognizer.listen(source, phrase_time_limit=45, timeout=60)  # Timeout is in seconds

                # Validate the duration of the audio
                audio_duration = len(audio.get_wav_data()) / (16000 * 2)  # Assuming 16kHz sample rate and 16-bit audio
                if audio_duration >= 2.0:
                    print(f"Valid sound detected with duration: {audio_duration} seconds")
                    save_audio(audio, "uploads/recording.wav")
                    return "uploads/recording.wav"
                else:
                    print(f"Sound too short: {audio_duration:.2f} seconds. Ignoring...")
            except sr.WaitTimeoutError:
                print("No sound detected within the timeout period. Continuing...")
                break
            except Exception as e:
                print(f"Error processing audio: {e}")
        print("Listening timed out after 60 seconds.")
        return None
    
def withoutWakeWordProcess(history):
    while True:
        # Initialize timing dictionary
        method_times = {
            "listen_for_command": 0,
            "kurdish_resposnse_parsing": 0,
            "send_text_to_anthropic": 0,
            "control_led": 0,
            "generate_speech": 0
        }

        # Start measuring time for listen_for_command
        start_time = time.time()
        audio_file = listen_for_command()
        method_times["listen_for_command"] = time.time() - start_time

        if audio_file:
            # Measure time for kurdish_resposnse_parsing
            start_time = time.time()
            kurdish_response = kurdish_resposnse_parsing(audio_file)
            method_times["kurdish_resposnse_parsing"] = time.time() - start_time

            # Measure time for send_text_to_anthropic
            start_time = time.time()
            response = send_text_to_anthropic(api_key_claude, kurdish_response, history)
            method_times["send_text_to_anthropic"] = time.time() - start_time

            # Extract command and message
            command, message = extract_values(response)

            # Measure time for control_led
            start_time = time.time()
            control_led(command)
            method_times["control_led"] = time.time() - start_time

            # Measure time for generate_speech
            start_time = time.time()
            try:
                generate_speech(message=message)
            except Exception as e:
                print(f"Error: {e}")
            method_times["generate_speech"] = time.time() - start_time

            # Print timing results
            print("Method execution times:")
            for method, duration in method_times.items():
                print(f"{method}: {duration:.4f} seconds")

            # Identify the method that took the most time
            max_time_method = max(method_times, key=method_times.get)
            print(f"The method that took the most time: {max_time_method} ({method_times[max_time_method]:.4f} seconds)")

            last_instruction_time = time.time()
            break
        else:
            last_instruction_time = time.time() - 61

        # Reset timing dictionary for the next iteration
        method_times = {key: 0 for key in method_times}

    return last_instruction_time
    
def wakeWordProcess(history):
    while True:
        # Initialize timing dictionary
        method_times = {
            "listen_for_wake_word": 0,
            "kurdish_resposnse_parsing": 0,
            "send_text_to_anthropic": 0,
            "control_led": 0,
            "generate_speech": 0
        }

        # Start measuring time for listen_for_wake_word
        start_time = time.time()
        audio_file = listen_for_wake_word()
        method_times["listen_for_wake_word"] = time.time() - start_time

        if audio_file:
            # Measure time for kurdish_resposnse_parsing
            start_time = time.time()
            kurdish_response = kurdish_resposnse_parsing(audio_file)
            method_times["kurdish_resposnse_parsing"] = time.time() - start_time

            # Measure time for send_text_to_anthropic
            start_time = time.time()
            response = send_text_to_anthropic(api_key_claude, kurdish_response, history)
            method_times["send_text_to_anthropic"] = time.time() - start_time

            # Extract command and message
            command, message = extract_values(response)

            # Measure time for control_led
            start_time = time.time()
            control_led(command)
            method_times["control_led"] = time.time() - start_time

            # Measure time for generate_speech
            start_time = time.time()
            try:
                generate_speech(message=message)
            except Exception as e:
                print(f"Error: {e}")
            method_times["generate_speech"] = time.time() - start_time

            # Print timing results
            print("Method execution times:")
            for method, duration in method_times.items():
                print(f"{method}: {duration:.4f} seconds")

            last_instruction_time = time.time()
            break

    return last_instruction_time
            
if __name__ == "__main__":
    last_instruction_time = time.time()-61
    histroy = []
    # Run the program in a loop to keep listening for wake words and commands
    while True:  
        if (time.time() - last_instruction_time) < 60:
            last_instruction_time = withoutWakeWordProcess(history=histroy)
        else:
            histroy = []
            last_instruction_time = wakeWordProcess(history=histroy)

