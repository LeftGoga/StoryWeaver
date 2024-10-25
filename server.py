import pandas as pd
import json
import websockets
import asyncio
import functools
import os
import whisper  # Import Whisper for speech-to-text
import sounddevice as sd
import numpy as np
from mistralai import Mistral
from gtts import gTTS
import io

# Initialize Whisper model
whisper_model = whisper.load_model("large")  # You can also use 'small', 'medium', or 'large' based on accuracy needs

# Example data
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


# Tools definitions
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

# Bind tool functions to the dataframe
names_to_functions = {
    'retrieve_payment_status': functools.partial(retrieve_payment_status, df=df),
    'retrieve_payment_date': functools.partial(retrieve_payment_date, df=df)
}

# Mistral API setup
api_key = os.environ.get("MISTRAL_API_KEY")
model = "mistral-large-latest"
client = Mistral(api_key=api_key)


async def process_conversation(client, model, messages, tools, names_to_functions):
    print("Sending request to the model...")
    response = client.chat.complete(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    messages.append(response.choices[0].message)

    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            function_name = tool_call.function.name
            function_params = json.loads(tool_call.function.arguments)

            if function_name in names_to_functions:
                function_result = names_to_functions[function_name](**function_params)
                messages.append({"role": "tool", "name": function_name, "content": function_result, "tool_call_id": tool_call.id})

        response = client.chat.complete(model=model, messages=messages)
        messages.append(response.choices[0].message)
        return response.choices[0].message.content
    else:
        return response.choices[0].message.content


# Function to record audio using the microphone
def record_audio(duration=5, sample_rate=16000):
    print("Recording audio...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()  # Wait for the recording to complete
    audio = np.squeeze(audio)  # Remove extra dimensions
    return audio


# Function to use Whisper for speech-to-text
def recognize_speech_whisper(language='ru'):
    audio = record_audio()
    print("Processing audio with Whisper...")
    # Convert audio to the format expected by Whisper (16kHz, single-channel)
    result = whisper_model.transcribe(np.array(audio), fp16=False,language=language)
    return result['text']





async def text_to_speech(text, language="ru"):
    # Generate speech from text
    tts = gTTS(text=text, lang=language, slow=False)

    # Save the audio to a bytes buffer instead of a file
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)  # Reset buffer pointer to the beginning

    return audio_buffer.read()


async def handle_client(websocket, path):
    messages = []

    try:
        async for message in websocket:
            print(f"Received message: {message}")

            if message.startswith("speech"):
                voice_input = recognize_speech_whisper()  # Language handled by Whisper automatically
                print(f"Recognized voice input: {voice_input}")

                # Add recognized text to conversation
                messages.append({"role": "user", "content": voice_input})
                response = await process_conversation(client, model, messages, tools, names_to_functions)

                # Send text response back
                await websocket.send(response)

                # Generate audio from the response text
                audio_data = await text_to_speech(response)

                # Send the audio as a binary message
                await websocket.send(audio_data)

            else:
                messages.append({"role": "user", "content": message})
                response = await process_conversation(client, model, messages, tools, names_to_functions)

                # Send text response back
                await websocket.send(response)

                # Generate audio from the response text
                audio_data = await text_to_speech(response)

                # Send the audio as a binary message
                await websocket.send(audio_data)

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed.")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send("Server error occurred.")


async def main():
    print("WebSocket server is starting...")
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # Keep server running indefinitely


# Run the WebSocket server
asyncio.run(main())
