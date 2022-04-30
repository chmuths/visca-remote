import os.path
from datetime import datetime as dt
import json
from controllers.file_read_helper import get_dated_files_list


# Get config file from same folder than this module
folder_name = os.path.dirname(__file__)
config_path = os.path.join(folder_name, "..")


def open_backup_config(base_path):
    """
    Read the latest backup config file
    :return:
    """
    backup_dir = os.path.join(base_path, "backup")
    file_list = get_dated_files_list(backup_dir, 'config', 'json')

    for file_name, timestamp in file_list:
        backup_path = os.path.join(backup_dir, file_name)
        with open(backup_path, 'r') as backup_config_file:
            try:
                backup_conf = json.load(backup_config_file)
                backup_serial_port = backup_conf.get('global', {}).get("serial")
                if backup_serial_port:
                    print(f"Le fichier de configuration {file_name} a été récupéré")
                    restored_config_path = os.path.join(base_path, 'config.json')
                    with open(restored_config_path, 'w') as restored_config_file:
                        json.dump(backup_conf, restored_config_file)
                    return backup_conf
            except json.decoder.JSONDecodeError:
                print(f"Fichier de config {file_name} illisible, recherche du précédent backup")

    print("!!! ERREUR : Aucun fichier de config n'a pu être trouvé !!!")
    empty_conf = {"global": {
        "serial": "COM1",
        "debug": True
    }}
    return empty_conf


def save_config(cameras_list):
    """
    Save full configuration
    :param cameras_list: cluster of camera objects
    :return: Saved JSON file
    """
    camera_dict_list = []
    for camera in cameras_list:
        camera_dict = camera.__dict__
        camera_dict_list.append(camera_dict)

    final_dict = {"cameras": camera_dict_list, "global": hw_conf.get("global", {})}

    path = os.path.join(config_path, 'config.json')
    print(f"Path du fichier de config {path}")
    backup = os.path.join(config_path, "backup", f"config-{dt.now().strftime('%Y-%m-%d-%H%M%S')}.json")
    try:
        os.rename(path, backup)
    except FileNotFoundError:
        print(f"Attention, le dossier backup {backup} n'existe pas")

    with open(path, 'w') as config_file:
        json.dump(final_dict, config_file)


def read_config(path):
    config_file_path = os.path.join(path, 'config.json')
    try:
        with open(config_file_path, 'r') as config_file:
            config_dict = json.load(config_file)
            serial_port = config_dict.get('global', {}).get("serial")
            if not serial_port:
                print("Ficher de config incomplet, chargement du dernier backup")
                config_dict = open_backup_config(path)
    except FileNotFoundError:
        print("Pas de fichier de config, chargement du dernier backup")
        config_dict = open_backup_config(path)
    except json.decoder.JSONDecodeError:
        print("Fichier de config illisible, chargement du dernier backup")
        config_dict = open_backup_config(path)

    return config_dict


hw_conf = read_config(config_path)
