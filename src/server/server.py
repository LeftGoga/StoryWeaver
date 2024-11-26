
from model import create_whisper_model,create_mistral_agent
from src.audio_processing.audio_processing import record_audio_for_wake_word, record_audio_until_silence, \
    text_to_speech

import websockets
from src.utlis.conversation import process_conversation

from src.configs import model_name

from src.tools.tools_config import tools_dict, names_to_functions_dict
import asyncio
music_player = None

play_obj = None
playback_thread = None


whisper_model = create_whisper_model()

tools = tools_dict
names_to_functions = names_to_functions_dict


client = create_mistral_agent()


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
    heartbeat_task = asyncio.create_task(send_custom_heartbeat(websocket))  # Heartbeat task to keep the connection alive

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

                if "met" in voice_input.replace(" ","").lower() or "mat" in voice_input.replace(" ","").lower() or "мэт" in voice_input.replace(" ","").lower() or "bad" in voice_input.replace(" ","").lower()\
                        or "mad" in voice_input.replace(" ","").lower():
                    print("Wake word detected. Recording full input...")
                    break  # Proceed to record the full input

            # Step 2: Record full input
            audio =  record_audio_until_silence()  # Record with fixed duration
            full_input = whisper_model.transcribe(audio, fp16=False)['text']
            print(f"Full input transcription: {full_input}")

            # Step 3: Process full input and interact with Mistral API
            processed_input = full_input.replace("StoryWeaver", "").strip()
            messages.append({"role": "user", "content": processed_input})
            try:

                response = await process_conversation(client, model_name, messages, tools, names_to_functions)
            except Exception as e:
                print(f"Error processing conversation: {e}")
                response = "Error processing request; please try again."

            if response in ["No-op"]:
                print("Placeholder response received; resuming listening.")
                continue  # Immediately go back to listening without TTS

            if response:  # Only send audio if there's a text response
                print(f"Sending text response: {response}")

                # Step 4: Prepare audio response
                audio_data = await text_to_speech(response)
                print("Audio response generated.")

                # Step 5: Send both responses concurrently
                try:
                    await asyncio.gather(
                        websocket.send(response),         # Send text response
                        websocket.send(audio_data)        # Send audio response
                    )
                    print("Response sent successfully.")
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"Error sending response to client: {e}. WebSocket may have closed unexpectedly.")
                    break  # Stop processing if the connection is closed
                except Exception as e:
                    print(f"Unexpected error during response send: {e}")
                    break  # Exit loop on unexpected errors

            print("Waiting for the next wake word...")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed by the client or server: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Gracefully close the WebSocket connection when the client disconnects
        print("Closing WebSocket connection.")
        try:
            await websocket.send("Closing connection.")  # Inform the client of closure
        except Exception as e:
            print(f"Error sending close message: {e}")
        await websocket.close()  # Close the WebSocket connection properly
        heartbeat_task.cancel()  # Cancel the heartbeat task
        await websocket.wait_closed()  # Ensure the WebSocket is properly closed
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