from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from collections import deque
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from services.persona import personas  # Assume personas are defined in services.persona
import requests
import json

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

# Request schema
class Message(BaseModel):
    speaker: str
    message: str
    topic: str = ""

@app.post("/submit-turn/")
async def submit_turn(message: Message):
    """
    Handles a single turn in the debate.
    """
    global conversation_history, debate_topic

    # Handle moderator setting the topic
    if message.topic:
        if debate_topic != message.topic:
            debate_topic = message.topic
            conversation_history.append({"speaker": "Moderator", "message": f"Debate Topic: {debate_topic}"})
        return {"conversation_history": conversation_history}

    # Handle model responses
    if message.speaker:
        persona = personas.get(message.speaker)
        if not persona:
            return {"error": f"Speaker {message.speaker} not found."}

        # Generate response from the model
        try:
            system_prompt = persona["system_prompt"]
            user_message = f"The topic is: {debate_topic}. Provide your response."
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
            print("calling speak from submit-turn")
            response = speak(messages, persona["model_name"])
            # Add response to conversation history
            conversation_history.append({"speaker": persona["name"], "message": response["content"]})
        except Exception as e:
            return {"error": f"Failed to generate response: {str(e)}"}

        return {"conversation_history": conversation_history[-1:]}  # Only return the latest message

    return {"error": "Invalid request"}

async def run_debate(topic: str):
    """
    Manages the debate flow and ensures sequential responses from participants.
    """
    global participants, conversation_history, stop_flag
    for _ in range(len(participants)):
        if stop_flag:
            break  # Stop if moderator interrupts

        current_speaker = participants[0]
        persona = personas.get(current_speaker)

        if not persona:
            conversation_history.append({"speaker": "System", "message": f"Speaker {current_speaker} not found."})
            participants.rotate(-1)
            continue

        # Prepare system and user messages

        system_prompt = persona["system_prompt"]
        
        user_message = f"The topic is: {topic}. Provide your response, stick to the tone and language, pay most attention to the last 5 conversations and respond accordingly"
       
        messages = [
            {
                "role": "system",
                "content": (
                   f"{system_prompt}"
                )
            },
            {
                "role": "user",
                "content": (
                    f"### Here is the conversation history:\n{conversation_history}\n\n {user_message}"
                    
                )
            }
        ]
        # Generate response using the persona's model
        try:
            print("calling speak from run_debate ",persona["model_name"] )
            response = speak(messages, persona["model_name"])
            conversation_history.append({"speaker": persona["name"], "message": response["content"]})
        except Exception as e:
            conversation_history.append({"speaker": "System", "message": f"Error generating response for {persona['name']}: {e}"})

        # Rotate to the next participant
        participants.rotate(-1)

def speak(messages, model):
    """
    Sends messages to the specified model and retrieves the response.
    """
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": model, "messages": messages, "stream": False}
        )
        r.raise_for_status()
        response = r.json()
        if "error" in response:
            raise Exception(response["error"])
        return response.get("message", {})
    except Exception as e:
        raise Exception(f"Error communicating with model {model}: {str(e)}")

@app.get("/history/")
async def get_history():
    """
    Returns the conversation history.
    """
    return {"conversation_history": conversation_history}

@app.get("/personas/")
async def get_personas():
    """
    Fetch personas from configuration.
    """
    with open("personas.json", "r") as file:
        personas = json.load(file)
    return personas