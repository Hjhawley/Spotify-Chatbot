import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

def authenticate_spotify() -> spotipy.Spotify:
    scope = os.getenv("SPOTIPY_SCOPE")
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    if not all([scope, client_id, client_secret, redirect_uri]):
        raise ValueError("Missing Spotify API credentials.")

    auth_manager = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp
