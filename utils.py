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
    payload['messages'] = prompt
    return requests.post(url, headers=headers, json=payload, stream=True)


def generate_prompt(chat_dict):
    prompt = []
    for i in chat_dict:
        if i['role'] == 'tool':
            toolPrompt = ""
            for j in range(len(i['names'])):
                toolPrompt += f'\n<tool_response>\n{{"name": "{i["names"][j]}", "result": "{i["contents"][j]}"}}\n</tool_response>'
            prompt.append(
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': toolPrompt
                        }
                    ]
                }
            )
        if i['role'] == 'system':
            prompt.append(
                {
                    'role': 'system',
                    'content': [
                        {
                            'type': 'text',
                            'text': i['content']
                        }
                    ]
                }
            )
        if i['role'] == 'assistant':
            prompt.append(
                {
                    'role': 'assistant',
                    'content': [
                        {
                            'type': 'text',
                            'text': i['content']
                        }
                    ]
                }
            )
        if i['role'] == 'user':
            if 'image' in i.keys():
                prompt.append(
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': i['content']
                            }
                        ]
                    }
                )
                index = len(prompt)
                for image in i['image']:
                    prompt[index-1]['content'].append(
                        {
                            'type': 'image_url',
                            'image_url': {'url': image}
                        }
                    )
            else:
                prompt.append(
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': i['content']
                            }
                        ]
                    }
                )
    return prompt
