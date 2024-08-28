from spotify_interface.spotify_tools import create_playlist, add_tracks_to_playlist

class CreatePlaylistHelper:
    def __init__(self, sp, user_id):
        """
        Initialize the CreatePlaylistHelper with the Spotify client and user ID.
        """
        self.sp = sp
        self.user_id = user_id
        self.last_playlist_id = None

    def perform_task(self, playlist_name):
        """
        Create a playlist with the given name and store the playlist ID.
        """
        try:
            playlist_id = create_playlist(self.sp, self.user_id, playlist_name)
            self.last_playlist_id = playlist_id
            return f"Playlist '{playlist_name}' created successfully. Playlist ID: {playlist_id}"
        except Exception as e:
            return f"Error creating playlist '{playlist_name}': {str(e)}"

class AddTracksHelper:
    def __init__(self, sp, user_id):
        """
        Initialize the AddTracksHelper with the Spotify client and user ID.
        """
        self.sp = sp
        self.user_id = user_id

    def perform_task(self, playlist_id, songs):
        """
        Add the given list of songs to the specified playlist.
        """
        try:
            track_uris = add_tracks_to_playlist(self.sp, self.user_id, playlist_id, songs)
            return f"Tracks added to playlist '{playlist_id}' successfully. Track URIs: {track_uris}"
        except Exception as e:
            return f"Error adding tracks to playlist '{playlist_id}': {str(e)}"
