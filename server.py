import pandas as pd
import json
import websockets
import asyncio
import functools
import os
import whisper
import sounddevice as sd
import numpy as np
from mistralai import Mistral
from gtts import gTTS
import io
import torch
import requests
import vlc
import yt_dlp

import time

# Initialize Whisper model

device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)
whisper_model = whisper.load_model("medium").to(device)
print(f"Model device: {next(whisper_model.parameters()).device}")

data = {
    'transaction_id': ['1', 'T1002', 'T1003', 'T1004', 'T1005'],
    'customer_id': ['C001', 'C002', 'C003', 'C002', 'C001'],
    'payment_amount': [125.50, 89.99, 120.00, 54.30, 210.20],
    'payment_date': ['2021-10-05', '2021-10-06', '2021-10-07', '2021-10-05', '2021-10-08'],
    'payment_status': ['Paid', 'Unpaid', 'Paid', 'Paid', 'Pending']
}

df = pd.DataFrame(data)


# Global variable to store the player instance for stopping
music_player = None


music_player = None

def play_online_music(mood: str, volume: int = 50):
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

    # Create and start a new player instance
    instance = vlc.Instance("--no-video")
    music_player = instance.media_player_new()
    media = instance.media_new(audio_url)
    music_player.set_media(media)
    music_player.audio_set_volume(volume)
    music_player.play()
    print("Music started.")
    return "..."  # Suppress response

def stop_music():
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


def retrieve_payment_status(df: pd.DataFrame, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'status': df[df.transaction_id == transaction_id].payment_status.item()})
    return json.dumps({'error': 'transaction id not found.'})

def retrieve_payment_date(df: pd.DataFrame, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'date': df[df.transaction_id == transaction_id].payment_date.item()})
    return json.dumps({'error': 'transaction id not found.'})

def retrieve_related_chunks(query: str) -> str:
    url = "http://213.139.208.158:8000/search"
    params = {
        "query": query,
        "search_type": "embedding"  # or "fulltext" if preferred
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        chunks = response.json()[:3]
        print(chunks)
        return json.dumps({"chunks": chunks})
    else:
        return json.dumps({"error": f"API request failed with status code {response.status_code}"})

tools = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_payment_status",
            "description": "Get payment status of a transaction",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The transaction id.",
                    }
                },
                "required": ["transaction_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_payment_date",
            "description": "Get payment date of a transaction",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The transaction id.",
                    }
                },
                "required": ["transaction_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_related_chunks",
            "description": "Retrieve related chunks from the database to answer a query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search in the database.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "play_online_music",
            "description": "Play mood-specific background music from YouTube",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The type of music mood, e.g., 'ambient', 'action', 'mystery'.",
                    }
                },
                "required": ["mood"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_music",
            "description": "Выключает музыку которая играет сейчас",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]
names_to_functions = {
    'retrieve_payment_status': functools.partial(retrieve_payment_status, df=df),
    'retrieve_payment_date': functools.partial(retrieve_payment_date, df=df),
    'retrieve_related_chunks': functools.partial(retrieve_related_chunks),
    'play_online_music': play_online_music,
    'stop_music': stop_music
}


api_key = os.environ.get("MISTRAL_API_KEY")
model = "mistral-large-latest"
client = Mistral(api_key=api_key)

def record_audio(duration=5, sample_rate=16000):
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    return np.squeeze(audio)

def recognize_speech_whisper(language='ru'):
    print("Listening...")
    audio = record_audio()
    print("Processing audio with Whisper...")
    result = whisper_model.transcribe(np.array(audio), fp16=True, language=language)
    print(f"Transcription result: {result['text']}")
    return result['text']


