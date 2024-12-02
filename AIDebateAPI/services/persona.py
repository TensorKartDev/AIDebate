import json
def personas():
    with open("personas.json", "r") as file:
            personas = json.load(file)
            return personas