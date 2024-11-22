# # from mistralai import Mistral
# # import os
# #
# # model = "mistral-large-latest"
# # api_key = os.environ.get("MISTRAL_API_KEY")
# # client = Mistral(api_key=api_key)
# #
# # playlist_url = "https://www.youtube.com/playlist?list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq"  # Correct URL
# # music_player = None
# #
# #
# # import yt_dlp
# #
# # import difflib
# # import pafy
# # import vlc
# # import time
# def filter_video_by_query(video_titles, query):
#     """
#     This function will use Mistral to decide which video title fits the user's request.
#     If Mistral finds a relevant match, it returns the corresponding video title.
#     """
#     # Create a prompt for Mistral to analyze the query and decide the best match
#     prompt = f"Given the following video titles and the query '{query}', which video title best fits the request? Titles: {video_titles}.Return only name of hte video "
#
#     # Send the prompt to Mistral API
#     response = client.chat.complete(
#         model=model,
#         messages=[{"role": "user", "content": prompt}]
#     )
#
#     # Correctly access the content of the AssistantMessage object
#     best_match = response.choices[0].message.content.strip()
#     print(f"Mistral's suggestion: {best_match}")
#     # If Mistral's response is a valid match, return it
#
#     return best_match
# #
# #
# # def stop_music():
# #     global music_player
# #     if music_player is not None:
# #         # Stop playback and release resources
# #         music_player.stop()
# #         music_player.release()
# #         music_player = None  # Clear reference to ensure no residual playback
# #         print("Music stopped.")
# #     else:
# #         print("No music is currently playing.")
# #     return "..."  # Suppress response
# import pafy
# import vlc
#
# url = "https://www.youtube.com/watch?v=bMt47wvK6u0"
# # video = pafy.new(url)
# # best = video.getbest()
# # playurl = best.url
# #
# # Instance = vlc.Instance()
# # player = Instance.media_player_new()
# # Media = Instance.media_new(playurl)
# # Media.get_mrl()
# # player.set_media(Media)
# # player.play()
# #
# # import pafy
# # import vlc
#
# import yt_dlp
# import subprocess
# import io
# from pydub import AudioSegment
# from pydub.playback import play
#
#
# def play_audio_from_youtube(url,volume=0.5):
#     # Define yt-dlp options to get the best audio stream (audio-only)
#     ydl_opts = {
#         'format': 'bestaudio/best',  # Get best audio format
#         'outtmpl': '-',  # Don't save the file, just extract it
#         'quiet': True,
#         'noplaylist': True,  # Disable playlist extraction
#         'extractaudio': True,  # Extract audio only
#     }
#
#     # Download audio with yt-dlp and extract the audio stream URL
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info_dict = ydl.extract_info(url, download=False)
#
#         # Check all available formats and ensure we get the audio URL
#         audio_url = None
#         for format in info_dict['formats']:
#             if format.get('vcodec') == 'none' and format.get('acodec') != 'none':  # Audio stream, no video
#                 audio_url = format['url']
#                 break
#
#         if not audio_url:
#             print("Error: No valid audio stream found.")
#             return
#
#     # Use ffmpeg to directly stream and convert the audio to a playable format
#     print("Downloading and playing audio from YouTube...")
#
#     # Pass the audio URL to ffmpeg and decode the stream to an in-memory file
#     command = [
#         'ffmpeg',
#         '-i', audio_url,  # Input URL
#         '-vn',  # No video
#         '-acodec', 'pcm_s16le',  # Raw PCM audio
#         '-ar', '44100',  # Sample rate
#         '-ac', '2',  # Stereo
#         '-f', 'wav',  # Output format
#         'pipe:1'  # Output to stdout (piped)
#     ]
#
#     # Run the command and get the audio output in memory
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     stdout, stderr = process.communicate()
#
#     # If there was an error in ffmpeg, print it
#     if process.returncode != 0:
#         print(f"ffmpeg error: {stderr.decode()}")
#         return
#
#     # Use pydub to load the audio and play it
#     try:
#         # Load audio from memory and apply volume control
#         audio = AudioSegment.from_wav(io.BytesIO(stdout))  # Load the audio from memory
#
#         # Adjust the volume (0.0 to 1.0 scale)
#         audio = audio + (20 * (volume - 1))  # Increase or decrease by dB (1.0 = no change, 0.5 = -6 dB, etc.)
#
#         # Play the audio
#         play(audio)  # Play the audio
#     except Exception as e:
#         print(f"Error loading audio: {e}")
#
#
# if __name__ == "__main__":
#     video_url = "https://www.youtube.com/watch?v=Sr_bcwSOQqA&list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq&index=1&t=2s&ab_channel=Alejandro"
#     play_audio_from_youtube(video_url)
# import threading
# import yt_dlp
# import subprocess
# from pydub import AudioSegment
# from pydub.playback import play
# import io
# import os
# import tempfile
# import time
#
# # Global variable to hold the playback thread and stop event
# playback_thread = None
# stop_event = threading.Event()  # Event to signal stopping the playback
#
# def play_audio_from_youtube(url, volume=0.5):
#     global playback_thread, stop_event
#
#     # Stop any previous playback
#     stop_audio()
#
#     # Define yt-dlp options to get the best audio stream (audio-only)
#     ydl_opts = {
#         'format': 'bestaudio/best',  # Get best audio format
#         'outtmpl': '-',  # Don't save the file, just extract it
#         'quiet': True,
#         'noplaylist': True,  # Disable playlist extraction
#         'extractaudio': True,  # Extract audio only
#         'socket_timeout': 60,  # Increased timeout to avoid read timeouts
#         'verbose': True,  # Enable verbose output for debugging
#     }
#
#     # Download audio with yt-dlp and extract the audio stream URL
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         try:
#             info_dict = ydl.extract_info(url, download=False)
#
#             # Check all available formats and ensure we get the audio URL
#             audio_url = None
#             for format in info_dict['formats']:
#                 if format.get('vcodec') == 'none' and format.get('acodec') != 'none':  # Audio stream, no video
#                     audio_url = format['url']
#                     break
#
#             if not audio_url:
#                 print("Error: No valid audio stream found.")
#                 return
#         except Exception as e:
#             print(f"Error extracting video info: {e}")
#             return
#
#     # Use ffmpeg to directly stream and convert the audio to a playable format
#     print("Downloading and playing audio from YouTube...")
#
#     # Create a temporary file to store the audio
#     temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
#
#     # Pass the audio URL to ffmpeg and download it to a temporary file
#     command = [
#         'ffmpeg',
#         '-i', audio_url,  # Input URL
#         '-vn',  # No video
#         '-acodec', 'libmp3lame',  # Use MP3 encoding
#         '-ar', '44100',  # Sample rate
#         '-ac', '2',  # Stereo
#         temp_file.name  # Output file path
#     ]
#
#     # Run the command to download and save the audio to a file
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     stdout, stderr = process.communicate()
#
#     # If there was an error in ffmpeg, print it
#     if process.returncode != 0:
#         print(f"ffmpeg error: {stderr.decode()}")
#         return
#
#     # Function to play the audio from the temporary file
#     def play_audio():
#         try:
#             # Load audio from the temporary file
#             audio = AudioSegment.from_mp3(temp_file.name)
#
#             # Adjust the volume (0.0 to 1.0 scale)
#             audio = audio + (20 * (volume - 1))  # 1.0 means no change, 0.5 means -6 dB, etc.
#
#             # Play the audio
#             play(audio)  # Play the audio
#         except Exception as e:
#             print(f"Error loading audio: {e}")
#
#     # Create and start the playback thread
#     playback_thread = threading.Thread(target=play_audio)
#     playback_thread.start()
#
# def stop_audio():
#     global stop_event
#
#     # Set the stop flag to True if playback is ongoing
#     if playback_thread and playback_thread.is_alive():
#         stop_event.set()  # Signal the playback thread to stop
#         playback_thread.join()  # Wait for the thread to finish
#         print("Audio playback stopped.")
#     else:
#         print("No audio is currently playing.")
#
# if __name__ == "__main__":
#     video_url = "https://www.youtube.com/watch?v=Sr_bcwSOQqA&list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq&index=1&t=2s&ab_channel=Alejandro"
#     play_audio_from_youtube(video_url, volume=0.5)  # Adjust volume here
#     import time
#     time.sleep(15)  # Play for 15 seconds
#     print("Stopping music...")
#     stop_audio()


