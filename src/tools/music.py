
import subprocess
import io
import simpleaudio as sa
from pydub import AudioSegment
import threading
import json

import yt_dlp
import difflib
from src.configs import playlist_url, model_name
from src.server.model import create_mistral_agent
playlist_url= "https://www.youtube.com/playlist?list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq"

# Global player variable
play_obj = None
playback_thread = None
music_player = None
client = create_mistral_agent()
model = model_name


import subprocess
import io
import pygame
import numpy as np
from pydub import AudioSegment
import threading
import json
import yt_dlp
import difflib

# Global player variables
play_obj = None
music_player = None
model = "mistral-large-latest"  # Replace with your model name

# Initialize pygame mixer
pygame.mixer.init(frequency=44100, size=-16, channels=2)


# Function to play audio from YouTube URL
def play_audio_from_youtube(url, volume=0.5):
    global play_obj

    # Stop any previous playback before starting a new one
    stop_audio()

    # yt-dlp options to get the best audio stream (audio-only)
    ydl_opts = {
        'format': 'bestaudio/best',  # Get best audio format
        'outtmpl': '-',  # Don't save the file, just extract it
        'quiet': True,
        'noplaylist': True,  # Disable playlist extraction
        'extractaudio': True,  # Extract audio only
    }

    # Download audio with yt-dlp and extract the audio stream URL
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)

        # Check all available formats and ensure we get the audio URL
        audio_url = None
        for format in info_dict['formats']:
            if format.get('vcodec') == 'none' and format.get('acodec') != 'none':  # Audio stream, no video
                audio_url = format['url']
                break

        if not audio_url:
            print("Error: No valid audio stream found.")
            return

    # Use ffmpeg to directly stream and convert the audio to a playable format
    print("Downloading and playing audio from YouTube...")

    command = [
        'ffmpeg',
        '-i', audio_url,  # Input URL
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # Raw PCM audio
        '-ar', '44100',  # Sample rate
        '-ac', '2',  # Stereo
        '-f', 'wav',  # Output format
        'pipe:1'  # Output to stdout (piped)
    ]

    # Run the command and get the audio output in memory
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # If there was an error in ffmpeg, print it
    if process.returncode != 0:
        print(f"ffmpeg error: {stderr.decode()}")
        return

    try:
        # Load the audio as a Pygame sound object
        audio = AudioSegment.from_wav(io.BytesIO(stdout))

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
        music_player=None
    else:
        print("No active audio to stop.")

    return json.dumps({"status":"No-op"})


# Function to play music from a playlist
def play_music_from_playlist(query: str,volume=50):
    global music_player

    # Check if music is already playing
    if music_player is not None:
        print("Music is already playing. Skipping new track.")
        return "Music is already playing. Skipping new track."

    try:
        # Load playlist information
        with open("C:\\Users\\leftg\\PycharmProjects\\Dnd_bot\\src\\utlis\\playlist_info.json", "r") as f:
            playlist_info = json.load(f)

        print("playlist_info", playlist_info)

        video_titles = [entry[0] for entry in playlist_info]
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
        for entry in playlist_info:
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
                    (entry for entry in playlist_info if entry[0] == closest_match[0]), None
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
    play_audio_from_youtube(video_url)

    return "No-op"



# Function to filter video titles by query using Mistral (or fallback logic)
def filter_video_by_query(video_titles, query):
    """
    This function will use Mistral to decide which video title fits the user's request.
    If Mistral finds a relevant match, it returns the corresponding video title.
    """
    prompt = f"""
    Given the following video titles and the query '{query}', which video title best fits the request? Titles: {video_titles}. Return only the name of the video.
    So good answer for  Включи музыку для города would be Colony 6 - Rebuilding Extended - Xenoblade Chronicles Definitive Edition OST, not "To determine which video title best fits the query 'музыка для города' (which translates to "music for the city"), we need to identify a title that suggests an urban or city-related theme.
The title "Colony 6 - Rebuilding Extended - Xenoblade Chronicles Definitive Edition OST" seems to fit best as "Colony 6" suggests a developed area, which could be associated with a city."
"""

    # Send the prompt to Mistral API
    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    best_match = response.choices[0].message.content.strip()
    print(f"Mistral's suggestion: {best_match}")
    return best_match


