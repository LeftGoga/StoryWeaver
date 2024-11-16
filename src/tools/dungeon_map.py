import requests
import time
import json
import aiofiles
async def generate_dungeon_map(params: dict, output_path: str = "map.png") -> None:
    """
    Генерация карт с помощью dinjon.su
    :param params:
    :param output_path:
    :return:
    """
    url = "https://donjon.bin.sh/fantasy/dungeon/construct.cgi"

    params_dict = params#.model_dump()
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
    async with aiofiles.open(output_path, "wb") as f:
        await f.write(image.content)
    return json.dumps({"status": "no-op"})