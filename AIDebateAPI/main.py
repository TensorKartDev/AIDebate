import os
import json
import re
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
import logging_config
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

def remove_emoticons(text):
    # Define a regex pattern to match emojis and emoticons
    emoji_pattern = re.compile(
        "[\U00010000-\U0010FFFF]",  # Match any Unicode emoji character
        flags=re.UNICODE
    )
    # Replace emojis with an empty string
    return emoji_pattern.sub(r'', text)

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

            logging.debug(f"Message received from client: {message}")

            # Check if the message has already been processed
            is_processed = "tags" in message and message["tags"]
            logging.info(f"is_processed: {is_processed}")

            if not is_processed:
                # New message, typically from Moderator
                logging.info("New Moderator message detected, extracting tags.")
                tags = tag_extractor.extract_tags(message["message"], method="keyword")
                message["tags"] = tags
                message["isProcessed"] = True  # Mark the message as processed

                # Publish the message with all relevant routing keys
                all_tag_values = {tag for tags_list in tags.values() for tag in tags_list}
                for tag_value in all_tag_values:
                    rabbitmq_manager.publish_message(
                        {
                            "speaker": message["speaker"],
                            "message": message["message"],
                            "tags": tags,
                            "context": message.get("context", []),
                            "isProcessed": True,
                        },
                        routing_key=tag_value
                    )
            else:
                logging.info("Processed message detected. Routing to context_queue.")

            # Avoid duplicate speakers
            current_speaker = message["speaker"]
            previous_speaker = message.get("previous_speaker", "")
            logging.info("--------------- In Websocket ------------------")
            logging.warning(f"- Current speaker: {current_speaker}")
            logging.warning(f"- Previous speaker: {previous_speaker}")
            logging.warning(f"- Tags: {message.get('tags', {})}")
            logging.info("------------------END debug------------------")

            if previous_speaker == current_speaker:
                logging.warning(f"Skipping duplicate response from {current_speaker}.")
                continue

            # Update previous speaker in the message
            message["previous_speaker"] = current_speaker

            # Publish to context_queue for WebSocket updates
            rabbitmq_manager.publish_message(
                {
                    "speaker": message["speaker"],
                    "message": message["message"],
                    "tags": message.get("tags", {}),
                    "context": message.get("context", []),
                    "previous_speaker": message["previous_speaker"],
                    "isProcessed": True,
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
   
    message_data = json.loads(message)
    speaker = message_data.get("speaker", "")
    previous_speaker = message_data.get("previous_speaker", "")
    content = message_data.get("message", "")
    context = message_data.get("context", [])
    previous_speaker = message_data.get("previous_speaker", "Not set")
    logging.info(f"***************** In Process_message *****************")
    logging.warning(f"- Message received in {queue_name}")
    logging.warning(f"- Current speaker  {speaker}")
    logging.warning(f"- Previous speaker  {previous_speaker}")
    logging.warning(f"- Message  {message_data}")
    logging.info(f"***********END debug***********")
    # Process messages from context_queue
    if queue_name == "context_queue":
        logging.info("Processing the final queue: context_queue")
        for connection in list(client_connections):
            try:
                message_data["read_aloud"] = speaker != "Moderator"
                await connection.send_text(json.dumps(message_data))
                logging.critical(f"Message sent to WebSocket client: {message_data}")
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
    name = persona['name']
    last_message = context[-1]["message"] if context else ""
    
    user_prompt = (
        f"Remember your name is {name}, never include your own name in response."
        f"The Moderator has set the topic: '{content}'. "
        f"The last message in the discussion was: '{last_message}'. "
        f"DO NOT ADD ANY EMOTICONS, IMAGES OR EMOTITIONAL ICONS "
        f"Craft a strictly 2-line response that is smart, witty, and infused with light humor. "
        f"Keep it brief and engaging,avoiding repetition of the moderator's question or the prior context."
    )

    try:
        response = speak(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            persona["model_name"]
        )
        generated_message = response.get("content", "No response generated.")
        generated_message = remove_emoticons(generated_message)
        logging.info(f"{agent_name} response generated: {generated_message}")

        # Add the agent's response to the context
        updated_context = context + [{"speaker": agent_name, "message": generated_message}]

        # Publish response back to discussion_exchange without routing keys
        # rabbitmq_manager.publish_message(
        #     {
        #         "speaker": agent_name,
        #         "message": generated_message,
        #         "context": updated_context,
        #         "previous_speaker": agent_name,  # Add the agent as the previous speaker
        #         "isProcessed": True
        #     }
        # )

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