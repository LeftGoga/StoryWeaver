import asyncio
import websockets
import io
from pydub import AudioSegment
from pydub.playback import play
import pygame
import io

def play_audio_with_pygame(audio_data):
    pygame.mixer.init()
    pygame.mixer.music.load(io.BytesIO(audio_data))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

async def listen_to_agent():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri, ping_interval=None) as websocket:
        print("Connected to the server for continuous interaction. Press Ctrl+C to exit.")

        try:
            while True:
                # Wait for the server's response text
                response_text = await websocket.recv()
                print(f"Agent: {response_text}")

                # Wait for the server's audio response
                audio_data = await websocket.recv()

                # Play the received audio directly (without threading)
                try:
                    play_audio_with_pygame(audio_data)
                except Exception as e:
                    print(f"Error while playing audio: {e}")
        except KeyboardInterrupt:
            print("Exiting the interaction...")

# Run the client
asyncio.run(listen_to_agent())
