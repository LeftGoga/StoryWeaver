import json
import time
import asyncio
async def process_conversation(client, model, messages, tools, names_to_functions, max_retries=5, initial_delay=2):
    retry_count = 0
    delay = initial_delay
    system_prompt = """Ты - помощник ведущего настольно-ролевой игры. Твоя задача помогать ведущему с помощью инструментов.
        Тебе будет подаваться отрывки из игрового диалогА, тебе придется проанализировать его и понять, какие инструменты надо применить.
        В своих ответах будь как можно более краток - не более 5-6 предложений. 
        Для ответов на вопросы используй инструмент retrieve_related_chunks, подавай в запрос больше информации от пользователя.
        В функцию generate_dungeon_map передавай аргументы json-ом, Если пользователь не указал параметры, бери по параметры умолчанию 
        которые не указал пользователь, просто не включай их в ответ
        """
    messages.insert(0, {
        "role": "system",
        "content": system_prompt
    })#переделать чтобы было ограниченный контекст сообщений

    while retry_count < max_retries:
        try:
            # Initial response from Mistral with tool selection

            response = client.chat.complete(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            messages.append(response.choices[0].message)
            print("tools: ", response.choices[0].message.tool_calls)
            # Tool processing
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    print(f"Tool requested: {function_name}")

                    # Handle music commands locally and skip Mistral response for these cases


                    # Process other tool calls as normal
                    function_params = json.loads(tool_call.function.arguments)
                    print("func_params: ",function_params)

                    if function_name == "retrieve_related_chunks":
                        # Retrieve the first three chunks
                        function_result = names_to_functions[function_name](**function_params)[:3]

                        # Safely join the 'description' from each chunk
                        chunks = " ".join(
                            chunk.get("description", "") for chunk in function_result if isinstance(chunk, dict))
                        print(chunks)
                        print(type(chunks))
                        # Append the message
                        messages.append({
                            "role": "tool",
                            "name": function_name,
                            "content": f""" Ты агент, помогающий игрокам в Dnd. Отвечай по существу и кратко, не более чем в 5-6 предложений.
                            Ответь на вопрос {function_params["query"]} используя данные контекст:\n{chunks}.for """,
                            "tool_call_id": tool_call.id
                        })

                        response = client.chat.complete(model=model, messages=messages)
                        messages.append(response.choices[0].message)
                        return response.choices[0].message.content

                    if function_name == "generate_dungeon_map":
                        try:
                            # Generate dungeon map asynchronously and await the result
                            function_result = names_to_functions[function_name](function_params)
                            print("func_res: ", function_result)
                            result_data = json.loads(function_result)

                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "Map has been generated!",  # This is now a string, not a coroutine
                                "tool_call_id": tool_call.id
                            })
                            response = client.chat.complete(model=model, messages=messages)
                            messages.append(response.choices[0].message)
                            return "No-op"
                        except Exception as func_error:
                            print(f"Error processing 'generate_dungeon_map': {func_error}")
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "Error processing tool function",
                                "tool_call_id": tool_call.id
                            })

                    elif function_name in ["play_music_from_playlist", "stop_audio"]:
                        try:
                            # Handle music commands locally
                            names_to_functions[function_name](**function_params)
                            print(f"Processed {function_name} locally with result: Success")
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "No-op",
                                "tool_call_id": tool_call.id
                            })
                            response = client.chat.complete(model=model, messages=messages)
                            messages.append(response.choices[0].message)
                            return "No-op"
                        except Exception as func_error:
                            print(f"Error processing tool '{function_name}': {func_error}")
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "Error processing tool function",
                                "tool_call_id": tool_call.id
                            })

                    elif function_name in names_to_functions:
                        try:
                            # Process all other tool calls
                            function_result = names_to_functions[function_name](**function_params)
                            result_data = json.loads(function_result)

                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": function_result,
                                "tool_call_id": tool_call.id
                            })
                        except Exception as func_error:
                            print(f"Error processing tool '{function_name}': {func_error}")
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": "Error processing tool function",
                                "tool_call_id": tool_call.id
                            })

                # Only request a new Mistral completion for non-music tools
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