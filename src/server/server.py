# import sys
# import os
#
# # Add the src folder to the system path to allow imports from it
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
# import os
# print("Current working directory:", os.getcwd())
import whisper
from mistralai import Mistral
from src.audio_processing.audio_processing import record_audio_for_wake_word, record_audio_fixed_duration, \
    text_to_speech

import websockets
from src.utlis.conversation import process_conversation

from src.configs import device, whisper_model_size ,api_key,model_name
from src.tools.payment_tool import retrieve_payment_date,retrieve_payment_status
from src.tools.music import play_online_music,stop_music
from src.tools.dungeon_map import generate_dungeon_map
from src.tools.rag import retrieve_related_chunks
from src.tools.tools_config import tools_dict, names_to_functions_dict
import asyncio
music_player = None



whisper_model = whisper.load_model(whisper_model_size).to(device)

tools = tools_dict
names_to_functions = names_to_functions_dict


client = Mistral(api_key=api_key)


async def send_custom_heartbeat(websocket):
    while True:
        try:
            await websocket.ping()
            await asyncio.sleep(300)  # Every 5 minutes
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed during heartbeat.")
            break

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

                if "met" in voice_input.replace(" ","").lower() or "mat" in voice_input.replace(" ","").lower()or "мэт" in voice_input.replace(" ","").lower():
                    print("Wake word detected. Recording full input...")
                    break  # Proceed to record the full input

            # Step 2: Record full input
            audio = record_audio_fixed_duration(duration=10)  # Record with fixed duration
            full_input = whisper_model.transcribe(audio, fp16=False)['text']
            print(f"Full input transcription: {full_input}")

            # Step 3: Process full input and interact with Mistral API
            processed_input = full_input.replace("StoryWeaver", "").strip()
            messages.append({"role": "user", "content": processed_input})
            response = await process_conversation(client, model_name, messages, tools, names_to_functions)
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