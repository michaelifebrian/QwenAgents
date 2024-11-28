import requests
from apitoken import API_TOKEN
import json
from transformers.utils import get_json_schema

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def create_tools_json(tools):
    getFunction = {}
    for i in tools:
        getFunction[get_json_schema(i)['function']['name']] = i
    tools = [json.dumps(get_json_schema(i)) for i in tools]
    tools = "\n".join(tools)
    return getFunction, tools


def query(url, payload, prompt):
    payload['prompt'] = prompt
    return requests.post(url + "/v1/completions", headers=headers, json=payload, stream=True)


def generate_prompt(chat_dict):
    prompt = ""
    for i in chat_dict:
        if i['role'] == 'system':
            prompt += f"<|im_start|>system\n{i['content']}<|im_end|>\n"
        elif i['role'] == 'user':
            prompt += f"<|im_start|>user\n{i['content']}<|im_end|>\n"
        elif i['role'] == 'assistant':
            prompt += f"<|im_start|>assistant\n{i['content']}<|im_end|>\n"
        elif i['role'] == 'tool':
            prompt += f'<|im_start|>user'
            for j in range(len(i['names'])):
                prompt += f'\n<tool_response>\n{{"name": "{i["names"][j]}", "result": "{i["contents"][j]}"}}\n</tool_response>'
            prompt += '<|im_end|>\n'
    return prompt
