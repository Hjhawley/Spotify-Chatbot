import json
from chatbot.helpers import CreatePlaylistHelper, AddTracksHelper
from spotify_interface.spotify_tools import authenticate_spotify

class ManagerAgent:
    def __init__(self):
        # Initialize the Spotify client
        self.sp = authenticate_spotify()
        self.user_id = self.sp.current_user()['id']

        # Initialize helper agents
        self.create_playlist_helper = CreatePlaylistHelper(self.sp, self.user_id)
        self.add_tracks_helper = AddTracksHelper(self.sp, self.user_id)

        # Initialize task list
        self.task_list = []

    def process_user_request(self, formatted_messages, temperature):
        """
        Processes the user's request, determines if a task list is needed, and manages the flow of tasks.
        """
        # Simulate a response from OpenAI (this would be an API call in a real implementation)
        ai_response = self.simulate_openai_response(formatted_messages, temperature)
        print(f"AI Response: {ai_response}")

        # Parse the AI's response to determine what actions to take
        self.task_list = self.create_task_list_from_response(ai_response)

        # Execute tasks
        return self.execute_tasks()

    def create_task_list_from_response(self, ai_response):
        """
        Parses the AI's response to create a list of tasks for the helper agents to perform.
        """
        task_list = []
        if "create playlist" in ai_response and "add songs" in ai_response:
            task_list.append({
                "task": "create_playlist",
                "playlist_name": ai_response["playlist_name"]
            })
            task_list.append({
                "task": "add_tracks_to_playlist",
                "songs": ai_response["songs"]
            })
        # Add more conditions for other complex requests

        return task_list

    def execute_tasks(self):
        """
        Executes tasks in the task list by delegating them to the appropriate helper agents.
        """
        responses = []
        while self.task_list:
            task = self.task_list.pop(0)
            if task['task'] == 'create_playlist':
                result = self.create_playlist_helper.perform_task(task['playlist_name'])
                responses.append(result)
            elif task['task'] == 'add_tracks_to_playlist':
                playlist_id = self.create_playlist_helper.last_playlist_id  # Assumes the last playlist created is the one to be populated
                result = self.add_tracks_helper.perform_task(playlist_id, task['songs'])
                responses.append(result)
        return "\n".join(responses)

    def simulate_openai_response(self, formatted_messages, temperature):
        """
        This function simulates an OpenAI API call and response.
        Replace this with the actual API call in your implementation.
        """
        # Simulated AI response based on user input
        # This is a placeholder. Replace with actual logic to interact with OpenAI.
        ai_response = {
            "playlist_name": "Chill Vibes",
            "songs": [
                {"artist_and_song": "Artist 1 - Song 1"},
                {"artist_and_song": "Artist 2 - Song 2"},
                {"artist_and_song": "Artist 3 - Song 3"}
            ]
        }
        return ai_response
