import pandas as pd
import json
import websockets
import asyncio
import functools
import os
from mistralai import Mistral

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
    # Request response from the model
    print("Sending request to the model...")
    response = client.chat.complete(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto"  # Try enforcing the tool usage
    )

    # Debug: Print full response
    print("Raw API response:", response)

    # Add model response to messages
    messages.append(response.choices[0].message)

    # Process tool calls
    if response.choices[0].message.tool_calls:
        print("Tool call(s) detected...")

        # Handle each tool call
        for tool_call in response.choices[0].message.tool_calls:
            function_name = tool_call.function.name
            function_params = json.loads(tool_call.function.arguments)

            # Execute the corresponding tool
            if function_name in names_to_functions:
                function_result = names_to_functions[function_name](**function_params)
                print(f"Tool '{function_name}' result:", function_result)

                # Add the tool result back to messages
                messages.append(
                    {"role": "tool", "name": function_name, "content": function_result, "tool_call_id": tool_call.id})

        # After processing tool calls, send the conversation back to the model
        print("Sending updated conversation to the model...")
        response = client.chat.complete(
            model=model,
            messages=messages
        )
        messages.append(response.choices[0].message)
        print("Final response:", response.choices[0].message.content)
        return response.choices[0].message.content
    else:
        print("No tool call found.")
        return response.choices[0].message.content


async def handle_client(websocket, path):
    # Initial message list
    messages = []

    try:
        async for message in websocket:
            print(f"Received message: {message}")

            # Add user message to conversation
            messages.append({"role": "user", "content": message})

            # Process the conversation with the model
            response = await process_conversation(client, model, messages, tools, names_to_functions)

            # Send back the final model response to the WebSocket client
            await websocket.send(response)
            # The connection should stay open to process additional messages
            print("Message processed, connection still open.")

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed by client.")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send("An error occurred on the server side. Connection remains open.")




async def main():
    print("WebSocket server is starting...")
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever


# Run the WebSocket server
asyncio.run(main())
