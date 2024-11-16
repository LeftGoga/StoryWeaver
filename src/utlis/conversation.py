import json
import time
async def process_conversation(client, model, messages, tools, names_to_functions, max_retries=5, initial_delay=2):
    retry_count = 0
    delay = initial_delay
    system_prompt = """Ты - помощник ведущего настольно-ролевой игры. Твоя задача помогать ведущему с помощью инструментов.
        В своих ответах будь краток - 5-6 предложений. Если тебя просят включить или выключить музыку-В ответ скажи no-op.
        Для ответов на вопросы используй инструмент retrieve_related_chunks.
        В функцию generate_dungeon_map передавай аргументы json-ом.
        """
    messages.insert(0, {
        "role": "system",
        "content": system_prompt
    })

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

            # Tool processing
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    print(f"Tool requested: {function_name}")

                    # Handle music commands locally and skip Mistral response for these cases
                    if function_name in ["play_online_music", "stop_music"]:
                        function_params = json.loads(tool_call.function.arguments)
                        names_to_functions[function_name](**function_params)
                        print(f"Processed {function_name} locally with result: Success")
                        messages.append({
                            "role": "tool",
                            "name": function_name,
                            "content": "Music command processed."
                        })
                        continue

                    # Process other tool calls as normal
                    function_params = json.loads(tool_call.function.arguments)
                    print("func_params: ",function_params)
                    if function_name in names_to_functions:
                        try:
                            if function_name == "generate_dungeon_map":

                                function_result = await names_to_functions[function_name](function_params)
                                print("func_res: ",function_result)

                            else:
                                function_result = names_to_functions[function_name](**function_params)
                            result_data = json.loads(function_result)


                            if function_name == "retrieve_related_chunks" and "chunks" in result_data:
                                top_chunks = "\n".join(
                                    chunk['description'] if isinstance(chunk, dict) and 'description' in chunk else str(chunk)
                                    for chunk in result_data["chunks"][:3]
                                )
                                messages.append({
                                    "role": "tool",
                                    "name": function_name,
                                    "content": f"Relevant Information:\n{top_chunks}",
                                    "tool_call_id": tool_call.id
                                })
                            else:
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
