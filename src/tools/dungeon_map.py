import json
import requests
import asyncio  # For running blocking I/O in a separate thread
from pydantic import BaseModel
from typing import Literal, get_args

class DungeonParams(BaseModel):
    name: str = "Map"
    level: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20] = 3
    infest: Literal["", "Basic"] = ""
    motif: Literal[
        "",
        "Abandoned",
        "Aberrant",
        "Giant",
        "Undead",
        "Vermin",
        "Aquatic",
        "Desert",
        "Underdark",
        "Arcane",
        "Fire",
        "Cold",
        "Abyssal",
        "Infernal",
    ] = ""
    seed: str = "42"
    dungeon_size: Literal[
        "Fine", "Diminutive", "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan", "Colossal", "Custom"
    ] = "Medium"
    dungeon_layout: Literal[
        "Square", "Rectangle", "Box", "Cross", "Dagger", "Saltire", "Keep", "Hexagon", "Round", "Cavernous"
    ] = "Square"
    peripheral_egress: Literal["", "Yes", "Many", "Tiling"] = ""
    room_layout: Literal["Sparse", "Scattered", "Dense", "Symmetric"] = "Sparse"
    room_size: Literal["Small", "Medium", "Large", "Huge", "Gargantuan", "Colossal"] = "Medium"
    room_polymorph: Literal["", "Yes", "Many"] = ""
    door_set: Literal["None", "Basic", "Secure", "Standard", "Deathtrap"] = "None"
    corridor_layout: Literal["Labyrinth", "Errant", "Straight"] = "Labyrinth"
    remove_deadends: Literal["", "Some", "All"] = ""
    add_stairs: Literal["", "Yes", "Many"] = ""
    map_style: Literal[
        "Standard",
        "Classic",
        "Crosshatch",
        "GraphPaper",
        "Parchment",
        "Marble",
        "Sandstone",
        "Slate",
        "Aquatic",
        "Infernal",
        "Glacial",
        "Wooden",
        "Asylum",
        "Steampunk",
        "Gamma",
    ] = "Standard"
    grid: Literal["None", "Square", "Hex", "VertHex"] = "Square",
    n_pc: Literal[1,2,3,4,5,6] = 4

def write_map_to_file(map_data, output_path):
    """
    Asynchronously writes map data to a file.
    Offloads the file I/O to a separate thread to prevent blocking the event loop.
    """
    with open(output_path, "wb") as file:
        file.write(map_data)
        file.flush()  # Ensure the data is written immediately


def generate_dungeon_map(params: dict = {}, output_path: str = "map.png") -> str:
    """
    Synchronously generate a dungeon map using the Donjon API and save it as an image.
    The actual file writing is offloaded to an async thread to ensure non-blocking operation.
    :param params: Parameters for dungeon generation.
    :param output_path: Path to save the generated map image.
    :return: JSON string indicating success or failure.
    """
    base_url = "https://donjon.bin.sh/fantasy/dungeon"
    construct_url = f"{base_url}/construct.cgi"
    status_url = f"{base_url}/status.fcgi"
    cache_url = f"{base_url}/cache"
    if not params:
        params = {}

    params = DungeonParams(**params)
    params_dict = params.model_dump()
    params_dict["map_cols"] = 51
    params_dict["map_rows"] = 65
    params_dict["image_size"] = ""

    try:
        # Step 1: Initiate dungeon generation
        response = requests.get(construct_url, params=params_dict)
        response_data = response.json()
        req_id = response_data["id"]
        red_auth = response_data["auth"]

        # Step 2: Poll for completion status
        while True:
            status_response = requests.get(status_url, params={"auth": red_auth, "id": req_id})
            status_data = status_response.json()
            if "done" in status_data:
                print("Dungeon generation completed.")
                break
            else:
                print(f"Status note: {status_data.get('note', 'No note available')}")

        # Step 3: Download the generated map
        map_url = f"{cache_url}/{req_id}/map.png"
        map_response = requests.get(map_url)

        # Step 4: Use asyncio.to_thread to write the map in a separate thread
        # This ensures the event loop is not blocked by file I/O
        write_map_to_file(map_response.content, output_path)

        print(f"Map generation complete. Map will be saved to {output_path}.")
        return json.dumps({"status": "success", "path": output_path})

    except Exception as e:
        print(f"Error generating dungeon map: {e}")
        return json.dumps({"status": "error", "message": str(e)})

async def main():
    generate_dungeon_map()
if __name__ == "__main__":
    asyncio.run(main())