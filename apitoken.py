apimodel = "Qwen/Qwen2-VL-72B-Instruct"
# apimodel = "Qwen/Qwen2.5-72B-Instruct"
imgCompatible = True if "VL" in apimodel else False
URL = "https://api.studio.nebius.ai/v1/chat/completions"
API_TOKEN = ""
HF_TOKEN = ""
