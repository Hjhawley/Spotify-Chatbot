import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from dotenv import load_dotenv
import os
from openai import OpenAI
from spotify_interface import authenticate_spotify
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
        formatted_messages = [{"role": "system", "content": "You are an AI chatbot designed to create and populate Spotify playlists for users. Maintain a clear, conversational, helpful tone. Ask questions when necessary."}]
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

        # Schedule the authentication message to be displayed after the GUI is set up
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
        self.history_display.config(state='normal')
        self.history_display.insert(tk.END, f"{sender}: {message}\n")
        self.history_display.config(state='disabled')
        self.history_display.yview(tk.END)

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
