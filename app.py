import json
import os
import re
from flask import Flask, Response, stream_with_context, request, render_template, jsonify, send_from_directory
from utils import query, generate_prompt
from prompt import system_prompt, toolsAlias, getFunction, parameters
# from pyngrok import ngrok
from sseclient import SSEClient
from apitoken import URL, apimodel, imgCompatible
# public_url = ngrok.connect(5000).public_url

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
        if 'images' in user_text.keys():
            chat.append({'role': 'user', 'content': user_text['usertext'], 'image': user_text['images']})
        else:
            chat.append({'role': 'user', 'content': user_text['usertext']})
        print("---" * 1000)
        print("AI: \n", end="")
        userTurn = False
        stopGenerate = False
    while not userTurn:
        prompt = generate_prompt(chat)
        output = ""
        print(prompt)
        try:
            parameters['stream'] = True
            print(parameters)
            data = query(URL, parameters, prompt)
            print(data)
            client = SSEClient(data)
        except Exception as e:
            yield f"error: {e}"
            break
        for token in client.events():
            print(token.data)
            if stopGenerate:
                break
            if token.data != "[DONE]":
                chunk = json.loads(token.data)['choices'][0]['delta']["content"]
                output += chunk
                yield chunk
        yield '\n\n'
        print("parsing " + output)
        if stopGenerate:
            chat.append({'role': 'assistant', 'content': output})
            userTurn = True
            break
        if output != "":
            chat.append({'role': 'assistant', 'content': output})
            userTurn = True
            if '<tool_call>' in output:
                userTurn = False
                json_objects = re.compile(f"{re.escape('<tool_call>')}(.*?){re.escape('</tool_call>')}", re.DOTALL).findall(output)
                parsed_json = [json.loads(match.strip()) for match in json_objects]
                for i in parsed_json:
                    yield f"**{toolsAlias[i['name']]} called**\n\n"
                chat.append(
                    {
                        'role': 'tool',
                        'names': [i['name'] for i in parsed_json],
                        'contents': [getFunction[i['name']](**json.loads(i['arguments']) if type(i['arguments']) == str else i['arguments']) for i in parsed_json]
                    }
                )
        else:
            userTurn = False


app = Flask(__name__)
# app.config["BASE_URL"] = public_url


@app.route('/sendtext', methods=['POST'])
def send_text():
    userText = request.get_json()
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


@app.route('/imgcompatible')
def get_model():
    return jsonify({'message': imgCompatible}), 200


if __name__ == '__main__':
    print(f"Using model: {apimodel}")
    print(f"Parameter: {parameters}")
    # print(f"Access this: {public_url}")
    reset_conv()
    app.run(debug=False)
