import re
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
api_key_claude = os.getenv("CLAUDE_API")

def send_text_to_anthropic(api_key_claude, kurdish_text):
    client = anthropic.Anthropic(api_key=api_key_claude)
    
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=5000,
        temperature=1,
        system="Convert any input regarding smart home controls into a predefined command from the specified list and support multiple languages.\n\nIdentify and match each user's request to the appropriate command for controlling lights within various rooms of the home. If the instruction is unclear, not achievable, or if it isn't a smart home command, use the respective commands for those situations.\n\n# Steps\n\n1. Analyze the input text to identify the room and action (ON/OFF) intended by the user, regardless of the input language.\n2. Match the determined room and action with one of the specified commands.\n3. If the input does not clearly indicate a specific room, use LIGHTS_ON or LIGHTS_OFF for general commands.\n4. If the instruction is unclear, use the command UNCLEAR_INSTRUCTION.\n5. If the requested action is not possible, use the command NOT_ABLE_TO_DO.\n6. If the input is not related to smart home instructions, indicate this in the output.\n\n# Output Format\n\nReturn the output in a JSON-like structured format. Include two responses:\n- A command string selected from the specified command list.\n- A concise text that reflects the demand in the same language as the input, suitable for fast and small talk AI. For non-smart home instructions, directly answer the question when possible.\n\nIf the input isn't related to smart home instructions, the output should be:\n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"[Concise answer in the input language or direct answer]\"\n}\n```\n\n# Examples\n\n**Example 1:**\n\n- **Input:** \"Turn off the lights in the living room.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIVING_ROOM_LIGHTS_OFF\",\n  \"message\": \"Turning off living room lights.\"\n}\n```\n\n**Example 2:**\n\n- **Input:** \"Ich möchte das Licht in der Küche einschalten.\"\n- **Output:** \n```json\n{\n  \"command\": \"KITCHEN_LIGHTS_ON\",\n  \"message\": \"Licht in der Küche einschalten.\"\n}\n```\n\n**Example 3:**\n\n- **Input:** \"Quiero encender las luces en todas partes.\"\n- **Output:** \n```json\n{\n  \"command\": \"LIGHTS_ON\",\n  \"message\": \"Enciende todas las luces.\"\n}\n```\n\n**Example 4:**\n\n- **Input:** \"Can you set the mood lighting?\"\n- **Output:** \n```json\n{\n  \"command\": \"UNCLEAR_INSTRUCTION\",\n  \"message\": \"Instruction unclear.\"\n}\n```\n\n**Example 5:**\n\n- **Input:** \"What's the weather like today?\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Checking the weather.\"\n}\n```\n\n**Example 6:**\n\n- **Input:** \"What is the area of the Kurdistan Region\"\n- **Output:** \n```json\n{\n  \"command\": \"NOT_SMART_HOME_INSTRUCTION\",\n  \"message\": \"Kurdistan Region covers about 40,643 square kilometers.\"\n}\n```\n\n# Notes\n\n- Consider synonyms or variations of \"turn on\" and \"turn off\" to determine the correct command.\n- Anticipate variations in phrasing or language that may affect room identification.\n- If no room is specified, assume the instruction refers to all lights.\n- If conditions or systems limit the ability to perform an action, opt for the NOT_ABLE_TO_DO response.\n- Ensure input language is detected and maintained in the output message.",
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

try:
    kurdish_text = "چالاککردنی ڕووناکی خانوویەکەت "
    response = send_text_to_anthropic(api_key_claude, kurdish_text)
    response_text = response.text  # Extract the text attribute from the TextBlock object
    command, message = extract_values(response_text)
    print(f"response: {response_text}")
    print(f"message: {message}")
    print(f"Command: {command}")
except Exception as e:
    print(f"response: {response}")
    print(f"Error: {e}")
    
