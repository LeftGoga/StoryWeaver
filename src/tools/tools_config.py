import functools
from src.tools.payment_tool import retrieve_payment_date,retrieve_payment_status
from src.tools.music import play_music_from_playlist,stop_audio
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
            "description": "Retrieve related chunks from the database to answer a query. Use this when you get questions.Use cases: speaks of game rules",
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
        "name": "play_music_from_playlist",
        "description": "Play certain music depending on user query. Use cases: When party enter a location, when changing a mood of scene(e.g. Started Fight)",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "user request on playing certain type of music",
                },
                "volume": {
                    "type": "integer",
                    "description": "The playback volume level (1-100). Default is 50.",
                    "default": 50,
                },
            },
            "required": ["query"],
        },
    },
},
    {
        "type": "function",
        "function": {
            "name": "stop_audio",
            "description": "Stops the music that is playing right now ",
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
        "description": "Generate a fantasy dungeon map based on specified parameters. Use cases: Entering a dungeon or any other similiar stucture",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "description": "The dungeon level (difficulty)",
                    "default": 3
                },
                "motif": {
                    "type": "string",
                    "enum": ["", "Abandoned", "Aberrant", "Giant", "Undead", "Vermin", "Aquatic", "Desert", "Underdark", "Arcane", "Fire", "Cold", "Abyssal", "Infernal"],
                    "description": "The type of dungeon",
                    "default": ""
                },
                "dungeon_size": {
                    "type": "string",
                    "enum": ["Fine", "Diminutive", "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan", "Colossal", "Custom"],
                    "description": "The size of the dungeon",
                    "default": "Medium"
                }
            }
        }
    }
}
]
names_to_functions_dict = {
    'retrieve_payment_status': functools.partial(retrieve_payment_status, df=df),
    'retrieve_payment_date': functools.partial(retrieve_payment_date, df=df),
    'retrieve_related_chunks': retrieve_related_chunks,
    'play_music_from_playlist': play_music_from_playlist,
    'stop_audio': stop_audio,
"generate_dungeon_map":  generate_dungeon_map
}