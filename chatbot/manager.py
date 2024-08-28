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
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "create_playlist",
                        "description": "Create an empty playlist with an appropriate name.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "playlist_name": {
                                    "type": "string",
                                    "description": "The name of the playlist",
                                }
                            },
                            "required": ["playlist_name"],
                        },
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "add_tracks_to_playlist",
                        "description": "Add multiple tracks to a specified playlist.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "playlist_id": {
                                    "type": "string",
                                    "description": "The ID of the playlist.",
                                },
                                "songs": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "artist_and_song": {
                                                "type": "string",
                                                "description": "A song, formatted as {artist} - {song}",
                                            }
                                        },
                                        "required": ["artist_and_song"]
                                    },
                                    "description": "A list of songs to add to the playlist"
                                }
                            },
                            "required": ["playlist_id", "songs"],
                        },
                    }
                }
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Or another model like "gpt-3.5-turbo"
                messages=formatted_messages,
                temperature=temperature,
                tools=tools,  # Include the tools
                tool_choice="auto"  # Allow the model to automatically select the tools
            )

            # Extract the content of the response correctly
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

        if ai_response:
            try:
                response_data = json.loads(ai_response)  # Try parsing as JSON

                # If it's a tool call response, we add to the task list
                for tool_call in response_data.get("tool_calls", []):
                    print(f"Detected tool call: {tool_call['function_name']}")
                    if tool_call["function_name"] == "create_playlist":
                        task_list.append({
                            "task": "create_playlist",
                            "playlist_name": tool_call["arguments"]["playlist_name"]
                        })
                    elif tool_call["function_name"] == "add_tracks_to_playlist":
                        task_list.append({
                            "task": "add_tracks_to_playlist",
                            "playlist_id": tool_call["arguments"]["playlist_id"],
                            "songs": tool_call["arguments"]["songs"]
                        })
                print("Task list generated:", task_list)

            except json.JSONDecodeError:
                print("Failed to parse AI response as JSON. Check the format.")
        return task_list

    def execute_tasks(self):
        """
        Executes tasks in the task list by delegating them to the appropriate helper agents.
        """
        responses = []
        print("Executing tasks from the task list...")
        while self.task_list:
            task = self.task_list.pop(0)
            print(f"Executing task: {task['task']}")
            if task['task'] == 'create_playlist':
                result = self.create_playlist_helper.perform_task(task['playlist_name'])
                print(f"Create Playlist Result: {result}")
                responses.append(result)
            elif task['task'] == 'add_tracks_to_playlist':
                playlist_id = self.create_playlist_helper.last_playlist_id
                print(f"Adding tracks to playlist: {playlist_id}")
                result = self.add_tracks_helper.perform_task(playlist_id, task['songs'])
                print(f"Add Tracks Result: {result}")
                responses.append(result)
        print("All tasks executed.")
        return "\n".join(responses)
