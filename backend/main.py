# uvicorn main:app
# uvicorn main:app --reload

# Main Imports
from fastapi import Body, FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import urllib.parse
import os
import json
import tempfile
from pydub import AudioSegment
from typing import List, Optional
from ast import literal_eval

# Custom Function Imports
from functions.database import store_messages, reset_messages, get_system_prompt
from functions.openai_requests import convert_audio, get_chat_response
from functions.text_to_speech import convert_text_to_speech_here

# Initiate App
app = FastAPI()

class Prompt(BaseModel):
    behaviour: str
    rating: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# CORS - Origins
origins = [
    "https://localhost:5173",
    "https://localhost:5174",
    "https://localhost:4173",
    "https://localhost:4174",
    "https://localhost:3000",
]

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check health
@app.get("/health")
async def check_health():
    return {"message": "healthy"}

# Reset Messages
@app.get("/reset")
async def reset_conversation():
    reset_messages()
    return {"message": "Conversation reset"}

# Get system-prompt
@app.post("/set-prompt/")
async def set_prompt(prompt: Prompt):

    try:
        prompt_data = {"behaviour": prompt.behaviour, "rating": prompt.rating}
        with open("current_prompt.json", "w") as f:
            json.dump(prompt_data, f)
        return {"status": f"Prompt set successfully" , "behaviour": prompt.behaviour, "rating": prompt.rating }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.post("/convert-audio-to-text")
async def convert_audio_to_text(file: UploadFile = File(...)):

    # Save uploaded audio file
    temp_input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_input_file.write(file.file.read())
    temp_input_file.close()
    
    # Load audio file
    audio = AudioSegment.from_wav(temp_input_file.name)
    
    # Export AudioSegment to a file-like object
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio.export(temp_audio_file.name, format="wav")

    # Convert audio file to text
    with open(temp_audio_file.name, "rb") as audio_file:
        message_decoded = convert_audio(audio_file)

    # Guard : Ensure message decoded  
    if not message_decoded:
        return HTTPException(status_code=400, detail=" Failed to decode Audio")

    message_decoded = message_decoded.to_dict().get("text")
    
    return  {"text": message_decoded}


@app.post("/text-conversation")
async def text_conversation(chat_request: ChatRequest):
    
    messages = chat_request.messages
    decoded_text = [msg.dict() for msg in messages]
    # # Get chatgpt response using the provided text
    chat_response = get_chat_response(decoded_text)
    
    # Guard : Ensure chat response  
    if not chat_response:
        return HTTPException(status_code=400, detail=" Failed to get chat response")

    # Store Messages
    # store_messages(decoded_text, chat_response)
    
    return {"response": chat_response}


@app.post("/convert-text-to-speech")
async def convert_text_to_speech(text: str = Body(...)):

    # import pdb;pdb.set_trace()
    # print(text)
    decoded_text = urllib.parse.unquote_plus(text[5:])
    # print(decoded_text)
    # Convert text to audio using the provided text
    audio_output = convert_text_to_speech_here(decoded_text)

    return True