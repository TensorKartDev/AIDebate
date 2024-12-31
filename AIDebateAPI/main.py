import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from collections import deque
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from fastapi.responses import FileResponse
import logging
import re
from services.llm import speak
import pyttsx3
# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load personas
persona_file_path = os.path.join(os.path.dirname(__file__), "personas.json")
if not os.path.exists(persona_file_path):
    raise FileNotFoundError("personas.json file not found.")
with open(persona_file_path, "r") as file:
    personas = json.load(file)

# Globals
participants = deque(personas.keys())
conversation_history: List[Dict] = []
debate_topic: str = ""

# Ensure directories exist
os.makedirs("audio_responses", exist_ok=True)

# Request schema
class Message(BaseModel):
    speaker: str
    topic: str = ""
    message: str = ""

# def generate_audio_response(text, speaker_name):
#     """
#     Generate an audio file from text using pyttsx3 with persona-based voice properties.
#     """
#     try:
#         # Fetch persona details
#         persona = personas.get(speaker_name)
#         if not persona:
#             raise ValueError(f"Persona '{speaker_name}' not found.")

#         # Extract voice properties
#         voice_language = persona.get("voice_language", "en")
#         voice_gender = persona.get("voice_gender", "male")

#         # Initialize pyttsx3 engine
#         engine = pyttsx3.init()

#         # Set voice properties
#         voices = engine.getProperty('voices')
#         selected_voice = None
#         for voice in voices:
#             if voice_language in voice.languages and voice_gender in voice.name.lower():
#                 selected_voice = voice.id
#                 break

#         if selected_voice:
#             engine.setProperty('voice', selected_voice)
#         else:
#             print(f"No matching voice found for language '{voice_language}' and gender '{voice_gender}'. Using default voice.")

#         # Set additional properties
#         engine.setProperty('rate', 150)  # Adjust speed if needed
#         engine.setProperty('volume', 0.9)  # Adjust volume if needed

#         # Save the audio file
#         sanitized_name = speaker_name.replace(" ", "_")
#         file_path = f"audio_responses/{sanitized_name}_response.mp3"
#         os.makedirs("audio_responses", exist_ok=True)
#         engine.save_to_file(text, file_path)
#         engine.runAndWait()

#         print(f"Audio file generated at {file_path}")
#         return file_path
#     except Exception as e:
#         raise Exception(f"Error generating audio with pyttsx3: {str(e)}")

# def generate_audio_response(text, speaker_name):
#     """
#     Generates a text-to-speech audio file using gTTS, ensuring consistent filename sanitization.
#     """
#     sanitized_name = re.sub(r"[^a-zA-Z0-9]+", "_", speaker_name).strip("_")
#     file_path = f"audio_responses/{sanitized_name}_response.mp3"
    
#     logging.debug(f"Saving audio file at: {file_path}")
#     try:
#         print("generating audio response of ", text)
#         tts = gTTS(text=text, lang="en")
#         tts.save(file_path)
#         return file_path, ipd.Audio(file_path)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")


@app.get("/personas/")
async def get_personas():
    """
    Fetch predefined personas from the `personas.json` file.
    """
    return personas


@app.post("/moderator-topic/")
async def moderator_topic(data: Message):
    """
    Sets the debate topic and prepares it for participant responses.
    """
    global debate_topic, conversation_history

    if not data.topic:
        raise HTTPException(status_code=400, detail="No topic provided")

    # Update the debate topic and conversation history
    debate_topic = data.topic
    conversation_history.append({
        "speaker": "Moderator",
        "message": f"Debate Topic: {debate_topic}"
    })

    return {"conversation_history": conversation_history}


@app.post("/submit-turn/")
async def submit_turn(data: Message):
    """
    Handles responses from participants during the debate.
    """
    global conversation_history
    if not data.speaker:
        raise HTTPException(status_code=400, detail="No speaker specified")

    persona = personas.get(data.speaker)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Speaker '{data.speaker}' not found.")

    system_prompt = persona["system_prompt"]
    response_text = f"{data.speaker} responds: {system_prompt} on the topic '{debate_topic}'"
    conversation_history.append({"speaker": data.speaker, "message": response_text})

    audio_file = generate_audio_response(response_text, data.speaker)
    return {"conversation_history": conversation_history, "audio_file": audio_file}


@app.post("/participant-response/{participant_name}")
async def participant_response(participant_name: str):
    """
    Generates a response for a specific participant based on the current debate topic.
    This is called for each participant one by one.
    """
    global debate_topic, conversation_history
    responses = []

    if not debate_topic:
        raise HTTPException(status_code=400, detail="Debate topic is not set.")

    persona = personas.get(participant_name)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Participant '{participant_name}' not found.")

    system_prompt = f"{persona['system_prompt']} On the topic '{debate_topic}', provide your perspective."
    user_message = f"The topic is: '{debate_topic}'. Provide a concise, short and insightful response."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        response = speak(messages, persona["model_name"])
        generated_message = response.get("content", "")
        conversation_history.append({"speaker": participant_name, "message": generated_message})
        responses.append({
            "speaker": participant_name,
            "message": generated_message,
        })

    except Exception as e:
        conversation_history.append({
            "speaker": "System",
            "message": f"Error generating response for {participant_name}: {str(e)}"
        })

    return {"conversation_history": conversation_history, "responses": responses}


@app.get("/history/")
async def get_history():
    """
    Returns the conversation history.
    """
    return {"conversation_history": conversation_history}


@app.get("/audio/{speaker_name}")
async def get_audio(speaker_name: str):
    print(speaker_name)
    #sanitized_name = re.sub(r"[^a-zA-Z0-9]+", "_", speaker_name).strip("_")
    file_path = f"audio_responses/{speaker_name}_response.mp3"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Audio file not found")