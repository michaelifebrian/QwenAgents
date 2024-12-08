# Chatbot Agents with Tools Integration
This project is a Flask-based web interface for deploying chatbot agents powered by OpenAI-compatible servers. The application is designed for flexibility, allowing you to modify and extend tools/functions calling based on your requirements. 
## Features
- **Customizable API Token:** Easily switch between different servers by updating the `apitoken.py` file.
- **Configurable Prompts and Tool Integration:** Modify system prompts and extend the bot's capabilities by adding tools/functions in `prompt.py`.
- **Colab Deployment:** Run the app using Google Colab with `ngrok` for public access.
---
## Setup Instructions
### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/michaelifebrian/QwenAgents.git
    cd QwenAgents
    ```
2. Install required Python packages:
    When using colab, you need to forward the local server to public ip using ngrok
    ```bash
    pip -q install pyngrok
    pip -q install ngrok
    ngrok config add-authtoken <ngrok_authtoken>
    pip -q install sseclient-py
    ```
    On this example, there is several example tools that needs to install another package
    ```bash
    pip -q install selenium
    pip -q install markdownify
    pip -q install duckduckgo-search
    ```
### Configuration
1. API Token (`apitoken.py`)
    - Update the `apimodel`, `URL`, and `API_TOKEN` variables to match the OpenAI-compatible server you are using.
    - If your `tools.py` script requires additional tokens, you can store them here as well.
    - Example: 
        ```python
        apimodel = "Qwen/Qwen2-VL-72B-Instruct"
        URL = "https://api.studio.nebius.ai/v1/chat/completions"
        API_TOKEN = "<YOUR_API_TOKEN>"
        ```
    - There is `imgCompatible` variable for vision compability (for QWEN2VL)
2. Prompt Configuration (`prompt.py`)
    - Update the `parameters` variable with payload parameters compatible with your server. Example:
        ```python
        parameters = {
            "model": apimodel,
            "max_tokens": 4096,
            'temperature': 0.95,
            'top_p': 0.9,
        }
    - You can customize the `system_prompt` variable to define the chatbot's behavior. Example:
        ```python
        system_prompt = f"""You are Qwen, created by Alibaba Cloud. You are a helpful assistant that speaks Gen-Z slang.
        ...
        ```
---
## Adding Tools/Functions
You can enhance the chatbot's capabilities by adding or modifying tools:

1. Define Functions in `tools.py`
    - Create a function with a descriptive docstring.
    - Return data in a dictionary format (recommended but optional).
    - Example:
        ```python
        namedatabase = []
        def store_name(name: str):
            """
            Store the user's name.
            
            Args:
                name: The user's name.
            Returns:
                Updated database.
            """
            namedatabase.append(name)
            return {"updated_database": namedatabase}        
        ```
        More info about descriptive docstring: [Huggingface tool schemas](https://huggingface.co/docs/transformers/en/chat_templating#understanding-tool-schemas)
2. Import and Register Functions in `prompt.py`
    - Import your function.
    - Add the function alias to `toolsAlias` and the function itself to `create_tools_json` lines:
        ```python
        from tools import store_name
        
        toolsAlias = {
            "store_name": "Store user's name"
        }
        getFunction, tools = create_tools_json([ ... , store_name])        
        ```
    - You can add another policy to make the model more understand how to use the tools
        ```python
        system_prompt = f"""
        ...
        Policy for each functions you need to follow:
        'store_name':
        1. Do not ask confirmation from user. Just add them as soon as you know their name.
        2. ...
        ...
        ```
---
## Running the Application
### Local Deployment
```bash
python3 app.py
```
### Colab Deployment
1. Uncomment the following pyngrok lines in `app.py`:
    ```python
    from pyngrok import ngrok
    public_url = ngrok.connect(5000).public_url
    app.config["BASE_URL"] = public_url
    print(f"Access this: {public_url}")
    ```
2. Run the app:
    ```bash
    python3 app.py
    ```
You can check the example for running in colab.