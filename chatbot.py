import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from dotenv import load_dotenv
import os
from openai import OpenAI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading

# Load OpenAI and Spotify API keys from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class MessageHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, message):
        self.messages.append({"sender": sender, "message": message})

    def get_messages(self):
        return self.messages

    def format_message_history(self):
        formatted_messages = [{"role": "system", "content": "You are an AI chatbot. You are friendly and conversational."}]
        for msg in self.messages:
            role = "user" if msg["sender"] == "User" else "assistant"
            formatted_messages.append({"role": role, "content": msg["message"]})
        return formatted_messages

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot")

        self.history = MessageHistory()

        self.sp = self.authenticate_spotify()

        self.chat_history = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

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

    def authenticate_spotify(self) -> spotipy.Spotify:
        scope = os.getenv("SPOTIPY_SCOPE")
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

        if not all([scope, client_id, client_secret, redirect_uri]):
            raise ValueError("Spotify API credentials are missing in .env file.")

        auth_manager = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return sp

    def display_message(self, sender, message):
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END, f"{sender}: {message}\n")
        self.chat_history.config(state='disabled')
        self.chat_history.yview(tk.END)

    def send_message(self, event=None):
        user_message = self.user_input.get()
        if user_message.strip():
            self.display_message("User", user_message)
            self.history.add_message("User", user_message)
            self.user_input.delete(0, tk.END)
            threading.Thread(target=self.get_response).start()  # Use threading for async response

    def get_response(self):
        temperature = self.temperature_slider.get()
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.history.format_message_history(),
                temperature=temperature
            )
            bot_message = response.choices[0].message.content
        except Exception as e:
            bot_message = f"Error: {str(e)}"
        self.display_message("Chatbot", bot_message)
        self.history.add_message("Chatbot", bot_message)

    def update_temperature_label(self, event=None):
        self.temperature_value_label.config(text=f"{self.temperature_slider.get():.1f}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()
