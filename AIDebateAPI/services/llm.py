import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
ollama_host = os.getenv("OLLAMA_HOST")
ollama_port = os.getenv("OLLAMA_PORT")
def speak(messages, model):
    r = requests.post(
        f"http://{ollama_host}:{ollama_port}/api/chat",
        json={"model": model, "messages": messages, "stream": True},
        stream=True
    )
    r.raise_for_status()
    output = ""

    for line in r.iter_lines():
        body = json.loads(line)
        if "error" in body:
            raise Exception(body["error"])
        if body.get("done") is False:
            message = body.get("message", "")
            content = message.get("content", "")
            output += content
        if body.get("done", False):
            message["content"] = output
            return message