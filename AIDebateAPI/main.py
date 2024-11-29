from fastapi import FastAPI
from pydantic import BaseModel
from collections import deque
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from services import llm
from services.persona import personas
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
# Participants queue
participants = deque(["WizardLM2", "LLaMA3", "LLaMA2", "Mistral"])

# Conversation history and topic
conversation_history: List[Dict] = []
debate_topic: str = ""



# Request schema
class Message(BaseModel):
    speaker: str
    message: str
    topic: str = ""

@app.post("/submit-turn/")
async def submit_turn(message: Message):
    global conversation_history, debate_topic

    if message.topic:
        # Set the debate topic
        debate_topic = message.topic
        conversation_history.append({"speaker": "Moderator", "message": f"Debate Topic: {debate_topic}"})
    elif message.speaker:
        # Add the participant's response
        response = generate_ai_response(message.speaker, debate_topic)
        conversation_history.append({"speaker": message.speaker, "message": response})

    # Rotate participants
    participants.rotate(-1)
    next_speaker = participants[0]
    print(conversation_history)
    return {
        "conversation_history": conversation_history,
        "next_speaker": next_speaker,
        "persona": personas.get(next_speaker, {"name": next_speaker, "image": "", "description": "No description available."}),
    }

def generate_ai_response(speaker: str, topic: str) -> str:
    # Placeholder for actual AI logic
    llm.speak("wiza")
    return f"This is a response from {speaker} about the topic '{topic}'."