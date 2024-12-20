import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from collections import deque
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS

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
    speaker: str  # Required
    topic: str    # Required
    message: str = ""  # Optional with default value

# Generate TTS
def generate_audio_response(text, speaker_name):
    """
    Generates a text-to-speech audio file using gTTS with persona-specific settings.
    """
    persona = personas.get(speaker_name)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{speaker_name}' not found.")
    lang = persona.get("voice_language", "en")  # Default to English
    try:
        file_path = f"audio_responses/{speaker_name}_response.mp3"
        tts = gTTS(text, lang=lang)
        tts.save(file_path)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

@app.get("/personas/")
async def get_personas():
    """
    Fetch predefined personas from the `persona.json` file.
    """
    return personas

@app.post("/moderator-topic/")
async def moderator_topic(data: Message):
    """
    Sets the debate topic based on the moderator's input.
    """
    global debate_topic, conversation_history
    if not data.topic:
        raise HTTPException(status_code=400, detail="No topic provided")
    debate_topic = data.topic
    conversation_history.append({"speaker": "Moderator", "message": f"Debate Topic: {debate_topic}"})
    return {"conversation_history": conversation_history}

@app.post("/submit-turn/")
async def submit_turn(data: Message):
    """
    Handles responses from participants during the debate.
    """
    global conversation_history
    if not data.speaker:
        raise HTTPException(status_code=400, detail="No speaker specified")
    
    # Simulate participant response
    persona = personas.get(data.speaker)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Speaker '{data.speaker}' not found.")
    
    system_prompt = persona["system_prompt"]
    response_text = f"{data.speaker} responds: {system_prompt} on the topic '{debate_topic}'"

    # Add response to conversation history
    conversation_history.append({"speaker": data.speaker, "message": response_text})

    # Generate audio response
    audio_file = generate_audio_response(response_text, data.speaker)
    return {"conversation_history": conversation_history, "audio_file": audio_file}

@app.post("/participant-response/")
async def participant_response():
    """
    Handles the sequential flow of participant responses.
    """
    global participants, conversation_history, debate_topic
    if not debate_topic:
        raise HTTPException(status_code=400, detail="No debate topic set")

    responses = []
    for _ in range(len(participants)):
        participant = participants[0]
        persona = personas.get(participant)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Speaker '{participant}' not found.")

        system_prompt = persona["system_prompt"]
        response_text = f"{participant} says: {system_prompt} on the topic '{debate_topic}'"

        # Add response to conversation history
        conversation_history.append({"speaker": participant, "message": response_text})

        # Generate audio response
        audio_file = generate_audio_response(response_text, participant)
        responses.append({"speaker": participant, "message": response_text, "audio_file": audio_file})
        participants.rotate(-1)  # Move to the next participant

    return {"responses": responses, "conversation_history": conversation_history}

@app.get("/history/")
async def get_history():
    """
    Returns the conversation history.
    """
    return {"conversation_history": conversation_history}

@app.get("/audio/{speaker_name}")
async def get_audio(speaker_name: str):
    """
    Returns the audio file for a specific speaker's response.
    """
    file_path = f"audio_responses/{speaker_name}_response.mp3"
    if os.path.exists(file_path):
        return {"audio_file": file_path}
    raise HTTPException(status_code=404, detail="Audio file not found")