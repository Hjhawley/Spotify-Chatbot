import json
import os
from openai import OpenAI
from chatbot.helpers import CreatePlaylistHelper, AddTracksHelper
from spotify_interface.spotify_tools import authenticate_spotify

class ManagerAgent:
    def __init__(self):
        self.sp = authenticate_spotify()
        self.user_id = self.sp.current_user()['id']
        self.create_playlist_helper = CreatePlaylistHelper(self.sp, self.user_id)
        self.add_tracks_helper = AddTracksHelper(self.sp, self.user_id)
        self.task_list = []

    def process_user_request(self, formatted_messages, temperature):
        ai_response = self.get_openai_response(formatted_messages, temperature)
        if ai_response:
            print(f"AI Response: {ai_response}")
            self.task_list = self.create_task_list_from_response(ai_response)
            return self.execute_tasks()
        else:
            return "Error: Could not generate a response."

    def get_openai_response(self, formatted_messages, temperature):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=formatted_messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error fetching OpenAI response: {str(e)}")
            return None

    def create_task_list_from_response(self, ai_response):
        """
        Parses the AI's response to create a list of tasks for the helper agents to perform.
        """
        task_list = []
        print("Parsing AI response to generate tasks...")

        try:
            response_data = json.loads(ai_response)  # Parse AI response as JSON
            
            # Extract playlist creation task
            if "create_playlist" in response_data:
                playlist_name = response_data["create_playlist"]["playlist_name"]
                task_list.append({"task": "create_playlist", "playlist_name": playlist_name})
                print(f"Task: Create playlist '{playlist_name}'")

            # Extract add tracks task
            if "add_tracks_to_playlist" in response_data:
                playlist_id = response_data["add_tracks_to_playlist"]["playlist_id"]
                songs = response_data["add_tracks_to_playlist"]["songs"]
                task_list.append({"task": "add_tracks_to_playlist", "playlist_id": playlist_id, "songs": songs})
                print(f"Task: Add tracks to playlist '{playlist_id}' with songs: {songs}")

        except json.JSONDecodeError:
            print("Failed to parse AI response as JSON. Check the format.")
        except KeyError as e:
            print(f"KeyError in parsing AI response: {str(e)}")
        
        return task_list

    def execute_tasks(self):
        """
        Executes tasks in the task list by delegating them to the appropriate helper agents.
        """
        responses = []
        print("Executing tasks from the task list...")

        while self.task_list:
            task = self.task_list.pop(0)
            if task['task'] == 'create_playlist':
                # Pass the playlist name to the CreatePlaylistHelper
                result = self.create_playlist_helper.perform_task(task['playlist_name'])
                responses.append(result)
            elif task['task'] == 'add_tracks_to_playlist':
                # Pass the playlist ID and song list to the AddTracksHelper
                result = self.add_tracks_helper.perform_task(task['playlist_id'], task['songs'])
                responses.append(result)
        
        print("All tasks executed.")
        return "\n".join(responses)
