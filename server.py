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
import time

# Initialize Whisper model

device = "cuda"if torch.cuda.is_available() else "cpu"
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
        return json.dumps({"chunks": response.json()})
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
    }

]

names_to_functions = {
    'retrieve_payment_status': functools.partial(retrieve_payment_status, df=df),
    'retrieve_payment_date': functools.partial(retrieve_payment_date, df=df),
    'retrieve_related_chunks': functools.partial(retrieve_related_chunks)
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

import time


async def process_conversation(client, model, messages, tools, names_to_functions, max_retries=5, initial_delay=2):
    retry_count = 0
    delay = initial_delay

    # Add a system instruction to prioritize retrieved data
    messages.insert(0, {
        "role": "system",
        "content": "Use only the 'Relevant Information' provided to answer the question. If there isn't enough information, indicate that more data is needed."
    })

    while retry_count < max_retries:
        try:
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
                    print(f"Tool requested: {function_name}")  # Debug tool name
                    function_params = json.loads(tool_call.function.arguments)

                    if function_name in names_to_functions:
                        try:
                            # Call the appropriate tool function
                            function_result = names_to_functions[function_name](**function_params)
                            result_data = json.loads(function_result)

                            # If retrieving related chunks, add only the top 3 as context
                            if function_name == "retrieve_related_chunks" and "chunks" in result_data:
                                top_chunks = "\n".join(
                                    chunk['description'] if isinstance(chunk, dict) and 'description' in chunk else str(chunk)
                                    for chunk in result_data["chunks"][:3]
                                )
                                # Append context for assistant response
                                messages.append({
                                    "role": "tool",
                                    "name": function_name,
                                    "content": f"Relevant Information:\n{top_chunks}",
                                    "tool_call_id": tool_call.id
                                })
                            else:
                                # Add regular tool result
                                messages.append({
                                    "role": "tool",
                                    "name": function_name,
                                    "content": function_result,
                                    "tool_call_id": tool_call.id
                                })

                        except Exception as func_error:
                            print(f"Error processing tool '{function_name}': {func_error}")
                            # Append an error message for the tool result to keep the count consistent
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "Error processing tool function",
                                "tool_call_id": tool_call.id
                            })

                # Generate a final response after adding all tool outputs
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


async def text_to_speech(text, language="ru"):
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


def record_audio_fixed_duration(duration=10, sample_rate=16000):
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

                if "amy" in voice_input.replace(" ","").lower() or "Эйми" in voice_input.replace(" ","").lower():
                    print("Wake word detected. Recording full input...")
                    break  # Proceed to record the full input

            # Step 2: Record full input
            audio = record_audio_fixed_duration(duration=10)  # Record with fixed duration
            full_input = whisper_model.transcribe(audio, fp16=False)['text']
            print(f"Full input transcription: {full_input}")

            # Step 3: Process full input and interact with Mistral API
            processed_input = full_input.replace("StoryWeaver", "").strip()
            messages.append({"role": "user", "content": processed_input})
            response = await process_conversation(client, model, messages, tools, names_to_functions)

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