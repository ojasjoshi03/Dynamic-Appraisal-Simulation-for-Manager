import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import ast, json
import urllib.parse
# Import custom functions
from functions.database import get_recent_messages

# Retrive Environment Variables
load_dotenv()
 
SPEECH_MODEL = os.environ.get("AZURE_SPEECH_MODEL")
SPEECH_ENDPOINT = os.environ.get("AZURE_SPEECH_ENDPOINT")
SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
SPEECH_VERSION = os.environ.get("AZURE_SPEECH_VERSION")

GPT_MODEL = os.environ.get("AZURE_GPT_MODEL")
GPT_ENDPOINT = os.environ.get("AZURE_GPT_ENDPOINT")
GPT_KEY = os.environ.get("AZURE_GPT_KEY")
GPT_VERSION = os.environ.get("AZURE_GPT_VERSION")

# Initialize the Azure OpenAI client
speech_client = AzureOpenAI(
        azure_endpoint = SPEECH_ENDPOINT, 
        api_key=SPEECH_KEY,  
        api_version=SPEECH_VERSION
        )


chat_client = AzureOpenAI(
        azure_endpoint = GPT_ENDPOINT, 
        api_key=GPT_KEY,  
        api_version=GPT_VERSION
        )

# AzureOpenAI - Whisper
# Convert Audio to Text
def convert_audio(audio_file):
    try:
        transcript = speech_client.audio.transcriptions.create(model=SPEECH_MODEL, file=audio_file)
        message_text = transcript 
        return message_text
    except Exception as e:
        print(e)
        return 

# AzureOpenAI - GPT-3.5
# Send decoded text to LLM
def get_chat_response(message_input):
    try:
        response = chat_client.chat.completions.create(model=GPT_MODEL, messages=message_input)
        # print(response)
        message_text = response.choices[0].message.content
        print(message_text)
        return message_text
    except Exception as e:
        print(e)
        return