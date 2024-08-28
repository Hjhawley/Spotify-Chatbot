import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from chatbot.manager import ManagerAgent
from chatbot.message_history import MessageHistory

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot")

        # Initialize ManagerAgent and MessageHistory
        self.manager_agent = ManagerAgent()
        self.history = MessageHistory()

        # Setup the history display (ScrolledText widget)
        self.history_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.history_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Setup the input frame and input field
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X, expand=True)

        self.user_input = tk.Entry(self.input_frame, width=80)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Temperature slider setup
        self.temperature_frame = tk.Frame(self.root)
        self.temperature_frame.pack(pady=5, fill=tk.X)

        self.temperature_label = tk.Label(self.temperature_frame, text="Temperature")
        self.temperature_label.pack(side=tk.LEFT)

        self.temperature_slider = ttk.Scale(self.temperature_frame, from_=0, to=2, orient='horizontal', value=0.7)
        self.temperature_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.temperature_slider.bind("<Motion>", self.update_temperature_label)

        self.temperature_value_label = tk.Label(self.temperature_frame, text=f"{self.temperature_slider.get():.1f}")
        self.temperature_value_label.pack(side=tk.RIGHT)

        # Start authentication message
        self.root.after(10, self.spotify_auth_message)

    def spotify_auth_message(self):
        try:
            self.sp = self.manager_agent.authenticate_spotify()
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
        response = self.manager_agent.handle_user_message(self.history.format_message_history(), temperature)
        self.display_message("Chatbot", response)
        self.history.add_message("Chatbot", response)

    def update_temperature_label(self, event=None):
        self.temperature_value_label.config(text=f"{self.temperature_slider.get():.1f}")
