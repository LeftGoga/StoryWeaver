import yt_dlp
import json


def download_playlist_info(playlist_url, output_file='playlist_info.json'):
    # Create a yt-dlp options dictionary
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # To avoid downloading videos, just fetch metadata
    }

    # Create a downloader object
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract the playlist information
        info_dict = ydl.extract_info(playlist_url, download=False)

        # Check if the URL is a playlist
        if 'entries' not in info_dict:
            print("Error: Provided URL is not a valid playlist.")
            return

        # List to hold video info
        video_list = []

        # Extract relevant info for each video
        for entry in info_dict['entries']:
            video_name = entry.get('title', 'Unknown Title')
            video_url = entry.get('url', 'Unknown URL')
            video_list.append([video_name, video_url])

        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(video_list, json_file, ensure_ascii=False, indent=4)

        print(f"Playlist info has been saved to {output_file}")


# Example Usage:
playlist_url = "https://www.youtube.com/playlist?list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq"
download_playlist_info(playlist_url)