from pydub import AudioSegment
from pydub.playback import play
import asyncio
import websockets
import io

async def listen_to_agent():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri, ping_interval=None) as websocket:
        print("Connected to the server for continuous interaction. Press Ctrl+C to exit.")

        try:
            while True:
                # Wait for the server's response text
                response_text = await websocket.recv()
                print(f"Agent: {response_text}")

                # Wait for the server's audio response and play it
                audio_data = await websocket.recv()
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
                play(audio)

        except KeyboardInterrupt:
            print("Exiting the interaction...")

# Run the client
asyncio.run(listen_to_agent())
