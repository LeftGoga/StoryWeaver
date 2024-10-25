from pydub import AudioSegment
from pydub.playback import play
import asyncio
import websockets
import io

async def chat_with_agent():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected to the server. Type 'exit' to quit.")

        while True:
            # Take user input
            message = input("You: ")

            if message.lower() == 'exit':
                print("Exiting the chat...")
                break

            # Send message to the server
            await websocket.send(message)

            # Wait for response from the server (first text, then audio)
            response = await websocket.recv()
            print(f"Agent: {response}")

            # Receive the audio response (binary data) and play it
            audio_data = await websocket.recv()
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            play(audio)

# Run the client
asyncio.run(chat_with_agent())