class MessageHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, message):
        """Adds a message to the history."""
        if message:
            role = "user" if sender == "User" else "assistant"
            self.messages.append({"role": role, "content": message})
        else:
            print(f"Attempted to add None message from {sender}.")

    def add_function_response(self, function_name, content):
        """Adds a function response to the history."""
        self.messages.append({
            "role": "function",
            "name": function_name,
            "content": content
        })

    def get_messages(self):
        """Returns the list of messages."""
        return self.messages

    def format_message_history(self):
        """Formats the message history for the OpenAI API."""
        formatted_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that can manage Spotify playlists using function calls.",
            }
        ]
        formatted_messages.extend(self.messages)
        return formatted_messages
