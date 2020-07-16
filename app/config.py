import os.path
import json

# Get config file from same folder than this module
folder_name = os.path.dirname(__file__)
path = os.path.join(folder_name, "..", 'config.json')
with open(path, 'r') as config_file:
    hw_conf = json.load(config_file)
