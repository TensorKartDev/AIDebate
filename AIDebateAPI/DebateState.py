class DebateState:
    def __init__(self):
        self.current_topic = None
        self.is_explained = False
        self.context = []

    def set_topic(self, topic):
        """
        Set a new topic and reset state.
        """
        self.current_topic = topic
        self.is_explained = False
        self.context = [topic]
        print(f"New topic set: {topic}")

    def add_context(self, message):
        """
        Add a message to the context.
        """
        self.context.append(message)

    def mark_as_explained(self):
        """
        Mark the current topic as explained.
        """
        self.is_explained = True
        print(f"Topic '{self.current_topic['message']}' marked as explained.")