# import yt_dlp
# import subprocess
# import io
# import simpleaudio as sa
# from pydub import AudioSegment
#
# def play_audio_from_youtube(url, volume=0.5):
#     # Define yt-dlp options to get the best audio stream (audio-only)
#     ydl_opts = {
#         'format': 'bestaudio/best',  # Get best audio format
#         'outtmpl': '-',  # Don't save the file, just extract it
#         'quiet': True,
#         'noplaylist': True,  # Disable playlist extraction
#         'extractaudio': True,  # Extract audio only
#     }
#
#     # Download audio with yt-dlp and extract the audio stream URL
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info_dict = ydl.extract_info(url, download=False)
#
#         # Check all available formats and ensure we get the audio URL
#         audio_url = None
#         for format in info_dict['formats']:
#             if format.get('vcodec') == 'none' and format.get('acodec') != 'none':  # Audio stream, no video
#                 audio_url = format['url']
#                 break
#
#         if not audio_url:
#             print("Error: No valid audio stream found.")
#             return
#
#     # Use ffmpeg to directly stream and convert the audio to a playable format
#     print("Downloading and playing audio from YouTube...")
#
#     # Pass the audio URL to ffmpeg and decode the stream to an in-memory file
#     command = [
#         'ffmpeg',
#         '-i', audio_url,  # Input URL
#         '-vn',  # No video
#         '-acodec', 'pcm_s16le',  # Raw PCM audio
#         '-ar', '44100',  # Sample rate
#         '-ac', '2',  # Stereo
#         '-f', 'wav',  # Output format
#         'pipe:1'  # Output to stdout (piped)
#     ]
#
#     # Run the command and get the audio output in memory
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     stdout, stderr = process.communicate()
#
#     # If there was an error in ffmpeg, print it
#     if process.returncode != 0:
#         print(f"ffmpeg error: {stderr.decode()}")
#         return
#
#     # Use pydub to load the audio from memory and adjust volume
#     try:
#         # Load audio from memory
#         audio = AudioSegment.from_wav(io.BytesIO(stdout))
#
#         # Adjust the volume (0.0 to 1.0 scale)
#         audio = audio + (20 * (volume - 1))  # Increase or decrease by dB (1.0 = no change, 0.5 = -6 dB, etc.)
#
#         # Convert to raw audio data
#         raw_data = audio.raw_data
#
#         # Play the audio using simpleaudio
#         play_obj = sa.play_buffer(
#             raw_data,
#             num_channels=audio.channels,
#             bytes_per_sample=audio.sample_width,
#             sample_rate=audio.frame_rate
#         )
#
#         # Wait for the playback to finish
#         play_obj.wait_done()
#
#     except Exception as e:
#         print(f"Error loading or playing audio: {e}")
#
#
# if __name__ == "__main__":
#     video_url = "https://www.youtube.com/watch?v=_oAMgAkgH0Y&list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq&index=18&ab_channel=JanValtaandAdamSporka-Topic"
#     play_audio_from_youtube(video_url)
import yt_dlp
import subprocess
import io
import simpleaudio as sa
from pydub import AudioSegment
import threading

