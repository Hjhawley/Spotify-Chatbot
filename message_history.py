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
        formatted_messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that can manage Spotify playlists using function calls. "
                    "When you call a function, you will receive the result, which you should use to decide "
                    "the next steps. Do not repeatedly call the same function unless necessary. "
                    "After creating a playlist, proceed to add songs to it if required. "
                    "Do not mention technical details like 'playlist_id' to the user; focus on providing a helpful response."
                ),
            }
        ]
        formatted_messages.extend(self.messages)
        return formatted_messages