async def process_conversation(client, model, messages, tools, names_to_functions, max_retries=5, initial_delay=2):
    retry_count = 0
    delay = initial_delay
    system_prompt = """Ты - помощник ведущего настольно-ролевой игры. Твоя задача помогать ведущему с помощью инструментов.
        В своих ответах будь краток - 5-6 предложений. Если тебя просят включить или выключить музыку-В ответ скажи no-op.
        Для ответов на вопросы используй инструмент retrieve_related_chunks
        """
    messages.insert(0, {
        "role": "system",
        "content": system_prompt
    })

    while retry_count < max_retries:
        try:
            # Initial response from Mistral with tool selection

            response = client.chat.complete(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            messages.append(response.choices[0].message)

            # Tool processing
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    print(f"Tool requested: {function_name}")

                    # Handle music commands locally and skip Mistral response for these cases
                    if function_name in ["play_online_music", "stop_music"]:
                        function_params = json.loads(tool_call.function.arguments)
                        names_to_functions[function_name](**function_params)
                        print(f"Processed {function_name} locally with result: Success")
                        messages.append({
                            "role": "tool",
                            "name": function_name,
                            "content": "Music command processed."
                        })
                        continue

                    # Process other tool calls as normal
                    function_params = json.loads(tool_call.function.arguments)
                    if function_name in names_to_functions:
                        try:
                            function_result = names_to_functions[function_name](**function_params)
                            result_data = json.loads(function_result)

                            if function_name == "retrieve_related_chunks" and "chunks" in result_data:
                                top_chunks = "\n".join(
                                    chunk['description'] if isinstance(chunk, dict) and 'description' in chunk else str(chunk)
                                    for chunk in result_data["chunks"][:3]
                                )
                                messages.append({
                                    "role": "tool",
                                    "name": function_name,
                                    "content": f"Relevant Information:\n{top_chunks}",
                                    "tool_call_id": tool_call.id
                                })
                            else:
                                messages.append({
                                    "role": "tool",
                                    "name": function_name,
                                    "content": function_result,
                                    "tool_call_id": tool_call.id
                                })

                        except Exception as func_error:
                            print(f"Error processing tool '{function_name}': {func_error}")
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "Error processing tool function",
                                "tool_call_id": tool_call.id
                            })

                # Only request a new Mistral completion for non-music tools
                response = client.chat.complete(model=model, messages=messages)
                messages.append(response.choices[0].message)
                return response.choices[0].message.content
            else:
                return response.choices[0].message.content

        except Exception as e:
            if "429" in str(e):  # Handle rate limiting
                retry_count += 1
                print(f"Rate limit hit. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"Error: {e}")
                return "Error processing request; please try again."

    return "Exceeded maximum retry attempts due to rate limiting."

def generate_silent_audio(duration=1):
    # Creates a silent audio file of the specified duration in seconds
    sample_rate = 16000  # Example rate
    num_samples = duration * sample_rate
    silent_audio = np.zeros(num_samples, dtype=np.float32)
    audio_bytes = silent_audio.tobytes()  # Convert to bytes for sending
    return audio_bytes

async def text_to_speech(text, language="ru"):
    if "No-op" in text:
        print("Ignoring placeholder response for text-to-speech.")
        return generate_silent_audio(duration=1)
    tts = gTTS(text=text, lang=language, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()

def record_audio_for_wake_word(duration=2, sample_rate=16000, threshold=0.03):
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    audio = np.squeeze(audio)

    # Check if there is sufficient sound level to consider this as an actual wake word attempt
    if np.max(np.abs(audio)) < threshold:
        print("Wake word not detected (sound level too low). Waiting...")
        return None

    return audio


def record_audio_fixed_duration(duration=5, sample_rate=16000):
    print("Recording input after wake word...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    return np.squeeze(audio)

# Function to detect wake word and proceed only when it is detected
async def handle_client(websocket, path):
    messages = []
    heartbeat_task = asyncio.create_task(send_custom_heartbeat(websocket))

    try:
        while True:
            # Step 1: Wait for the wake word
            print("Listening for the wake word 'StoryWeaver'...")

            while True:
                audio = record_audio_for_wake_word(duration=2)  # Short listening for wake word detection
                if audio is None:
                    continue  # No significant audio detected, continue listening

                # Transcribe and check for wake word
                voice_input = whisper_model.transcribe(audio, fp16=False)['text']
                print(f"Transcription for wake word detection: {voice_input}")

                if "met" in voice_input.replace(" ","").lower() or "mat" in voice_input.replace(" ","").lower():
                    print("Wake word detected. Recording full input...")
                    break  # Proceed to record the full input

            # Step 2: Record full input
            audio = record_audio_fixed_duration(duration=5)  # Record with fixed duration
            full_input = whisper_model.transcribe(audio, fp16=False)['text']
            print(f"Full input transcription: {full_input}")

            # Step 3: Process full input and interact with Mistral API
            processed_input = full_input.replace("StoryWeaver", "").strip()
            messages.append({"role": "user", "content": processed_input})
            response = await process_conversation(client, model, messages, tools, names_to_functions)
            if response in ["No-op"]:
                print("Placeholder response received; resuming listening.")
                continue  # Immediately go back to listening without TTS

            if response:  # Only send audio if there's a text response
                print(f"Sending text response: {response}")

                # Step 4: Prepare audio response
                audio_data = await text_to_speech(response)
                print("Audio response generated.")

                # Step 5: Send both responses concurrently
                await asyncio.gather(
                    websocket.send(response),         # Send text response
                    websocket.send(audio_data)        # Send audio response
                )

            print("Response sent successfully. Waiting for the next wake word...")

    finally:
        heartbeat_task.cancel()
        await websocket.wait_closed()
        print("Client connection fully closed.")

async def send_custom_heartbeat(websocket):
    while True:
        try:
            await websocket.ping()
            await asyncio.sleep(300)  # Every 5 minutes
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed during heartbeat.")
            break
# Main server loop remains unchanged

async def main():
    print("Starting WebSocket server...")
    while True:
        try:
            async with websockets.serve(handle_client, "localhost", 8765, ping_interval=None):
                await asyncio.Future()
        except Exception as e:
            print(f"Server error: {e}. Restarting in 10 seconds...")
            await asyncio.sleep(10)

asyncio.run(main())