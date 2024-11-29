from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from collections import deque
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import time  # For simulating delays
from services.persona import personas
# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
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
stop_flag: bool = False

# Personas with additional details

# Request schema
class Message(BaseModel):
    speaker: str
    message: str
    topic: str = ""

@app.post("/submit-turn/")
async def submit_turn(message: Message, background_tasks: BackgroundTasks):
    """
    Handles each turn in the debate.
    """
    global conversation_history, debate_topic, stop_flag
    print(message,debate_topic)
    # Moderator interrupts or stops the debate
    if message.message.lower() == "stop":
        stop_flag = True
        conversation_history.append({"speaker": "Moderator", "message": "Debate stopped by Moderator."})
        return {
            "conversation_history": conversation_history,
            "next_speaker": None,
            "persona": None
        }

    # Moderator resumes or sets a new topic
    if message.topic:
        if stop_flag:
            # Reset stop flag if a new topic is set after stopping
            stop_flag = False
        debate_topic = message.topic
        conversation_history.append({"speaker": "Moderator", "message": f"Debate Topic: {debate_topic}"})
        
        # Start or restart the debate in the background
        background_tasks.add_task(run_debate, debate_topic)
        return {
            "conversation_history": conversation_history,
            "next_speaker": participants[0],
            "persona": personas.get(participants[0], {
                "name": participants[0],
                "image": "/images/default-avatar.png",
                "description": "No description available."
            }),
        }

    # Return an error if no valid action is provided
    return {"error": "Invalid request. Please provide a topic or a stop command."}

async def run_debate(topic: str):
    """
    Handles the debate sequence, ensuring each participant responds sequentially.
    """
    global participants, conversation_history, stop_flag

    for _ in range(len(participants)):
        if stop_flag:
            break  # Stop if moderator interrupts

        current_speaker = participants[0]
        persona = personas.get(current_speaker, {})
        response = generate_ai_response(persona, topic)

        # Add response to the conversation history
        conversation_history.append({"speaker": persona.get("name", current_speaker), "message": response})

        # Rotate participants
        participants.rotate(-1)

        # Simulate a delay to represent processing time
        time.sleep(2)

def generate_ai_response(persona: Dict, topic: str) -> str:
    """
    Simulate generating an AI response based on the persona's system prompt and style.
    Replace this with actual interaction with an AI model (e.g., OpenAI API).
    """
    print(persona,topic)
    system_prompt = persona.get("system_prompt", "Speak in a neutral tone.")
    style = persona.get("style", "")
    name = persona.get("name", "Unknown Speaker")
    return f"{name} responds in style: '{style}' about the topic: '{topic}'."