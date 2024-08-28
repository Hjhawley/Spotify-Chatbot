import json
import os
from openai import OpenAI
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

        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def process_user_request(self, formatted_messages, temperature):
        """
        Processes the user's request, determines if a task list is needed, and manages the flow of tasks.
        """
        # Replace the simulated response with an actual OpenAI API call
        ai_response = self.get_openai_response(formatted_messages, temperature)
        print(f"AI Response: {ai_response}")

        # Parse the AI's response to determine what actions to take
        self.task_list = self.create_task_list_from_response(ai_response)

        # Execute tasks
        return self.execute_tasks()

    def get_openai_response(self, formatted_messages, temperature):
        """
        Makes an API call to OpenAI's GPT model to get a response based on the conversation history.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Or another model like "gpt-3.5-turbo"
                messages=formatted_messages,
                temperature=temperature
            )
            # Extract the content of the response
            return response.choices[0].message['content']
        except Exception as e:
            print(f"Error fetching OpenAI response: {str(e)}")
            return None

    def create_task_list_from_response(self, ai_response):
        """
        Parses the AI's response to create a list of tasks for the helper agents to perform.
        """
        task_list = []
        if ai_response:  # Check if there's a valid AI response
            # Assuming the AI response is a JSON-like structure (you may need to parse it)
            try:
                response_data = json.loads(ai_response)

                if "create_playlist" in response_data and "add_songs" in response_data:
                    task_list.append({
                        "task": "create_playlist",
                        "playlist_name": response_data["create_playlist"]["playlist_name"]
                    })
                    task_list.append({
                        "task": "add_tracks_to_playlist",
                        "songs": response_data["add_songs"]["songs"]
                    })
                # Add more conditions for other complex requests

            except json.JSONDecodeError:
                print("Failed to parse AI response. Check the format.")
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
