import pika
import json
import os
import threading
import logging
from dotenv import load_dotenv
import asyncio
class RabbitMQManager:
    """
    RabbitMQ Manager for AI Fireside Chat with dynamic routing using persona-based tags.
    """

    def __init__(self, personas, host="localhost", exchange="fireside_exchange"):
        """
        Initialize RabbitMQManager with personas and connection settings.
        """
        load_dotenv()

        self.host = os.getenv("RABBITMQ_HOST", host)
        self.exchange_name = os.getenv("EXCHANGE_NAME", exchange)
        self.connection_params = pika.ConnectionParameters(
            host=self.host,
            heartbeat=60,
            blocked_connection_timeout=300
        )
        self.context_queue = "context_queue"

        # Load personas and tags
        self.personas = personas
        self.participants = list(self.personas.keys())
        self.candidate_tags = {
            persona: data.get("relevant_tags", []) for persona, data in self.personas.items()
        }
        self.connection = None
        self.channel = None

        logging.info(f"Loaded personas: {self.participants}")

    def ensure_channel_open(self):
        if not self.connection or self.connection.is_closed:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
            logging.info("Reopened RabbitMQ connection and channel.")

    def setup_exchange_and_queues(self):
        """
        Set up RabbitMQ direct exchange and bind queues with relevant tags.
        """
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()

        # Declare the exchange
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type="direct")

        # Create and bind participant queues with tags as binding keys
        for participant, tags in self.candidate_tags.items():
            queue_name = f"{participant.replace(' ', '_')}_queue"
            self.channel.queue_declare(queue=queue_name)
            for tag in tags:
                self.channel.queue_bind(exchange=self.exchange_name, queue=queue_name, routing_key=tag)
                logging.info(f"Bound queue {queue_name} to {self.exchange_name} with binding key '{tag}'.")

        # Create the context queue
        self.channel.queue_declare(queue=self.context_queue)
        self.channel.queue_bind(exchange=self.exchange_name, queue=self.context_queue, routing_key="context_queue")
        logging.info(f"Context queue {self.context_queue} created and bound with key 'context_queue'.")

    def publish_message(self, message, routing_key=""):
        """
        Publish a message to the exchange with an optional routing key.
        """
        self.ensure_channel_open()
        self.channel.basic_publish(exchange=self.exchange_name, routing_key=routing_key, body=json.dumps(message))
        logging.critical(f"Published message to exchange '{self.exchange_name}' with routing key '{routing_key}': {message}")

    def start_consuming(self, queue_name, callback_function):
        """
        Start consuming messages from the specified queue.
        """
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()

        async def async_callback_wrapper(queue_name, message):
            """
            Wrapper to run async callback function in the event loop.
            """
            await callback_function(queue_name, message)

        def wrapped_callback(ch, method, properties, body):
            """
            Wrap the provided callback function to adapt RabbitMQ's arguments.
            """
            try:
                message = body.decode()
                loop = asyncio.new_event_loop()  # Create a new event loop for the thread
                asyncio.set_event_loop(loop)  # Set the loop for this thread
                loop.run_until_complete(async_callback_wrapper(queue_name, message))
            except Exception as e:
                logging.error(f"Error in wrapped_callback for queue {queue_name}: {e}")
            finally:
                loop.close()  # Clean up the loop

        channel.basic_consume(queue=queue_name, on_message_callback=wrapped_callback, auto_ack=True)
        try:
            logging.info(f"Consuming messages from queue: {queue_name}")
            channel.start_consuming()
        except Exception as e:
            logging.error(f"Error consuming queue {queue_name}: {e}")
        finally:
            if channel.is_open:
                channel.close()
            if connection.is_open:
                connection.close()

    def connect_agents(self, callback_function):
        """
        Start consumers for all participant queues and the context queue.
        :param callback_function: Function to handle messages from the queues.
        """
        for participant in self.participants:
            queue_name = f"{participant.replace(' ', '_')}_queue"
            thread = threading.Thread(
                target=self.start_consuming, args=(queue_name, callback_function), daemon=True
            )
            thread.start()
            logging.info(f"Started consumer for {queue_name}")

        thread = threading.Thread(
            target=self.start_consuming, args=(self.context_queue, callback_function), daemon=True
        )
        thread.start()
        logging.info(f"Started consumer for {self.context_queue}")

    def close_all_connections(self):
        """
        Close all RabbitMQ connections.
        """
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
                logging.info("RabbitMQ channel closed.")
        except Exception as e:
            logging.error(f"Error closing channel: {e}")

        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logging.info("RabbitMQ connection closed.")
        except Exception as e:
            logging.error(f"Error closing connection: {e}")
