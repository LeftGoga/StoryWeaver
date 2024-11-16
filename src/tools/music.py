import json
import vlc
import yt_dlp

music_player = None

def play_online_music(mood: str, volume: int = 50):

    """
    Играет музыку с ютьба, если включается еще один трек пока играет - следующий не включается
    :param mood:
    :param volume:
    :return:
    """
    global music_player
    # Check if music is already playing
    if music_player is not None and music_player.is_playing():
        print("Music is already playing. Skipping new track.")
        return ""  # Prevent Mistral response

    search_query = f"{mood} music soundtrack"
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'default_search': 'ytsearch',
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_query, download=False)
            if info and 'entries' in info and info['entries']:
                audio_url = info['entries'][0].get('url')
                if not audio_url:
                    print("No audio URL found in the first entry.")
                    return "..."  # Suppress response
            else:
                print("No entries found in search results.")
                return ".."  # Suppress response
        except Exception as e:
            print(f"Error retrieving audio URL: {e}")
            return json.dumps({"error": str(e)})
    instance = vlc.Instance("--no-video")
    music_player = instance.media_player_new()
    media = instance.media_new(audio_url)
    music_player.set_media(media)
    music_player.audio_set_volume(volume)
    music_player.play()
    print("Music started.")
    return "..."  # Suppress response

def stop_music():
    "стопает играющую музыку"
    global music_player
    if music_player is not None:
        # Stop playback and release resources
        music_player.stop()
        music_player.release()
        music_player = None  # Clear reference to ensure no residual playback
        print("Music stopped.")
    else:
        print("No music is currently playing.")
    return "..."  # Suppress response