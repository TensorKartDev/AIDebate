import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from collections import deque
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from fastapi.responses import FileResponse
from services.llm import speak

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
    topic: str = ""  # Optional for participant responses
    message: str = ""  # Optional with default value


# Generate TTS
from gtts import gTTS
from fastapi import HTTPException
import re

def generate_audio_response(text, speaker_name):
    """
    Generates a text-to-speech audio file using gTTS, ensuring consistent filename sanitization.
    """
    # Sanitize speaker name: Replace spaces or special characters with a single underscore
    sanitized_name = re.sub(r"[^a-zA-Z0-9]+", "_", speaker_name).strip("_")
    file_path = f"audio_responses/{sanitized_name}_response.mp3"
    
    print(f"Saving audio file at: {file_path}")  # Debugging log
    try:
        tts = gTTS(text=text, lang="en")  # Adjust language as needed
        tts.save(file_path)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")
    
@app.get("/personas/")
async def get_personas():
    """
    Fetch predefined personas from the `personas.json` file.
    """
    return personas


@app.post("/moderator-topic/")
async def moderator_topic(data: Message):
    """
    Sets the debate topic and prepares it for participant responses only.
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

    # Directly return the updated conversation history without invoking the speak function
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
    
    # Generate response text
    system_prompt = persona["system_prompt"]
    response_text = f"{data.speaker} responds: {system_prompt} on the topic '{debate_topic}'"

    # Append response to conversation history
    conversation_history.append({"speaker": data.speaker, "message": response_text})

    # Generate audio response
    audio_file = generate_audio_response(response_text, data.speaker)
    return {"conversation_history": conversation_history, "audio_file": audio_file}


@app.post("/participant-response/")
async def participant_response():
    """
    Generates responses from participants based on the current debate topic.
    Ensures only the latest audio files are stored for each participant.
    """
    global participants, debate_topic, conversation_history
    responses = []

    if not debate_topic:
        raise HTTPException(status_code=400, detail="Debate topic is not set.")

    for participant in participants:
        if participant == "Moderator":
            continue  # Skip the moderator

        persona = personas.get(participant)
        if not persona:
            continue

        # Construct the system prompt
        system_prompt = (
            f"{persona['system_prompt']} "
            f"On the topic '{debate_topic}', provide your perspective, please be short and add humour wherever possoble and applicable."
        )

        # User message to guide the participant's response
        user_message = (
            f"The topic is: '{debate_topic}'. "
            "Provide a concise and insightful response relevant to your expertise.please be short and add humour wherever possoble and applicable."
        )

        # Prepare the messages for the model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Generate response and overwrite the audio file
        try:
            response = speak(messages, persona["model_name"])
            generated_message = response.get("content", "")

            # Add to conversation history
            conversation_history.append({"speaker": persona["name"], "message": generated_message})

            # Generate and overwrite audio file
            audio_file = generate_audio_response(generated_message, persona["name"])
            responses.append({
                "speaker": persona["name"],
                "message": generated_message,
                "audio_file": audio_file  # Return the updated file path
            })

        except Exception as e:
            conversation_history.append({
                "speaker": "System",
                "message": f"Error generating response for {persona['name']}: {str(e)}"
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
    file_path = f"audio_responses/{speaker_name}_response.mp3"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Audio file not found")