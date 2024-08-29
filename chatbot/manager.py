import json
import os
from openai import OpenAI
from chatbot.helpers import CreatePlaylistHelper, AddTracksHelper
from spotify_interface.spotify_tools import authenticate_spotify

class ManagerAgent:
    def __init__(self):
        self.sp = authenticate_spotify()
        self.user_id = self.sp.current_user()['id']
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.create_playlist_helper = CreatePlaylistHelper(self.sp, self.user_id)
        self.add_tracks_helper = AddTracksHelper(self.sp, self.user_id)
        self.task_list = []

    def process_user_request(self, formatted_messages, temperature):
        ai_response = self.get_openai_response(formatted_messages, temperature)
        if ai_response:
            print(f"AI Response: {ai_response}")
            if "***GENERATING TASK LIST***" in ai_response:
                print("Detected task generation signal from AI response.")
                return self.manage_tasks(ai_response)
            else:
                return ai_response  # Just a normal conversational response
        else:
            return "Error: Could not generate a response."
        
    def manage_tasks(self, ai_response):
        task_report = []
        print("Entering task management loop...")

        # Start by checking for tasks in the AI response
        task_list = self.create_task_list_from_plain_text(ai_response)
        while task_list:
            for task in task_list:
                if task['task'] == 'create_playlist':
                    result = self.create_playlist_helper.perform_task(task['playlist_name'])
                    task_report.append(result)
                    task_list.remove(task)  # Remove completed task
                elif task['task'] == 'add_tracks_to_playlist':
                    # Wait for playlist creation if needed
                    if self.create_playlist_helper.last_playlist_id:
                        result = self.add_tracks_helper.perform_task(self.create_playlist_helper.last_playlist_id, task['songs'])
                        task_report.append(result)
                        task_list.remove(task)  # Remove completed task
                    else:
                        print("Waiting for playlist creation...")
        return "\n".join(task_report)  # Report back to user

    def create_task_list_from_plain_text(self, ai_response):
        task_list = []
        print("Parsing AI response to generate tasks...")

        if "Creating a blank playlist called" in ai_response:
            playlist_name = ai_response.split("Creating a blank playlist called")[1].split('"')[1]
            task_list.append({"task": "create_playlist", "playlist_name": playlist_name})
            print(f"Task: Create playlist '{playlist_name}'")

        # Add more parsing logic here as needed to detect other tasks
        # For example, adding tracks might involve looking for specific keywords or phrases

        if not task_list:
            print("No tasks generated from the AI response.")
        return task_list

    def get_openai_response(self, formatted_messages, temperature):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=formatted_messages,
                temperature=temperature
            )
            print("Raw AI Response:", response)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error fetching OpenAI response: {str(e)}")
            return None
