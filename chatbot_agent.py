import os
import json
from openai import OpenAI
from spotify_tools import (
    authenticate_spotify,
    create_playlist,
    add_tracks_to_playlist,
)
from config import OPENAI_API_KEY
from message_history import MessageHistory

class ChatbotAgent:
    def __init__(self):
        # Instantiate the OpenAI client with your API key
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.message_history = MessageHistory()
        self.sp = None  # Spotify client
        self.user_id = None  # Spotify user ID

        # Define the functions that the assistant can call
        self.functions = [
            {
                "name": "create_playlist",
                "description": "Creates a new Spotify playlist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "playlist_name": {"type": "string", "description": "Name of the playlist."},
                    },
                    "required": ["playlist_name"],
                },
            },
            {
                "name": "add_songs_to_playlist",
                "description": "Adds songs to a Spotify playlist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "playlist_id": {"type": "string", "description": "ID of the playlist."},
                        "songs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "track_name": {"type": "string"},
                                    "artist_name": {"type": "string"},
                                },
                                "required": ["track_name", "artist_name"],
                            },
                            "description": "List of songs to add.",
                        },
                    },
                    "required": ["playlist_id", "songs"],
                },
            },
        ]

    def authenticate_spotify(self):
        """Authenticates with Spotify and sets up the Spotify client and user ID."""
        self.sp = authenticate_spotify()
        self.user_id = self.sp.current_user()["id"]

    def process_user_message(self, formatted_message_history, temperature):
        """Processes the user's message and generates a response."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=formatted_message_history,
                functions=self.functions,
                function_call="auto",
                temperature=temperature,
            )

            assistant_message = response.choices[0].message

            # Check if the assistant wants to call a function
            if assistant_message.function_call:
                function_name = assistant_message.function_call.name
                arguments = json.loads(assistant_message.function_call.arguments)

                # Handle the function call
                function_response_content = self.handle_function_call(function_name, arguments)

                # Add the assistant's message and the function response to the message history
                self.message_history.add_message("Assistant", assistant_message.content or "")
                self.message_history.add_function_response(function_name, function_response_content)

                # Generate the final response
                final_response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.message_history.format_message_history(),
                    temperature=temperature,
                )

                final_message = final_response.choices[0].message.content
                self.message_history.add_message("Assistant", final_message)
                return final_message
            else:
                # If no function call, return the assistant's message
                self.message_history.add_message("Assistant", assistant_message.content)
                return assistant_message.content

        except Exception as e:
            print(f"Error processing user message: {e}")
            return "Sorry, I encountered an error while processing your request."

    def handle_function_call(self, function_name, arguments):
        """Executes the function call requested by the assistant."""
        if function_name == "create_playlist":
            playlist_name = arguments.get("playlist_name")
            playlist_id = create_playlist(self.sp, self.user_id, playlist_name)
            result = {"playlist_id": playlist_id}
            return json.dumps(result)
        elif function_name == "add_songs_to_playlist":
            playlist_id = arguments.get("playlist_id")
            songs = arguments.get("songs")
            added_tracks = add_tracks_to_playlist(self.sp, self.user_id, playlist_id, songs)
            result = {"added_tracks": added_tracks}
            return json.dumps(result)
        else:
            return json.dumps({"error": f"Function {function_name} not implemented."})
