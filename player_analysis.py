import json

file_path = 'Soccer_Data/coaches.json'


with open(file_path, 'r') as f:
    coaches_data = json.load(f)
    print(json.dumps(coaches_data, indent=2))

