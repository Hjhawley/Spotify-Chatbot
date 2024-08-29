import json
import os
from openai import OpenAI
from spotify_interface.spotify_tools import create_playlist, add_tracks_to_playlist

class CreatePlaylistHelper:
    def __init__(self, sp, user_id):
        self.sp = sp
        self.user_id = user_id
        self.last_playlist_id = None
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def perform_task(self, playlist_name):
        try:
            print(f"Creating playlist: {playlist_name}")
            # Create the playlist using Spotify API
            playlist_id = create_playlist(self.sp, self.user_id, playlist_name)
            self.last_playlist_id = playlist_id
            print(f"Playlist '{playlist_name}' created with ID: {playlist_id}")
            return f"Playlist '{playlist_name}' created successfully."
        except Exception as e:
            print(f"Error in CreatePlaylistHelper: {str(e)}")
            return f"Error creating playlist '{playlist_name}': {str(e)}"

class AddTracksHelper:
    def __init__(self, sp, user_id):
        self.sp = sp
        self.user_id = user_id
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def perform_task(self, playlist_id, songs):
        try:
            print(f"Adding tracks to playlist ID: {playlist_id}")
            # Add tracks using Spotify API
            track_uris = add_tracks_to_playlist(self.sp, self.user_id, playlist_id, songs)
            print(f"Tracks added: {track_uris}")
            return f"Tracks added to playlist '{playlist_id}' successfully."
        except Exception as e:
            print(f"Error in AddTracksHelper: {str(e)}")
            return f"Error adding tracks to playlist '{playlist_id}': {str(e)}"
