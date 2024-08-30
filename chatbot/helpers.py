import json
import os
from openai import OpenAI
from spotify_interface.spotify_tools import create_playlist

class CreatePlaylistHelper:
    def __init__(self, sp, user_id):
        self.sp = sp
        self.user_id = user_id
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.last_playlist_id = None

    def perform_task(self, task_details):
        try:
            # Extract the relevant details from the JSON task details
            playlist_name = task_details.get("playlist_name")
            print(f"CreatePlaylistHelper: Creating playlist '{playlist_name}'...")

            # Call the OpenAI API with the extracted details to create the playlist
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CreatePlaylistHelper agent. Your job is to create a playlist with the provided name."
                    },
                    {
                        "role": "user",
                        "content": f"Create a playlist named '{playlist_name}'"
                    }
                ],
                temperature=0.5,
                tools=[
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
                    }
                ],
                tool_choice="auto"
            )

            # Extract the tool call result and execute the task
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls:
                args = json.loads(tool_calls[0].function.arguments)
                playlist_name = args["playlist_name"]

                # Execute the tool call to create the playlist
                playlist_id = create_playlist(self.sp, self.user_id, playlist_name)
                self.last_playlist_id = playlist_id
                return {"message": f"Playlist '{playlist_name}' created successfully with ID: {playlist_id}"}

            else:
                return {"error": "No tool calls were made by the AI."}

        except Exception as e:
            print(f"Error in CreatePlaylistHelper: {str(e)}")
            return {"error": f"Error creating playlist '{playlist_name}': {str(e)}"}

import json
import os
from openai import OpenAI
from spotify_interface.spotify_tools import add_tracks_to_playlist

class AddTracksHelper:
    def __init__(self, sp, user_id):
        self.sp = sp
        self.user_id = user_id
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def perform_task(self, task_details):
        try:
            # Extract the relevant details from the JSON task details
            playlist_id = task_details.get("playlist_id")
            songs = task_details.get("songs")
            print(f"AddTracksHelper: Adding tracks to playlist '{playlist_id}'...")

            # Call the OpenAI API with the extracted details to add tracks to the playlist
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AddTracksHelper agent. Your job is to add tracks to a specified playlist."
                    },
                    {
                        "role": "user",
                        "content": f"Add these tracks to the playlist with ID '{playlist_id}': {', '.join([song['artist_and_song'] for song in songs])}"
                    }
                ],
                temperature=0.5,
                tools=[
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
                ],
                tool_choice="auto"
            )

            # Extract the tool call result and execute the task
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls:
                args = json.loads(tool_calls[0].function.arguments)
                playlist_id = args["playlist_id"]
                songs = args["songs"]

                # Execute the tool call to add tracks to the playlist
                track_uris = add_tracks_to_playlist(self.sp, self.user_id, playlist_id, songs)
                return {"message": f"Tracks added to playlist '{playlist_id}' successfully. Track URIs: {track_uris}"}

            else:
                return {"error": "No tool calls were made by the AI."}

        except Exception as e:
            print(f"Error in AddTracksHelper: {str(e)}")
            return {"error": f"Error adding tracks to playlist '{playlist_id}': {str(e)}"}
