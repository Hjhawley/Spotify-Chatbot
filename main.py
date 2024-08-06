import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from dotenv import load_dotenv
import os
import json
import threading
from openai import OpenAI
from spotify_interface import authenticate_spotify, create_playlist, add_tracks_to_playlist

# Load OpenAI and Spotify API keys from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

sp = authenticate_spotify()
user_id = sp.current_user()['id']

class MessageHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, message):
        if message:
            self.messages.append({"sender": sender, "message": message})
        else:
            print(f"Attempted to add None message from {sender}.")

    def get_messages(self):
        return self.messages

    def format_message_history(self):
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
                """.strip()
            }
        ]
        for msg in self.messages:
            role = "user" if msg["sender"] == "User" else "assistant"
            formatted_messages.append({"role": role, "content": msg["message"]})
        return formatted_messages

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot")

        self.history = MessageHistory()

        self.history_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.history_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X, expand=True)

        self.user_input = tk.Entry(self.input_frame, width=80)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        self.temperature_frame = tk.Frame(self.root)
        self.temperature_frame.pack(pady=5, fill=tk.X)

        self.temperature_label = tk.Label(self.temperature_frame, text="Temperature")
        self.temperature_label.pack(side=tk.LEFT)

        self.temperature_slider = ttk.Scale(self.temperature_frame, from_=0, to=2, orient='horizontal', value=0.7)
        self.temperature_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.temperature_slider.bind("<Motion>", self.update_temperature_label)

        self.temperature_value_label = tk.Label(self.temperature_frame, text=f"{self.temperature_slider.get():.1f}")
        self.temperature_value_label.pack(side=tk.RIGHT)

        self.root.after(10, self.spotify_auth_message)

    def spotify_auth_message(self):
        try:
            self.sp = authenticate_spotify()
            self.user = self.sp.current_user()
            sp_message = f"Successfully authenticated user {self.user['display_name']}"
            self.display_message("Spotify", sp_message)
            self.history.add_message("Spotify", sp_message)
        except Exception as e:
            sp_message = f"Error during Spotify authentication: {str(e)}"
            self.display_message("Spotify", sp_message)
            self.history.add_message("Spotify", sp_message)

    def display_message(self, sender, message):
        if message:
            self.history_display.config(state='normal')
            self.history_display.insert(tk.END, f"{sender}: {message}\n")
            self.history_display.config(state='disabled')
            self.history_display.yview(tk.END)
        else:
            print(f"Attempted to display None message from {sender}.")

    def send_message(self, event=None):
        user_message = self.user_input.get()
        if user_message.strip():
            self.display_message("User", user_message)
            self.history.add_message("User", user_message)
            self.user_input.delete(0, tk.END)
            threading.Thread(target=self.get_response).start()

    def get_response(self):
        temperature = self.temperature_slider.get()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_playlist",
                    "description": "Create an empty playlist with an appropriate name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "playlist_name": {
                                "type": "string",
                                "description": "The name of the playlist",
                            }
                        },
                        "required": ["playlist_name"],
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_tracks_to_playlist",
                    "description": "Add multiple tracks to a specified playlist.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "playlist_id": {
                                "type": "string",
                                "description": "The ID of the playlist.",
                            },
                            "songs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "artist_and_song": {
                                            "type": "string",
                                            "description": "A song, formatted as {artist} - {song}",
                                        }
                                    },
                                    "required": ["artist_and_song"]
                                },
                                "description": "A list of songs to add to the playlist"
                            }
                        },
                        "required": ["playlist_id", "songs"],
                    },
                }
            }
        ]
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.history.format_message_history(),
                temperature=temperature,
                tools=tools,
                tool_choice="auto"
            )
            bot_message = response.choices[0].message
            tool_calls = bot_message.tool_calls
            if tool_calls:
                print(f"Calling a tool: {tool_calls[0]}")
                self.history.add_message("assistant", bot_message.content)
                available_functions = {
                    "create_playlist": self.handle_create_playlist,
                    "add_tracks_to_playlist": self.handle_add_tracks_to_playlist
                }
                for tool_call in tool_calls:
                    print(f"Tool call: {tool_call}")
                    function_name = tool_call.function.name
                    print(f"Function Name: {function_name}")
                    function_to_call = available_functions[function_name]
                    args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(**args)
                    self.history.add_message("tool", function_response)
                    if function_name == "create_playlist":
                        self.display_message("Chatbot", f"Playlist '{args['playlist_name']}' created successfully.")
                    elif function_name == "add_tracks_to_playlist":
                        self.display_message("Chatbot", f"Tracks added to playlist '{args['playlist_id']}' successfully.")
                second_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=self.history.format_message_history(),
                )
                second_bot_message = second_response.choices[0].message
                if second_bot_message.content:
                    self.display_message("Chatbot", second_bot_message.content)
                    self.history.add_message("Chatbot", second_bot_message.content)
                else:
                    error_message = "Received empty response from Chatbot."
                    self.display_message("Chatbot", error_message)
                    self.history.add_message("Chatbot", error_message)
            else:
                self.display_message("Chatbot", bot_message.content)
                self.history.add_message("Chatbot", bot_message.content)

        except Exception as e:
            bot_message = f"Error: {str(e)}"
            self.display_message("Chatbot", bot_message)
            self.history.add_message("Chatbot", bot_message)

    def handle_create_playlist(self, playlist_name):
        playlist_id = create_playlist(sp, user_id, playlist_name)
        return {"playlist_id": playlist_id, "message": f"Playlist '{playlist_name}' created successfully."}

    def handle_add_tracks_to_playlist(self, playlist_id, songs):
        try:
            track_list = []
            for song in songs:
                artist, track = song['artist_and_song'].split(' - ')
                track_list.append({"track_name": track.strip(), "artist_name": artist.strip()})
            track_uris = add_tracks_to_playlist(sp, user_id, playlist_id, track_list)
            return {"playlist_id": playlist_id, "message": f"Tracks added to playlist '{playlist_id}': {track_uris}."}
        except Exception as e:
            return {"playlist_id": playlist_id, "message": f"Error adding tracks to playlist: {str(e)}"}

    def update_temperature_label(self, event=None):
        self.temperature_value_label.config(text=f"{self.temperature_slider.get():.1f}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()
