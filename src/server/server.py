import websockets
import asyncio
import time

from model import create_whisper_model,create_mistral_agent
from src.configs import model_name
from src.utlis.conversation import process_conversation

from src.audio_processing.audio_processing import record_audio_for_wake_word,text_to_speech
from src.tools.tools_config import tools_dict, names_to_functions_dict


music_player = None
play_obj = None
playback_thread = None


whisper_model = create_whisper_model()
client = create_mistral_agent()

tools = tools_dict
names_to_functions = names_to_functions_dict




async def send_custom_heartbeat(websocket):
    while True:
        try:
            await websocket.ping()
            await asyncio.sleep(300)  # Every 5 minutes
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed during heartbeat.")
            break

async def handle_client(websocket, path):
    messages = []
    heartbeat_task = asyncio.create_task(send_custom_heartbeat(websocket))
    
    try:
        while True:
            # Записываем аудио в течение 15 секунд
            print("Слушаю разговор...")
            audio = record_audio_for_wake_word(duration=15)
            
            if audio is None:
                continue
                
            # Транскрибируем записанный отрезок
            voice_input = whisper_model.transcribe(audio, fp16=False)['text']
            print(f"Записанный текст: {voice_input}")
            check_prompt = f"""Ты — многофункциональный помощник для ведущего и игроков в Dungeons & Dragons (DnD). Твоя цель — анализировать транскрибированные текстовые отрывки из диалогов участника (или участников) партии и определять, требует ли такое взаимодействие дальнейшего внимания и действия основного агента. Твои основные задачи, которые могут требовать вмешательства, включают:

1. **Объяснение правил игры**: Когда обсуждаются механики игры, такие как броски кубиков, использование заклинаний или уникальные особенности классов и навыков, ты должен определить, если это уместно.
2. **Генерация карты**: Если в диалоге обсуждается необходимость создания визуализации сцены, к примеру, для сражения, подземелья или города, твое вмешательство может понадобиться.
3. **Включение музыки**: Если обсуждается новое место действия или выражается изменение в атмосфере или характере сцены, стоит задуматься о сопровождении музыкой для создания соответствующего настроения.
4. **Настройка сцены**: когда тебя просят создать сцену, используй комбинации предыдущих инструментов, каких как: включение музыки, создание карты, объяснения правил. Не обязательно использовать все, решай сам что может понадобится.
Каждый раз, когда ты анализируешь текстовый отрывок, оценивай только требует ли он твоего вмешательства согласного вышеописанным сценариям. Используй предоставленный текстовой отрывок из разговора участников партии для анализа: {voice_input}.

Отвечай только "да" или "нет", в зависимости от того, уместно ли твоё вмешательство в контексте текущего обсуждения."""


            # Отправляем текст Mistral для проверки необходимости вмешательства
            check_message = {"role": "user", "content": check_prompt}
            response = client.chat.complete(model="mistral-small-latest", messages=[check_message])
            time.sleep(2)
            should_intervene = response.choices[0].message.content.lower()
            print(should_intervene )
            if "да" in should_intervene:
                print("Mistral решил вмешаться в разговор")
                messages.append({"role": "user", "content": voice_input})
                
                try:
                    response = await process_conversation(client, model_name, messages, tools, names_to_functions)
                except Exception as e:
                    print(f"Ошибка обработки диалога: {e}")
                    response = "Произошла ошибка, попробуйте еще раз."
                    
                if len(messages) > 10:
                    messages = messages[-10:]
                    
                if response in ["No-op"]:
                    print("Получен пустой ответ, продолжаю слушать.")
                    continue

                if response:
                    print(f"Отправляю текстовый ответ: {response}")
                    audio_data = await text_to_speech(response)
                    print("Аудио ответ сгенерирован.")

                    try:
                        await asyncio.gather(
                            websocket.send(response),
                            websocket.send(audio_data)
                        )
                        print("Ответ успешно отправлен.")
                    except websockets.exceptions.ConnectionClosed as e:
                        print(f"Ошибка отправки ответа клиенту: {e}")
                        break
                    except Exception as e:
                        print(f"Неожиданная ошибка при отправке: {e}")
                        break
            else:
                print("Mistral решил не вмешиваться, продолжаю слушать...")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Соединение закрыто клиентом или сервером: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
    finally:
        print("Закрываю WebSocket соединение.")
        try:
            await websocket.send("Закрываю соединение.")
        except Exception as e:
            print(f"Ошибка отправки сообщения о закрытии: {e}")
        await websocket.close()
        heartbeat_task.cancel()
        await websocket.wait_closed()
        print("Соединение с клиентом полностью закрыто.")

async def main():
    print("Запуск WebSocket сервера...")
    while True:
        try:
            async with websockets.serve(handle_client, "localhost", 8765, ping_interval=None):
                await asyncio.Future()
        except Exception as e:
            print(f"Ошибка сервера: {e}. Перезапуск через 10 секунд...")
            await asyncio.sleep(10)

asyncio.run(main())