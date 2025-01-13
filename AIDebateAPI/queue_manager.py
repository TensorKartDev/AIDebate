import pika
import json
import os
import threading
import logging
from dotenv import load_dotenv
import asyncio

class RabbitMQManager:
    """
    Class to manage RabbitMQ setup, message publishing, and consumption.
    """

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.persona_file = os.getenv("PERSONA_FILE", "personas.json")
        self.exchange_name = os.getenv("EXCHANGE_NAME", "discussion_exchange")

        self.connection_params = pika.ConnectionParameters(
            host=self.host,
            heartbeat=60,  # Heartbeat to maintain connection
            blocked_connection_timeout=300  # Timeout for blocked connections
        )

        self.channels = []
        self.connections = []

        # Validate persona file
        if not os.path.exists(self.persona_file):
            raise FileNotFoundError(f"{self.persona_file} not found.")

        # Load personas
        with open(self.persona_file, "r") as f:
            self.personas = json.load(f)

        # Extract agent names
        self.agents = list(self.personas.keys())

    def _get_connection_and_channel(self):
        """
        Create and return a new RabbitMQ connection and channel.
        """
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        return connection, channel

    def open_connection(self):
        """
        Ensure a RabbitMQ connection is open.
        """
        if not hasattr(self, 'connection') or self.connection is None or self.connection.is_closed:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channels.append(self.connection.channel())
            print("RabbitMQ connection opened.")

    def close_all_connections(self):
        """
        Close all RabbitMQ channels and connections.
        """
        # Close all channels
        for channel in self.channels:
            try:
                channel.close()
                print("Channel closed.")
            except Exception as e:
                logging.error(f"Error closing channel: {e}")

        # Close all connections
        if hasattr(self, 'connection') and self.connection:
            try:
                self.connection.close()
                print("Main connection closed.")
            except Exception as e:
                logging.error(f"Error closing connection: {e}")

    def setup_queues(self):
        """
        Set up RabbitMQ exchange, individual agent queues, and the context queue.
        """
        connection, channel = self._get_connection_and_channel()

        # Declare the exchange
        channel.exchange_declare(exchange=self.exchange_name, exchange_type="fanout")

        # Declare individual queues for agents
        for agent in self.agents:
            agent_queue = f"{agent.replace(' ', '_')}_queue"
            try:
                channel.queue_declare(queue=agent_queue, passive=True)
                print(f"Queue already exists: {agent_queue}")
            except pika.exceptions.ChannelClosedByBroker:
                # If the queue doesn't exist, create and bind it
                connection, channel = self._get_connection_and_channel()
                channel.queue_declare(queue=agent_queue)
                channel.queue_bind(exchange=self.exchange_name, queue=agent_queue)
                print(f"Queue created and bound: {agent_queue}")

        # Declare the common context queue
        context_queue = "context_queue"
        try:
            channel.queue_declare(queue=context_queue, passive=True)
            print(f"Queue already exists: {context_queue}")
        except pika.exceptions.ChannelClosedByBroker:
            connection, channel = self._get_connection_and_channel()
            channel.queue_declare(queue=context_queue)
            channel.queue_bind(exchange=self.exchange_name, queue=context_queue)
            print(f"Queue created and bound: {context_queue}")

        print("RabbitMQ setup complete with individual and context queues.")
        connection.close()

    def publish_message_to_exchange(self, exchange, message):
        """
        Publish a message to the specified exchange.
        """
        connection, channel = self._get_connection_and_channel()
        try:
            channel.basic_publish(exchange=exchange, routing_key="", body=message)
            print(f"Published message to exchange {exchange}: {message}")
        finally:
            channel.close()
            connection.close()

    def publish_message_to_queue(self, queue_name, message):
        """
        Publish a message directly to a queue.
        """
        connection, channel = self._get_connection_and_channel()
        try:
            channel.basic_publish(exchange="", routing_key=queue_name, body=message)
            print(f"Published message to queue {queue_name}: {message}")
        finally:
            channel.close()
            connection.close()

    def purge_queues(self):
        """
        Purge all messages from individual agent queues and the context queue.
        """
        connection, channel = self._get_connection_and_channel()

        for agent in self.agents:
            agent_queue = f"{agent.replace(' ', '_')}_queue"
            try:
                channel.queue_purge(queue=agent_queue)
                print(f"Purged queue: {agent_queue}")
            except Exception as e:
                logging.error(f"Error purging queue {agent_queue}: {e}")

        context_queue = "context_queue"
        try:
            channel.queue_purge(queue=context_queue)
            print(f"Purged queue: {context_queue}")
        except Exception as e:
            logging.error(f"Error purging queue context_queue: {e}")

        connection.close()

    def delete_queues_and_exchange(self):
        """
        Delete all queues and the exchange.
        """
        connection, channel = self._get_connection_and_channel()

        for agent in self.agents:
            agent_queue = f"{agent.replace(' ', '_')}_queue"
            try:
                channel.queue_delete(queue=agent_queue)
                print(f"Deleted queue: {agent_queue}")
            except Exception as e:
                logging.error(f"Error deleting queue {agent_queue}: {e}")

        context_queue = "context_queue"
        try:
            channel.queue_delete(queue=context_queue)
            print(f"Deleted queue: {context_queue}")
        except Exception as e:
            logging.error(f"Error deleting queue context_queue: {e}")

        try:
            channel.exchange_delete(exchange=self.exchange_name)
            print(f"Deleted exchange: {self.exchange_name}")
        except Exception as e:
            logging.error(f"Error deleting exchange {self.exchange_name}: {e}")

        connection.close()

    def start_consuming(self, queue_name, callback_function):
        """
        Start consuming messages from a queue and process them using the callback function.
        Handles both synchronous and asynchronous callbacks.
        """
        connection, channel = self._get_connection_and_channel()
        self.channels.append(channel)

        def on_message(ch, method, properties, body):
            message = body.decode()
            print(f"Received message in {queue_name}: {message}")

            try:
                if asyncio.iscoroutinefunction(callback_function):
                    # Run the async callback in the event loop
                    asyncio.run(callback_function(queue_name, message))
                else:
                    # Call the sync callback directly
                    callback_function(queue_name, message)
            except Exception as e:
                logging.error(f"Error processing message from {queue_name}: {e}")

        channel.basic_consume(queue=queue_name, on_message_callback=on_message, auto_ack=True)
        print(f"Listening to queue: {queue_name}")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print("Stopping consumer.")
            channel.stop_consuming()
            connection.close()

    def connect_agents(self, agents, callback_function):
        """
        Connect agents to their respective queues and the context queue.
        """
        threads = []

        for agent in agents:
            agent_queue = f"{agent.replace(' ', '_')}_queue"
            thread = threading.Thread(
                target=self.start_consuming,
                args=(agent_queue, callback_function),
                name=f"{agent}_listener"
            )
            thread.start()
            threads.append(thread)
            print(f"Agent {agent} connected to queue {agent_queue}")

        # Context queue
        context_thread = threading.Thread(
            target=self.start_consuming,
            args=("context_queue", callback_function),
            name="context_queue_listener"
        )
        context_thread.start()
        threads.append(context_thread)
        print("Context queue listener started.")

        return threads