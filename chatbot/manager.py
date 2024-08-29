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

            # Check if the response indicates task generation
            if "***GENERATING TASK LIST***" in ai_response:
                print("Detected task generation signal from AI response.")
                self.task_list = self.create_task_list_from_response(ai_response)
                if self.task_list:
                    return self.execute_tasks()
                else:
                    return "Error: No tasks generated from the AI response."
            else:
                # If the response is purely conversational, just return it as-is
                return ai_response
        else:
            return "Error: Could not generate a response."

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

    def create_task_list_from_response(self, ai_response):
        task_list = []
        print("Parsing AI response to generate tasks...")

        # Strip the task generation signal from the response if present
        #ai_response = ai_response.replace("***GENERATING TASK LIST***", "").strip()

        try:
            # Attempt to parse as JSON first
            response_data = json.loads(ai_response)
            if "create_playlist" in response_data:
                playlist_name = response_data["create_playlist"]["playlist_name"]
                task_list.append({"task": "create_playlist", "playlist_name": playlist_name})
            if "add_tracks_to_playlist" in response_data:
                playlist_id = response_data["add_tracks_to_playlist"]["playlist_id"]
                songs = response_data["add_tracks_to_playlist"]["songs"]
                task_list.append({"task": "add_tracks_to_playlist", "playlist_id": playlist_id, "songs": songs})

        except json.JSONDecodeError:
            print("AI response is not JSON; treating as plain text.")
            # Fallback to text-based task identification
            if "create a playlist" in ai_response.lower():
                task_list.append({"task": "create_playlist", "playlist_name": "Generated Playlist Name"})
            if "add tracks" in ai_response.lower():
                task_list.append({"task": "add_tracks_to_playlist", "playlist_id": self.create_playlist_helper.last_playlist_id, "songs": []})
        
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
