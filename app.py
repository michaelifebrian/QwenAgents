import json
import os
import re
from flask import Flask, Response, stream_with_context, request, render_template, jsonify, send_from_directory
from utils import query, generate_prompt
from prompt import system_prompt, toolsAlias, getFunction, parameters
# from pyngrok import ngrok
from sseclient import SSEClient
from apitoken import URL, apimodel
# public_url = ngrok.connect(5000).public_url

seed = int.from_bytes(os.urandom(8), 'big')
chat = []
userTurn = None
stopGenerate = False


def reset_conv():
    global userTurn
    global chat
    chat = [{'role': 'system', 'content': system_prompt}]
    userTurn = True


def run_model(user_text):
    global userTurn
    global chat
    global stopGenerate
    if userTurn:
        print("---" * 1000)
        chat.append({'role': 'user', 'content': user_text})
        print("---" * 1000)
        print("AI: \n", end="")
        userTurn = False
        stopGenerate = False
    while not userTurn:
        prompt = generate_prompt(chat) + "\n<|im_start|>assistant\n"
        output = ""
        print(prompt)
        try:
            parameters['stream'] = True
            data = query(URL, parameters, prompt)
            client = SSEClient(data)
        except Exception as e:
            yield f"error: {e}"
            break
        toolCalls = False
        stream = True
        for token in client.events():
            print(token.data)
            if stopGenerate:
                break
            if token.data != "[DONE]":
                chunk = json.loads(token.data)['choices'][0]["text"]
                output += chunk
                if "<tool_call>" in chunk:
                    toolCalls = True
                    stream = False
                    yield chunk.split("<tool_call>")[0].split("</tool_call>")[-1]
                if stream:
                    yield chunk
                if "</tool_call>" in chunk:
                    stream = True
                    if "<tool_call>" in chunk:
                        stream = False
        yield '\n\n'
        print("parsing " + output)
        if stopGenerate:
            chat.append({'role': 'assistant', 'content': output})
            userTurn = True
            break
        if output != "":
            chat.append({'role': 'assistant', 'content': output})
            userTurn = True
            if toolCalls:
                userTurn = False
                json_objects = re.compile(f"{re.escape('<tool_call>')}(.*?){re.escape('</tool_call>')}", re.DOTALL).findall(output)
                parsed_json = [json.loads(match.strip()) for match in json_objects]
                for i in parsed_json:
                    yield f"**{toolsAlias[i['name']]} called**\n\n"
                chat.append(
                    {
                        'role': 'tool',
                        'names': [i['name'] for i in parsed_json],
                        'contents': [getFunction[i['name']](**i['arguments']) for i in parsed_json]
                    }
                )
        else:
            userTurn = False


app = Flask(__name__)
# app.config["BASE_URL"] = public_url


@app.route('/sendtext', methods=['POST'])
def send_text():
    userText = request.get_json()['usertext']
    response = run_model(userText)
    return Response(stream_with_context(response))


@app.route('/<path:filename>')
def download_file(filename):
    return send_from_directory("", filename, as_attachment=False)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/resetconv', methods=['POST'])
def reset_conversation():
    reset_conv()
    return jsonify({'message': 'Conversation reset'}), 200


@app.route('/chatdict')
def chat_history():
    return jsonify(chat)


@app.route('/stopgenerate')
def stop_generate():
    global stopGenerate
    stopGenerate = True
    return jsonify({'message': 'Generation stopped'}), 200


if __name__ == '__main__':
    print(f"Using model: {apimodel}")
    print(f"Parameter: {parameters}")
    # print(f"Access this: {public_url}")
    reset_conv()
    app.run(debug=False)
