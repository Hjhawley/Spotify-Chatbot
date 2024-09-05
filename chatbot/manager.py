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
            print(f"AI Response: {ai_response}")  # Debugging output
            if "***GENERATING TASK LIST***" in ai_response:
                print("Task list generation detected.")  # Debugging output
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
            functions = [
                {
                    "name": "generate_task_list",  # Ensure the name field is present and correct
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
            ]

            # Modify the prompt to explicitly instruct the AI to output JSON
            system_prompt = (
                "You are an AI assistant. Based on the conversation, generate a step-by-step task list in JSON format. "
                "The JSON object should contain steps as keys and the corresponding descriptions as values. "
                "Do not include any additional text, just return the JSON object."
            )

            # Debugging: Check the prompt and request details
            print(f"Sending system prompt: {system_prompt}")
            print(f"AI response content: {ai_response}")

            # Use GPT-4 to generate the prompt and call the function
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": ai_response}
                ],
                temperature=0.5,
                functions=functions,  # Pass the corrected functions parameter
                function_call={"name": "generate_task_list"}  # Call the generate_task_list function
            )

            # Check if the function was called
            print(f"Function Call Attempted: {response.choices[0].message.function_call}")  # Debugging output

            # Check if the response contains valid content
            response_content = response.choices[0].message.content
            print(f"Raw AI Response Content: {response_content}")  # Debugging output
            if response_content is None:
                print("Error: The AI response returned no content.")
                return None

            # Try to parse the response content as JSON
            try:
                task_list = json.loads(response_content)
                print(f"Generated Task List: {task_list}")
                return task_list
            except json.JSONDecodeError as e:
                print(f"Error parsing task list: {str(e)}")
                return None

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
