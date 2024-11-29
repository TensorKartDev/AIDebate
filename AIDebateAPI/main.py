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
async def submit_turn(message: Message, background_tasks: BackgroundTasks):
    """
    Handles each turn in the debate.
    """
    global conversation_history, debate_topic, stop_flag

    # Moderator interrupts or stops the debate
    if message.message.lower() == "stop":
        stop_flag = True
        conversation_history.append({"speaker": "Moderator", "message": "Debate stopped by Moderator."})
        return {
            "conversation_history": conversation_history,
            "next_speaker": None,
            "persona": None
        }

    # Moderator sets the topic
    if message.topic:
        debate_topic = message.topic
        conversation_history.append({"speaker": "Moderator", "message": f"Debate Topic: {debate_topic}"})
        stop_flag = False  # Reset stop flag
        # Start the debate in the background
        background_tasks.add_task(run_debate, debate_topic)
        return {
            "conversation_history": conversation_history,
            "next_speaker": participants[0],
            "persona": personas.get(participants[0]),
        }

    return {"error": "Invalid request. Please provide a valid topic or command."}

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
                   "{system_prompt}"
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
            print("sending topic to ",persona["model_name"] )
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