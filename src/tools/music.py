import subprocess
import requests
import io
import pygame
import numpy as np
from pydub import AudioSegment
import json
import difflib
import time

from src.server.model import create_mistral_agent

client = create_mistral_agent()


play_obj = None
music_player = None
model = "mistral-large-latest"  # Replace with your model name

# Initialize pygame mixer
pygame.mixer.init(frequency=44100, size=-16, channels=2)

# List of songs with their titles and S3 URLs
s3_song_list = [
    ["Main Theme", "http://s3.ru1.storage.beget.cloud/04ea256ef50e-busy-lars/dndost/1-01%20Main%20Theme.mp3"],
    ["Village Day Theme", "http://s3.ru1.storage.beget.cloud/04ea256ef50e-busy-lars/dndost/1-06%20Colony%209%20%5BRemastered%5D.mp3"],
    ["Village Night Theme", "http://s3.ru1.storage.beget.cloud/04ea256ef50e-busy-lars/dndost/2-19%20Frontier%20Village%20(Night)%20%5BRemastered%5D.mp3"],
    ["Tension Theme", "http://s3.ru1.storage.beget.cloud/04ea256ef50e-busy-lars/dndost/2-05%20Tension.mp3"],
    ["Forest Theme", "http://s3.ru1.storage.beget.cloud/04ea256ef50e-busy-lars/dndost/2-16%20Forest%20of%20the%20Nopon%20%5BRemastered%5D.mp3"],
    ["Battle Theme", "http://s3.ru1.storage.beget.cloud/04ea256ef50e-busy-lars/dndost/3-06%20You%20Will%20Know%20Our%20Names%20%5BRemastered%5D.mp3"]
]

# Function to play audio from an S3 URL
def play_audio_from_s3(url, volume=0.3):
    global play_obj

    # Stop any previous playback before starting a new one
    stop_audio()

    try:
        # Download the audio file from S3
        response = requests.get(url)
        response.raise_for_status()

        # Load the audio as a Pydub AudioSegment
        audio = AudioSegment.from_mp3(io.BytesIO(response.content))

        # Convert audio to stereo data for pygame
        samples = np.array(audio.get_array_of_samples()).reshape((-1, audio.channels))

        # Adjust the volume
        samples = (samples * volume).astype(np.int16)

        # Use pygame to create a sound object
        sound = pygame.sndarray.make_sound(samples)

        # Play the audio
        play_obj = sound.play()
        print("Audio playback started.")
    except Exception as e:
        print(f"Error loading or playing audio: {e}")

# Function to stop audio playback
def stop_audio():
    global play_obj

    if play_obj:
        play_obj.stop()  # Stop audio playback
        print("Audio playback stopped.")
        play_obj = None
        music_player = None
    else:
        print("No active audio to stop.")

    return json.dumps({"status": "No-op"})

# Function to play music from the S3 playlist
def play_music_from_playlist(query: str, volume=30):
    global music_player

    # Check if music is already playing
    if music_player is not None:
        print("Music is already playing. Skipping new track.")
        return "Music is already playing. Skipping new track."

    try:
        # Extract video titles and URLs from the S3 song list
        video_titles = [entry[0] for entry in s3_song_list]
        video_urls = [entry[1] for entry in s3_song_list]

        print(f"Found videos: {video_titles}")

        # Use Mistral or other logic to select the best match
        relevant_video = filter_video_by_query(video_titles, query)
        print(f"Relevant video selected: '{relevant_video}'")

        if relevant_video is None:
            print("No relevant video found for the query.")
            return "No relevant video found for the query."

        # Normalize the relevant video title
        relevant_video_normalized = relevant_video.strip().lower()
        print(f"Normalized relevant video: '{relevant_video_normalized}'")

        # Find the matching video URL
        match = None
        for entry in s3_song_list:
            playlist_title_normalized = entry[0].strip().lower()
            if relevant_video_normalized == playlist_title_normalized:
                match = entry
                break

        # If no exact match is found, use fuzzy matching
        if not match:
            print(f"No exact match found for '{relevant_video}'. Using fuzzy matching.")
            closest_match = difflib.get_close_matches(relevant_video, video_titles, n=1)
            if closest_match:
                print(f"Using closest match: {closest_match[0]}")
                match = next(
                    (entry for entry in s3_song_list if entry[0] == closest_match[0]), None
                )

        if match:
            video_url = match[1]
            print(f"Found relevant video: {match[0]} - {video_url}")
        else:
            print("No suitable match found.")
            return "No suitable match found."

    except Exception as e:
        print(f"Error retrieving playlist or videos: {e}")
        return f"Error: {str(e)}"

    # Create and start a new player instance
    music_player = 1
    play_audio_from_s3(video_url, volume = volume/10)

    return "No-op"

# Function to filter video titles by query using Mistral (or fallback logic)
def filter_video_by_query(video_titles, query):
    """
    This function will use Mistral to decide which video title fits the user's request.
    If Mistral finds a relevant match, it returns the corresponding video title.
    """
    prompt = f"""
    Given the following video titles and the query '{query}', which video title best fits the request? Titles: {video_titles}. Be really short in your answer, 1 sentence max, Return only the name of the video.
    """

    # Send the prompt to Mistral API
    response = client.chat.complete(
        model="ministral-8b-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    time.sleep(2)

    best_match = response.choices[0].message.content.strip()
    print(f"Mistral's suggestion: {best_match}")
    return best_match

if __name__=="__main__":

    play_music_from_playlist("play music for small rural town")
    time.sleep(15)
    stop_audio()
