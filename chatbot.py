import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load OpenAI API key from .env file
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
        
        self.chat_history = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.user_input = tk.Entry(self.root, width=80)
        self.user_input.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", self.send_message)
        
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(padx=10, pady=10, side=tk.RIGHT)

        self.temperature_label = tk.Label(self.root, text="Temperature")
        self.temperature_label.pack(pady=5)
        
        self.temperature_slider = ttk.Scale(self.root, from_=0, to=2, orient='horizontal', value=0.7)
        self.temperature_slider.pack(pady=5, fill=tk.X, padx=10)
        self.temperature_slider.bind("<Motion>", self.update_temperature_label)

        self.temperature_value_label = tk.Label(self.root, text=f"{self.temperature_slider.get():.1f}")
        self.temperature_value_label.pack(pady=5)

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
            self.user_input.delete(0, tk.END) # Clear the input field
            self.get_response() # Pass the entire message history as input

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
