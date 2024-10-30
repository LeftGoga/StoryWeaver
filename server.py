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
import time

# Initialize Whisper model
whisper_model = whisper.load_model("large")

data = {
    'transaction_id': ['T1001', 'T1002', 'T1003', 'T1004', 'T1005'],
    'customer_id': ['C001', 'C002', 'C003', 'C002', 'C001'],
    'payment_amount': [125.50, 89.99, 120.00, 54.30, 210.20],
    'payment_date': ['2021-10-05', '2021-10-06', '2021-10-07', '2021-10-05', '2021-10-08'],
    'payment_status': ['Paid', 'Unpaid', 'Paid', 'Paid', 'Pending']
}

df = pd.DataFrame(data)

def retrieve_payment_status(df: pd.DataFrame, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'status': df[df.transaction_id == transaction_id].payment_status.item()})
    return json.dumps({'error': 'transaction id not found.'})

def retrieve_payment_date(df: pd.DataFrame, transaction_id: str) -> str:
    if transaction_id in df.transaction_id.values:
        return json.dumps({'date': df[df.transaction_id == transaction_id].payment_date.item()})
    return json.dumps({'error': 'transaction id not found.'})

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
    }
]

names_to_functions = {
    'retrieve_payment_status': functools.partial(retrieve_payment_status, df=df),
    'retrieve_payment_date': functools.partial(retrieve_payment_date, df=df)
}

api_key = os.environ.get("MISTRAL_API_KEY")
model = "mistral-large-latest"
client = Mistral(api_key=api_key)


async def process_conversation(client, model, messages, tools, names_to_functions):
    try:
        # Direct call without await, as before
        response = client.chat.complete(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        messages.append(response.choices[0].message)

        # Handle tool calls if any
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                function_params = json.loads(tool_call.function.arguments)

                if function_name in names_to_functions:
                    function_result = names_to_functions[function_name](**function_params)
                    messages.append({"role": "tool", "name": function_name, "content": function_result,
                                     "tool_call_id": tool_call.id})

            # Second response after tool call
            response = client.chat.complete(model=model, messages=messages)
            messages.append(response.choices[0].message)
            return response.choices[0].message.content
        else:
            return response.choices[0].message.content

    except Exception as e:
        error_message = str(e)
        print(f"Error in conversation processing: {error_message}")

        # Check if the error indicates rate limiting or an API limit
        if "rate limit" in error_message.lower() or "too many requests" in error_message.lower():
            print("Rate limit error encountered with Mistral API. Consider reducing request frequency.")
            time.sleep(2)  # Wait briefly before the next request attempt
        elif "server error" in error_message.lower() or "unavailable" in error_message.lower():
            print("Server-side error with Mistral API. Retrying might resolve this.")
            time.sleep(2)
        else:
            print("Unhandled error occurred.")

        return "Error processing request; please try again."

def record_audio(duration=5, sample_rate=16000):
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    return np.squeeze(audio)

def recognize_speech_whisper(language='ru'):
    print("Recording audio...")
    audio = record_audio()
    print("Processing audio with Whisper...")
    result = whisper_model.transcribe(np.array(audio), fp16=False, language=language)
    print(f"Transcription result: {result['text']}")
    return result['text']

async def text_to_speech(text, language="ru"):
    tts = gTTS(text=text, lang=language, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()

async def handle_client(websocket, path):
    messages = []
    retries = 3
    retry_delay = 5  # seconds

    async def send_custom_heartbeat(websocket):
        while True:
            try:
                await websocket.ping()
                print("Custom ping sent to keep connection alive.")
                await asyncio.sleep(300)  # Every 5 minutes
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed during custom heartbeat.")
                break
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break
    heartbeat_task = asyncio.create_task(send_custom_heartbeat(websocket))

    try:
        while retries > 0:
            try:
                message = await websocket.recv()
                print(f"Received message: {message}")

                if message.startswith("speech"):
                    voice_input = recognize_speech_whisper()
                    messages.append({"role": "user", "content": voice_input})
                    response = await process_conversation(client, model, messages, tools, names_to_functions)

                    await websocket.send(response)
                    audio_data = await text_to_speech(response)
                    await websocket.send(audio_data)

                else:
                    messages.append({"role": "user", "content": message})
                    response = await process_conversation(client, model, messages, tools, names_to_functions)

                    await websocket.send(response)
                    audio_data = await text_to_speech(response)
                    await websocket.send(audio_data)

                retries = 3  # Reset retries on success

            except websockets.exceptions.ConnectionClosedError as e:
                retries -= 1
                print(f"Connection closed unexpectedly: {e}, retrying... attempts left: {retries}")
                if retries == 0:
                    print("Retries exhausted; closing connection.")
                    break
                await asyncio.sleep(retry_delay)  # Delay before retry

            except Exception as e:
                print(f"Error during message processing: {e}")
                await websocket.send("Server error occurred.")
    finally:
        heartbeat_task.cancel()
        await websocket.wait_closed()
        print("Client connection fully closed.")

async def main():
    while True:
        try:
            print("Starting WebSocket server...")
            async with websockets.serve(
                handle_client, "localhost", 8765, ping_interval=None
            ):
                await asyncio.Future()  # Keep server running indefinitely
        except Exception as e:
            print(f"Server encountered an error: {e}. Restarting in 10 seconds...")
            await asyncio.sleep(10)  # Delay before restarting
asyncio.run(main())
