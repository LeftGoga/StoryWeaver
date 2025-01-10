import json
import time


async def process_conversation(client, model, messages, tools, names_to_functions, max_retries=5, initial_delay=2):
    retry_count = 0
    delay = initial_delay
    system_prompt = """Ты - виртуальный помощник для мастера игры DnD. Твоя задача заключается в эффективной помощи ведущему игры, используя доступные инструменты. Эти инструменты включают поиск информации, генерацию карт подземелий и подбор подходящей музыки.

# Задачи
1. **Анализировать диалог:** Принимай входящие части диалога, чтобы определять, какие инструменты наиболее полезны в контексте текущей игровой ситуации.
2. **Предлагать решения:** На основе анализа предоставляй краткие, чёткие рекомендации или действия. Ответы должны быть ёмкими, не более чем 5-6 предложений.
3. **Решение комплексных задач**: иногда потребуется использовать несколько инструментов, например для настройки сцены.

# Использование инструментов
- **Поиск информации:** Для ответов на вопросы используй инструмент `retrieve_related_chunks`. Включай как можно больше релевантной информации из контекста пользователя.
- **Генерация карт подземелий:** Аргументы в функцию `generate_dungeon_map` передавай в формате JSON. Если параметры не указаны явно, используй настройки по умолчанию, пропуская их в выходном ответе.
- **Включение музыки:** Определи подходящую музыку на основе описания сцены и настроений в диалоге.

# Формат Ответа
Рекомендации и действия в формате, понятном и удобном для восприятия ведущего.
        """
    messages.insert(0, {"role": "system", "content": system_prompt})
    processed_tool_calls = set()  # Track processed tool_call IDs

    while retry_count < max_retries:
        try:
            # Generate a response from the AI model
            response = client.chat.complete(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            messages.append(response.choices[0].message)
            print("tools: ", response.choices[0].message.tool_calls)

            # Process tool calls if present
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_call_id = tool_call.id

                    # Skip already processed tool calls
                    if tool_call_id in processed_tool_calls:
                        continue
                    processed_tool_calls.add(tool_call_id)

                    function_name = tool_call.function.name
                    print(f"Tool requested: {function_name}")

                    # Extract tool call parameters
                    function_params = json.loads(tool_call.function.arguments)

                    try:
                        if function_name in names_to_functions:
                            # Call the tool function
                            function_result = names_to_functions[function_name](**function_params)

                            # Append the tool response to messages
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps(function_result),
                                "tool_call_id": tool_call_id
                            })

                        else:
                            print(f"Unknown tool: {function_name}")
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "Error: Unknown tool",
                                "tool_call_id": tool_call_id
                            })
                    except Exception as func_error:
                        print(f"Error processing tool '{function_name}': {func_error}")
                        messages.append({
                            "role": "tool",
                            "name": function_name,
                            "content": "Error processing tool function",
                            "tool_call_id": tool_call_id
                        })

                # Make a follow-up AI response after tool calls
                response = client.chat.complete(model=model, messages=messages)
                messages.append(response.choices[0].message)
                return response.choices[0].message.content

            else:
                return response.choices[0].message.content

        except Exception as e:
            if "429" in str(e):  # Handle rate limiting
                retry_count += 1
                print(f"Rate limit hit. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"Error: {e}")
                return "Error processing request; please try again."

    return "Exceeded maximum retry attempts due to rate limiting."

if __name__ =="__main__":
    from src.server.model import create_mistral_agent
    from src.configs import model_name
    from src.tools.tools_config import tools_dict, names_to_functions_dict
    import asyncio

    async def main():
        music_player = None
        play_obj = None
        playback_thread = None

        client = create_mistral_agent()
        messages = []
        voice_input = "Вы прибываете в подземелье дракона и начинается бой"
        messages.append({"role": "user", "content": voice_input})
        tools = tools_dict
        names_to_functions = names_to_functions_dict

        answer = await process_conversation(client, model_name, messages, tools, names_to_functions)
        print(answer)


    asyncio.run(main())