import speech_recognition as sr
# Example processing functions - customize these with your actual logic

def process_text(text: str) -> str:
    """Process text input and return response"""
    # Your custom processing logic here
    processed_text = f"You sent: {text}. This has been processed."
    return processed_text


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