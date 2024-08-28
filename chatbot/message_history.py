class MessageHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, message):
        """Adds a message to the history."""
        if message:
            self.messages.append({"sender": sender, "message": message})
        else:
            print(f"Attempted to add None message from {sender}.")

    def get_messages(self):
        """Returns the list of messages."""
        return self.messages

    def format_message_history(self):
        """Formats the message history for the OpenAI API."""
        formatted_messages = [
            {
                "role": "system",
                "content": """
                    You are an AI chatbot designed to create and populate Spotify playlists for users. 
                    Maintain a clear, conversational, brief tone.
                    If the user has a specific request, just do what they ask.
                    Whatever information they don't provide, exercise creative liberty and fill it in yourself.
                    For example, if they describe a playlist they want but don't give you a name, just name it yourself.
                    If they describe a playlist but don't tell you specific songs to add, add them yourself.
                    By default, add 20 songs at a time unless otherwise specified.
                    If the user does NOT have a specific request, have a conversation with the user about their taste.
                    Figure out what they like and don't like, both broadly and specifically.
                    When you feel like you have a good grasp on their taste, suggest a tailor-made playlist for them.
                """.strip()  # Adjust the system message as needed
            }
        ]
        for msg in self.messages:
            role = "user" if msg["sender"] == "User" else "assistant"
            formatted_messages.append({"role": role, "content": msg["message"]})
        return formatted_messages
