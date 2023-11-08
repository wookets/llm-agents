import openai
import json
import subprocess


# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def run_kubectl_command(command):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return result.stdout, result.stderr


def run_conversation():
    # Step 1: send the conversation and available functions to the model
    messages = [
        {
            "role": "user",
            "content": "Find all crashing pods in kubernetes using kubectl?",
        }
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_kubectl_command",
                "description": "Run the desired kubectl command to get the output.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to run.",
                        },
                    },
                    "required": ["command"],
                },
            },
        }
    ]
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "run_kubectl_command": run_kubectl_command,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                command=function_args.get("command"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = openai.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response


print(run_conversation())
