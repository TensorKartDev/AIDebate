import json
import os 
persona_file = os.path.join(os.getcwd(), "personas.json")
def get_personas():
    with open(persona_file, "r") as file:
            personas = json.load(file)
            return personas