# Global variable to store the play_obj so we can stop it later
play_obj = None
playback_thread = None

def play_audio_from_youtube(url, volume=0.5):
    global play_obj, playback_thread

    # Stop any previous playback before starting new one
    stop_audio()

    # Define yt-dlp options to get the best audio stream (audio-only)
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

    # Pass the audio URL to ffmpeg and decode the stream to an in-memory file
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

    # Use pydub to load the audio from memory and adjust volume
    try:
        # Load audio from memory
        audio = AudioSegment.from_wav(io.BytesIO(stdout))

        # Adjust the volume (0.0 to 1.0 scale)
        audio = audio + (20 * (volume - 1))  # Increase or decrease by dB (1.0 = no change, 0.5 = -6 dB, etc.)

        # Convert to raw audio data
        raw_data = audio.raw_data

        # Start playback in a separate thread
        def play():
            global play_obj
            # Play the audio using simpleaudio
            play_obj = sa.play_buffer(
                raw_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate
            )
            # Wait for the audio to finish playing
            play_obj.wait_done()

        # Start playback in a separate thread to avoid blocking
        playback_thread = threading.Thread(target=play)
        playback_thread.start()

    except Exception as e:
        print(f"Error loading or playing audio: {e}")

from src.server.model import create_mistral_agent
def stop_audio():
    global play_obj, playback_thread

    if play_obj:
        # Stop the audio if it's playing
        play_obj.stop()
        print("Audio playback stopped.")
        play_obj = None

    if playback_thread and playback_thread.is_alive():
        # Wait for the playback thread to finish (in case we're manually stopping the audio)
        playback_thread.join()
        playback_thread = None
