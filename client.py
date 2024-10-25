import asyncio
import websockets

async def chat_with_agent():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected to the server. Type 'exit' to quit.")

        while True:
            message = input("You: ")

            if message.lower() == 'exit':
                print("Exiting chat...")
                break

            if message.lower() == 'speech':
                print("Starting speech recognition...")
                await websocket.send("start_speech_recognition")
            else:
                await websocket.send(message)

            response = await websocket.recv()
            print(f"Agent: {response}")

# Run the client
asyncio.run(chat_with_agent())
