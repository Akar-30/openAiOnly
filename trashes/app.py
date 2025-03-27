from openai import OpenAI
from dotenv import load_dotenv
import os
import base64

load_dotenv()
# Initialize client with API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY2'))


# Read the audio file and convert it to base64
with open("./assets/living_on_ar_2.mp3", "rb") as audio_file:
    audio_bytes = audio_file.read()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

# API call
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


# Print the response content
print(response.choices[0].message.content)