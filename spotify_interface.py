import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fuzzywuzzy import fuzz

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

def create_playlist(sp, user_id, playlist_name):
    if isinstance(user_id, dict) and 'id' in user_id:
        user_id = user_id['id']
    playlist = sp.user_playlist_create(user_id, playlist_name)
    return playlist['id']

def find_best_track_match(tracks, query):
    best_match, best_score = None, 0
    for track in tracks:
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        popularity = track['popularity']
        match_score = fuzz.partial_ratio(query.lower(), f"{artist_name} {track_name}".lower())
        if match_score > best_score or (match_score == best_score and popularity > best_match['popularity']):
            best_match = track
            best_score = match_score
    return best_match

def search_track(sp, track_name, artist_name):
    results = sp.search(q=f"track:{track_name} artist:{artist_name}", type='track')
    tracks = results['tracks']['items']
    if not tracks:
        return None
    best_match = find_best_track_match(tracks, f"{artist_name} {track_name}")
    return best_match['uri'] if best_match else None

def add_tracks_to_playlist(sp, user_id, playlist_id, songs):
    track_uris = []
    for song in songs:
        print(f"Searching for: {song['track_name']} by {song['artist_name']}")  # Debugging statement
        track_uri = search_track(sp, song['track_name'], song['artist_name'])
        if track_uri:
            track_uris.append(track_uri)
        else:
            print(f"Track not found: {song['track_name']} by {song['artist_name']}")  # Debugging statement
    if track_uris:
        sp.user_playlist_add_tracks(user_id, playlist_id, track_uris)
    print(f"Track URIs added: {track_uris}")  # Debugging statement
    return track_uris
