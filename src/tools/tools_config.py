import functools
from src.tools.payment_tool import retrieve_payment_date,retrieve_payment_status
from src.tools.music import play_online_music,stop_music
from src.tools.dungeon_map import generate_dungeon_map
import pandas as pd

from tools.rag import retrieve_related_chunks

data = {
    'transaction_id': ['1', 'T1002', 'T1003', 'T1004', 'T1005'],
    'customer_id': ['C001', 'C002', 'C003', 'C002', 'C001'],
    'payment_amount': [125.50, 89.99, 120.00, 54.30, 210.20],
    'payment_date': ['2021-10-05', '2021-10-06', '2021-10-07', '2021-10-05', '2021-10-08'],
    'payment_status': ['Paid', 'Unpaid', 'Paid', 'Paid', 'Pending']
}

df = pd.DataFrame(data)

tools_dict = [
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
    },
    {
        "type": "function",
        "function": {
            "name": "play_online_music",
            "description": "Play mood-specific background music from YouTube",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The type of music mood, e.g., 'ambient', 'action', 'mystery'.",
                    }
                },
                "required": ["mood"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_music",
            "description": "Выключает музыку которая играет сейчас",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
{
    "type": "function",
    "function": {
        "name": "generate_dungeon_map",
        "description": "Generate a fantasy dungeon map based on specified parameters",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "description": "The dungeon level (difficulty)"},
                "motif": {"type": "string", "enum": [
        "","Abandoned","Aberrant","Giant","Undead","Vermin","Aquatic","Desert","Underdark","Arcane","Fire","Cold","Abyssal","Infernal",], "description": "The type of dungeon"},
                "dungeon_size": {"type": "string", "enum": ["Fine", "Diminutive", "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan", "Colossal", "Custom"], "description": "The size of the dungeon"},
            },
            "required": ["level", "dungeon_type", "size"],
        },
    },
}
]
names_to_functions_dict = {
    'retrieve_payment_status': functools.partial(retrieve_payment_status, df=df),
    'retrieve_payment_date': functools.partial(retrieve_payment_date, df=df),
    'retrieve_related_chunks': functools.partial(retrieve_related_chunks),
    'play_online_music': play_online_music,
    'stop_music': stop_music,
"generate_dungeon_map":  generate_dungeon_map
}