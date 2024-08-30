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

    def process_user_request(self, formatted_messages, temperature):
        ai_response = self.get_openai_response(formatted_messages, temperature)
        if ai_response:
            print(f"AI Response: {ai_response}")
            if "***GENERATING TASK LIST***" in ai_response:
                # Call the tool to generate the task list with AI-generated parameters
                task_list = self.generate_task_list(ai_response)
                if task_list:
                    return self.manage_tasks(task_list)
                else:
                    return "Error: Could not generate a task list."
            else:
                return ai_response  # Just a normal conversational response
        else:
            return "Error: Could not generate a response."

    def generate_task_list(self, ai_response):
        """The ManagerAgent uses GPT-4 to intelligently create the prompt and then generate a task list."""
        try:
            # Define the tools to be used by the AI
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "generate_task_list",
                        "description": "Generate a step-by-step task list based on the user's request.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "A detailed prompt describing the task to be accomplished."
                                }
                            },
                            "required": ["prompt"],
                        },
                    }
                }
            ]

            # Use GPT-4 to generate the prompt and call the tool
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI assistant. Based on the conversation, create a detailed prompt that describes the task the user wants to accomplish."},
                    {"role": "user", "content": ai_response}
                ],
                temperature=0.5,
                tools=tools,
                function_call={"name": "generate_task_list"}  # Call the generate_task_list tool
            )

            # Parse the response to extract the task list
            task_list = json.loads(response.choices[0].message.content)
            print(f"Generated Task List: {task_list}")
            return task_list

        except Exception as e:
            print(f"Error generating task list: {str(e)}")
            return None

    def manage_tasks(self, task_list):
        task_report = []
        print("Entering task management loop...")

        for step, description in task_list.items():
            if "create_playlist" in description.lower():
                result = self.create_playlist_helper.perform_task(description)
                task_report.append(result)
            elif "add_tracks" in description.lower():
                if self.create_playlist_helper.last_playlist_id:
                    result = self.add_tracks_helper.perform_task(self.create_playlist_helper.last_playlist_id, description)
                    task_report.append(result)
                else:
                    print("No playlist created yet, cannot add tracks.")

        return "\n".join(task_report)

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
