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


# Load personas
persona_file_path = os.path.join(os.path.dirname(__file__), "personas.json")
if not os.path.exists(persona_file_path):
    raise FileNotFoundError("personas.json file not found.")
with open(persona_file_path, "r") as file:
    personas = json.load(file)
rabbitmq_manager = RabbitMQManager(personas=personas)
tag_extractor = TagExtractor(personas=personas)
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

            # Check if the message has already been processed
            is_processed = "tags" in message and message["tags"]
            is_explained = message.get("isExplained", False)

            if not is_processed:
                # New message, typically from Moderator
                logging.info("New message detected, extracting tags.")
                tags = tag_extractor.extract_tags(message["message"], method="keyword")
                message["tags"] = tags
                message["isProcessed"] = True  # Mark the message as processed
                message["isExplained"] = False  # New messages are not explained yet

                # Publish the new message to the exchange
                rabbitmq_manager.publish_message(
                    {
                        "speaker": message["speaker"],
                        "message": message["message"],
                        "tags": tags,
                        "context": [],  # Empty context for new messages
                        "isExplained": False,  # Set explicitly for new messages
                        "previous_speaker": message.get("speaker", ""),
                    }
                )
            else:
                ## Processed response detected
                logging.info("Processed message detected. Forwarding to context_queue and discussion_exchange.")

            # Avoid duplicate speakers
            previous_speaker = message.get("previous_speaker", "")
            if message["speaker"] == previous_speaker:
                logging.info(f"Skipping duplicate response from {message['speaker']}.")
                return

            # Update previous speaker in the message
            message["previous_speaker"] = message["speaker"]

            # Publish to context_queue for WebSocket updates
            rabbitmq_manager.publish_message(
                {
                    "speaker": message["speaker"],
                    "message": message["message"],
                    "tags": message["tags"],
                    "context": message.get("context", []),
                    "isProcessed": True,
                    "isExplained": is_explained,
                },
                routing_key="context_queue"
            )

            # Publish back to discussion_exchange with routing keys for further routing
            # Publish processed response back to discussion_exchange with relevant tags
            if message["tags"]:
            # Extract all tag values from the dictionary (flattened list)
                all_tag_values = [tag for tags in message["tags"].values() for tag in tags]
                
                # Use unique tags as routing keys
                for tag_value in set(all_tag_values):  # Use set to avoid duplicate tag values
                    rabbitmq_manager.publish_message(
                        {
                            "speaker": message["speaker"],
                            "message": message["message"],
                            "tags": message["tags"],
                            "context": message.get("context", []),
                            "isProcessed": True,
                            "isExplained": message.get("isExplained", False),
                        },
                        routing_key=tag_value  # Use tag value as the routing key
                    )
            else:
                logging.warning("No tags found in the message. Skipping routing to discussion_exchange.")
                if not tags:
                    logging.warning("No tags found in the message. Sending to context_queue.")
                    rabbitmq_manager.publish_message(
                        {
                            "speaker": message["speaker"],
                            "message": message["message"],
                            "context": message.get("context", []),
                            "isProcessed": True,
                            "isExplained": False,
                        },
                        routing_key="context_queue"
                    )
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
    print("In process_message")
    message_data = json.loads(message)
    speaker = message_data.get("speaker", "")
    previous_speaker = message_data.get("previous_speaker", "")
    content = message_data.get("message", "")
    context = message_data.get("context", [])
    is_processed = message_data.get("isProcessed", False)

    logging.info(f"Message received in {queue_name}: {message}")

    # Process messages from context_queue
    if queue_name == "context_queue":
        logging.info("Processing the final queue: context_queue")
        for connection in list(client_connections):
            try:
                message_data["read_aloud"] = speaker != "Moderator"
                await connection.send_text(json.dumps(message_data))
                logging.info(f"Message sent to WebSocket client: {message_data}")
            except Exception as e:
                logging.error(f"Failed to send message to WebSocket client: {e}")
                client_connections.discard(connection)
        return

    # Skip processing if the message is already processed
    # if is_processed:
    #     logging.info("Message already processed. Skipping further processing.")
    #     return

    # Process messages from agent queues
    agent_name = queue_name.replace("_queue", "").replace("_", " ")

    # Skip processing if the agent is the previous speaker
    if agent_name == previous_speaker:
        logging.info(f"{agent_name} skipped processing its own response.")
        return

    persona = personas.get(agent_name)

    if not persona:
        logging.warning(f"No persona found for {agent_name}. Ignoring the message.")
        return

    # Generate response based on context and persona
    system_prompt = (
            f"Your name is {persona['name']}, and your role is {persona['description']}. "
            f"You respond to discussions with wit and insight."
        )

    last_message = context[-1]["message"] if context else ""

    user_prompt = (
        f"The Moderator has set the topic: '{content}'. "
        f"The last message in the discussion was: '{last_message}'. "
        f"Craft a strictly 2-line response that is smart, witty, and infused with light humor. "
        f"Keep it brief and engaging, avoiding repetition of the moderator's question or the prior context."
    )

    try:
        response = speak(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            persona["model_name"]
        )
        generated_message = response.get("content", "No response generated.")
        logging.info(f"{agent_name} response generated: {generated_message}")

        # Add the agent's response to the context
        updated_context = context + [{"speaker": agent_name, "message": generated_message}]

        # Publish response back to discussion_exchange without routing keys
        rabbitmq_manager.publish_message(
            {
                "speaker": agent_name,
                "message": generated_message,
                "context": updated_context,
                "previous_speaker": agent_name,  # Add the agent as the previous speaker
                "isProcessed": True
            }
        )

        # Publish response to context_queue for WebSocket updates
        rabbitmq_manager.publish_message(
            {
                "speaker": agent_name,
                "message": generated_message,
                "context": updated_context,
                "isProcessed": True
            },
            routing_key="context_queue"
        )
    except Exception as e:
        logging.error(f"Error generating response for {agent_name}: {e}")
def close_all_connections(self):
    """
    Close all RabbitMQ channels and connections.
    """
    try:
        if self.channel and not self.channel.is_closed:
            self.channel.close()
            print("Channel closed.")
    except Exception as e:
        logging.error(f"Error closing channel: {e}")

    try:
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("Connection closed.")
    except Exception as e:
        logging.error(f"Error closing connection: {e}")
@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event: Open RabbitMQ connection and set up queues.
    """
    rabbitmq_manager.setup_exchange_and_queues()
    rabbitmq_manager.connect_agents(process_message)  # Start consuming messages
    logging.info("RabbitMQ consumers registered on startup.")
    #rabbitmq_manager.connect_agents(process_message)
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