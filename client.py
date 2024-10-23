import asyncio
import websockets

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

            # Wait for response from the server
            response = await websocket.recv()
            print(f"Agent: {response}")

# Run the client
asyncio.run(chat_with_agent())