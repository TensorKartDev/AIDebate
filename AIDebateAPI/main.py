import os
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import logging
import asyncio
from queue_manager import RabbitMQManager
from metadata import TagExtractor
from dotenv import load_dotenv
from services.llm import speak

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Track active WebSocket connections
client_connections = set()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://localhost:3000"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("pika").setLevel(logging.WARNING)  # Suppress Pika debug logs

# Initialize RabbitMQ manager and tag extractor
rabbitmq_manager = RabbitMQManager()
tag_extractor = TagExtractor()

# Load personas
persona_file_path = os.path.join(os.path.dirname(__file__), "personas.json")
if not os.path.exists(persona_file_path):
    raise FileNotFoundError("personas.json file not found.")
with open(persona_file_path, "r") as file:
    personas = json.load(file)

# Globals
conversation_history: List[Dict] = []
debate_topic: str = ""

# Request models
class ModeratorMessage(BaseModel):
    message: str

class Message(BaseModel):
    speaker: str
    topic: str = ""
    message: str = ""


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to handle client connections and relay messages.
    """
    await websocket.accept()
    client_connections.add(websocket)
    logging.info(f"Client connected. Total connections: {len(client_connections)}")

    try:
        while True:
            # Receive messages from the WebSocket client
            raw_message = await websocket.receive_text()
            message = json.loads(raw_message)

            logging.info(f"Message received from client: {message}")

            # Process tags and publish message to RabbitMQ
            metadata = tag_extractor.build_metadata(message["message"], method="keyword")
            tags = metadata["tags"]

            rabbitmq_manager.publish_message_to_exchange("discussion_exchange", json.dumps({
                "speaker": message["speaker"],
                "message": message["message"],
                "tags": tags
            }))
    except WebSocketDisconnect:
        logging.warning("WebSocket client disconnected.")
    except Exception as e:
        logging.error(f"Error in WebSocket connection: {e}")
    finally:
        client_connections.discard(websocket)
        logging.info(f"WebSocket connection closed. Remaining connections: {len(client_connections)}")


async def process_message(queue_name, message):
    """
    Processes RabbitMQ messages and sends relevant ones to WebSocket clients.
    """
    message_data = json.loads(message)
    speaker = message_data.get("speaker", "")
    content = message_data.get("message", "")
    tags = message_data.get("tags", [])

    logging.info(f"Message received in {queue_name}: {message}")

    if queue_name == "context_queue":
        logging.info("Processing the final queue: context_queue")
        for connection in list(client_connections):
            try:
                await connection.send_text(message)
                logging.info(f"Message sent to WebSocket client: {message}")
            except Exception as e:
                logging.error(f"Failed to send message to WebSocket client: {e}")
                client_connections.discard(connection)
        return

    # Determine the agent and process tags
    agent_name = queue_name.replace("_queue", "").replace("_", " ")
    persona = personas.get(agent_name)

    if persona:
        agent_tags = persona.get("relevant_tags", [])
        is_tag_match = any(tag.lower() in (t.lower() for t in agent_tags) for tag in tags)
        logging.info(f"{agent_name} relevant tags: {agent_tags}, Tag match: {is_tag_match}")

        if is_tag_match:
            # Get the last participant's response for context
            last_message = None
            if conversation_history and conversation_history[-1]["speaker"] != "Moderator":
                last_message = conversation_history[-1]["message"]

            system_prompt = (
                    f"Your role is to guide the conversation. Let's discuss: \"{content}\". "
                    f"Please ensure your tone is neutral."
                )

            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Let's explore the topic: '{content}'. "
                        f"Craft a very short response that is smart, witty, and infused with light humor. "
                        f"Relate to what was previously said if relevant."
                    ),
                },
            ]

            try:
                response = speak(messages, persona["model_name"])
                generated_message = response.get("content", "No response generated.")
                logging.info(f"{agent_name} response generated: {generated_message}")

                # Update conversation history
                conversation_history.append({"speaker": agent_name, "message": generated_message})

                rabbitmq_manager.publish_message_to_queue(
                    "context_queue",
                    json.dumps({"speaker": agent_name, "message": generated_message})
                )
            except Exception as e:
                logging.error(f"Error generating response for {agent_name}: {e}")
        else:
            logging.info(f"{agent_name} ignored the message. No relevant tags matched.")
    else:
        logging.warning(f"No persona found for {agent_name}. Ignoring the message.")


def _generate_and_publish_response(persona, system_prompt, user_message, agent_name):
    """
    Generates a response using LLM and publishes it to the context queue.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


    response = speak(messages, persona["model_name"])
    generated_message = response.get("content", "No response generated.")
    logging.info(f"{agent_name} response generated: {generated_message}")

    # Publish the generated message to the context queue
    rabbitmq_manager.publish_message_to_queue(
        "context_queue",
        json.dumps({"speaker": agent_name, "message": generated_message})
    )

@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event: Open RabbitMQ connection and set up queues.
    """
    rabbitmq_manager.setup_queues()
    rabbitmq_manager.connect_agents(rabbitmq_manager.agents, process_message)
    logging.info("RabbitMQ setup complete on startup.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    FastAPI shutdown event: Close RabbitMQ connection and channels.
    """
    rabbitmq_manager.close_all_connections()
    logging.info("RabbitMQ connection closed on shutdown.")


@app.get("/personas/")
async def get_personas():
    """
    Fetch predefined personas from the `personas.json` file.
    """
    return personas