client = create_mistral_agent()
model = "mistral-large-latest"
def filter_video_by_query(video_titles, query):
    """
    This function will use Mistral to decide which video title fits the user's request.
    If Mistral finds a relevant match, it returns the corresponding video title.
    """
    # Create a prompt for Mistral to analyze the query and decide the best match
    prompt = f"Given the following video titles and the query '{query}', which video title best fits the request? Titles: {video_titles}.Return only name of hte video "

    # Send the prompt to Mistral API
    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    # Correctly access the content of the AssistantMessage object
    best_match = response.choices[0].message.content.strip()
    print(f"Mistral's suggestion: {best_match}")
    # If Mistral's response is a valid match, return it

    return best_match
import difflib
import yt_dlp
import json
if __name__ == "__main__":
    ydl_opts = {
        'format': 'bestaudio/best',  # Get best audio format
        'outtmpl': '-',  # Don't save the file, just extract it
        'quiet': True,
        'noplaylist': True,  # Disable playlist extraction
        'extractaudio': True,  # Extract audio only
    }
    playlist_url = "https://www.youtube.com/playlist?list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq"

    with open("C:\\Users\\leftg\\PycharmProjects\\Dnd_bot\\src\\utlis\\youtube_playlist.py","r") as f:
        playlist_info = json.load(f)

    video_titles = [entry[0] for entry in playlist_info]
    print(f"Found videos: {video_titles}")

    relevant_video = filter_video_by_query(video_titles, "small town music")
    print(f"Relevant video selected: '{relevant_video}'")

    if relevant_video is None:
        print("No relevant video found for the query.")

    # Normalize the relevant video title (remove spaces and lower case for comparison)
    relevant_video_normalized = relevant_video.strip().lower()
    print(f"Normalized relevant video: '{relevant_video_normalized}'")

    # Try to find the matching video URL
    match = None
    for entry in playlist_info:
        playlist_title_normalized = entry[0].strip().lower()
        if relevant_video_normalized == playlist_title_normalized:
            match = entry
            break

        if match:
            video_url = match[1]
            print(f"Found relevant video: {relevant_video} - {video_url}")
        else:
            print(f"No exact match found for '{relevant_video}'")
            # Optionally, use fuzzy matching to find the best match
            closest_match = difflib.get_close_matches(relevant_video, video_titles, n=1)
            if closest_match:
                print(f"Using closest match: {closest_match[0]}")
                video_url = next(
                    entry[1] for entry in playlist_info if entry[0] == closest_match[0])
            else:
                print("No suitable match found.")

    video_url = video_url
    play_audio_from_youtube(video_url)

    # For testing purposes, let's stop the audio after 10 seconds
    import time
    time.sleep(10)
    print("Stopping audio...")
    stop_audio()
