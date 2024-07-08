import tkinter as tk
from tkinter import scrolledtext
from dotenv import load_dotenv
import os
import openai

# Load OpenAI API key from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class MessageHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, message):
        self.messages.append({"sender": sender, "message": message})

    def get_messages(self):
        return self.messages

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
            self.get_response(user_message)

    def get_response(self, user_message):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI chatbot. You are friendly and covnersational."},
                {"role": "user", "content": user_message}
            ]
        )
        bot_message = response.choices[0].message['content'] # Extract the chatbot's reply
        self.display_message("Chatbot", bot_message)
        self.history.add_message("Chatbot", bot_message)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()
