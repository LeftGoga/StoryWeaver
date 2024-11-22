import requests
import time
from pydantic import BaseModel
from typing import Literal, get_args


class DungeonParams(BaseModel):
    name: str
    level: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    infest: Literal["", "Basic"]
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
    ]
    seed: str
    dungeon_size: Literal[
        "Fine", "Diminutive", "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan", "Colossal", "Custom"
    ]
    dungeon_layout: Literal[
        "Square", "Rectangle", "Box", "Cross", "Dagger", "Saltire", "Keep", "Hexagon", "Round", "Cavernous"
    ]
    peripheral_egress: Literal["", "Yes", "Many", "Tiling"]
    room_layout: Literal["Sparse", "Scattered", "Dense", "Symmetric"]
    room_size: Literal["Small", "Medium", "Large", "Huge", "Gargantuan", "Colossal"]
    room_polymorph: Literal["", "Yes", "Many"]
    door_set: Literal["None", "Basic", "Secure", "Standard", "Deathtrap"]
    corridor_layout: Literal["Labyrinth", "Errant", "Straight"]
    remove_deadends: Literal["", "Some", "All"]
    add_stairs: Literal["", "Yes", "Many"]
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
    ]
    grid: Literal["None", "Square", "Hex", "VertHex"]


def generate_dungeon_map(params: DungeonParams, output_path: str = "map.png") -> None:

    url = "https://donjon.bin.sh/fantasy/dungeon/construct.cgi"

    params_dict = params.model_dump()
    params_dict["n_pc"] = 4
    params_dict["map_cols"] = 51
    params_dict["map_rows"] = 65
    params_dict["image_size"] = ""

    response = requests.get(url, params=params_dict)
    req_id = response.json()["id"]
    red_auth = response.json()["auth"]

    while True:
        status = requests.get(f"https://donjon.bin.sh/fantasy/dungeon/status.fcgi?auth={red_auth}&id={req_id}")
        time.sleep(1)
        if "done" in status.json():
            print("Done")
            break

        try:
            print(status.json()["note"])
        except Exception as e:
            print(e)

    image = requests.get(f"https://donjon.bin.sh/fantasy/dungeon/cache/{req_id}/map.png")
    with open(output_path, "wb") as f:
        f.write(image.content)


def print_dungeon_params_options():
    for field_name, field in DungeonParams.model_fields.items():
        if hasattr(field.annotation, "__args__"):
            values = get_args(field.annotation)
            print(f"\n{field_name}:")
            for value in values:
                print(f"  - {value}")
        else:
            print(f"\n{field_name}:")
            print(f"  - Type: {field.annotation}")


if __name__ == "__main__":

    params = DungeonParams(
        name="The Delve of Testing",
        level=10,
        infest="",
        motif="",
        seed="1186108665",
        dungeon_size="Large",
        dungeon_layout="Rectangle",
        peripheral_egress="Many",
        room_layout="Scattered",
        room_size="Large",
        room_polymorph="Yes",
        door_set="Standard",
        corridor_layout="Straight",
        remove_deadends="Some",
        add_stairs="",
        map_style="Standard",
        grid="Square",
    )

    print("\nAvailable parameter options:")
    print_dungeon_params_options()

    generate_dungeon_map(params)
