import os
import json
import azure.cognitiveservices.speech as speechsdk

from dotenv import load_dotenv

load_dotenv()

SPEECH_KEY = os.environ.get("TEXT_TO_SPEECH_KEY")
SPEECH_REGION = os.environ.get("TEXT_TO_SPEECH_REGION")
 
# Convert text to speech
def convert_text_to_speech_here(message):
    try:
        with open("current_prompt.json", "r") as f:
            current_prompt = json.load(f)
        behaviour = current_prompt.get("behaviour", "Humble")
        rating = current_prompt.get("rating", "High")
    except FileNotFoundError:
        behaviour = "Humble"
        rating = "High"

    file_name = f"employee_type_data/{behaviour}_{rating}.json"
    
    try:
        with open(file_name, "r") as file:
            employee_data = json.load(file)
    except FileNotFoundError:
        employee_data = {
            "voice" : "en-US-GuyNeural"
        }
    print(employee_data.get("voice"))
    
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_config.speech_synthesis_voice_name=employee_data.get("voice")
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesis_result = speech_synthesizer.speak_text_async(message).get()
    