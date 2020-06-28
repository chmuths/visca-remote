# coding: utf-8

import time
import json
import os.path
from flask import Flask, render_template, send_file, request, jsonify
from controllers import buttons as btn, head as hd, tally as ty, videohub as vh

# Get config file from same folder than this module
folder_name = os.path.dirname(__file__)
path = os.path.join(folder_name, "..", 'config.json')
with open(path, 'r') as config_file:
    hw_conf = json.load(config_file)

if 'heads' in hw_conf:
    heads = hd.init_heads(hw_conf['heads'])
    print(f"HEADS\n{heads}")
else:
    heads = []

tallies = ty.Tally(hw_conf.get('tallies'))
print(f"TALLIES\n{tallies.tallies}")

if 'videohub' in hw_conf:
    videohub = vh.Videohub(hw_conf['videohub'])
else:
    videohub = None
    print("no videohub in config file")

button_instances = {}
if 'buttons' in hw_conf:
    buttons = hw_conf['buttons']
    for button in buttons:
        button_instance = btn.Buttons(button, videohub, tallies)
        button_instances.update({button['name']: button_instance})
    print(f"BUTTONS\n{buttons}")
else:
    buttons = []


def save_config(config_dict):
    # Get config file from same folder than this module
    folder_name = os.path.dirname(__file__)
    path = os.path.join(folder_name, "..", 'config.json')
    with open(path, 'w') as config_file:
        json.dump(config_dict, config_file)


def update_all_buttons(buttons_list):
    for button_dict in buttons_list:
        button_to_update = button_instances[button_dict['name']]
        button_to_update.configure_button(action=button_dict['action'], matrix_in=button_dict['matrix_in'],
                                          matrix_out=button_dict['matrix_out'],
                                          visual_echo=button_dict.get('visual_echo'))


def auto_test():
    """
    Move all heads in the 4 directions to make sure connectivity is OK
    :return: Nothing
    """
    nb_heads = len(heads)
    nb_tallies = len(tallies.tallies)

    print('go right')
    for tally_ID in range(nb_tallies):
        tallies.set_tally(tally_ID, 'pvw')
    for head_ID in range(nb_heads):
        hd.go_right(heads[head_ID])
    time.sleep(1)

    print('Go left')
    for tally_ID in range(nb_tallies):
        tallies.set_tally(tally_ID, 'pgm')
    for head_ID in range(nb_heads):
        hd.go_left(heads[head_ID])
    time.sleep(1)

    print('Pan Stop')
    for head_ID in range(nb_heads):
        hd.pan_stop(heads[head_ID])

    print('go up')
    for tally_ID in range(nb_tallies):
        tallies.set_tally(tally_ID, 'pvw')
    for head_ID in range(nb_heads):
        hd.go_up(heads[head_ID])
    time.sleep(1)

    print('Go down')
    for tally_ID in range(nb_tallies):
        tallies.set_tally(tally_ID, 'pgm')
    for head_ID in range(nb_heads):
        hd.go_down(heads[head_ID])
    time.sleep(1)

    print('tilt Stop')
    for tally_ID in range(nb_tallies):
        tallies.set_tally(tally_ID, 'off')
    for head_ID in range(nb_heads):
        hd.tilt_stop(heads[head_ID])


app = Flask(__name__)


@app.route('/favicon.ico')
def get_favicon():
    """
    Returns a favicon picture file to the web browser.
    This may not be visible, but it avoids and HTTP error if the web browser requests the favicon.
    :return: HTTP answser with icon file
    """
    return send_file('static/images/favicon.ico', mimetype='image/x-icon')


@app.route('/images/<img_filename>')
def get_image(img_filename):
    """
    Processes images files requests
    :param img_filename: the filename of the picture being requested
    :return: HTTP answer with picture file
    """
    return send_file('static/images/' + img_filename, mimetype='image/png')


@app.route('/mph', methods=['GET', 'POST'])
def home():
    # GET is used for a web page user interface
    if request.method == 'GET':
        if request.args.get('head_id'):
            head_id = int(request.args.get('head_id'))
        else:
            head_id = 0
        if head_id < len(heads):
            direction = request.args.get('move')
            if direction:
                hd.move(heads[head_id], direction)
            speed = request.args.get('speed')
            if speed:
                hd.set_speed(heads[head_id], speed)

        return render_template('mph_remote_tpl.html', heads=heads)

    # POST is used for a RESTful end point
    if request.method == 'POST':
        content = request.get_json()
        if 'head_id' in content:
            head_id = int(content['head_id'])
        else:
            head_id = 0
        if head_id < len(heads):
            if 'move' in content:
                move_requ = content['move'].lower()
                hd.move(heads[head_id], move_requ)
            if 'speed' in content:
                speed_req = content['speed']
                hd.set_speed(heads[head_id], speed_req)

            return jsonify({'head_id': head_id, 'move': heads[head_id]['current_dir'],
                            'speed': heads[head_id]['current_speed']})
        else:
            return jsonify({'error': 'invalid head ID'}), 400

    if request.user_agent:
        print(request.user_agent.platform)


@app.route('/tally', methods=['GET', 'POST'])
def tally():
    """
    Sets tally light to a given status
    :return: HTML page in case of get, JSON file in case of POST
    """
    if request.method == 'GET':
        if request.args.get('tally_id'):
            tally_id = int(request.args.get('tally_id'))
        else:
            tally_id = 0
        if tally_id < len(tallies.tallies) and request.args.get('status'):
            tally_status = request.args.get('status')
            tallies.set_tally(tally_id, tally_status)
        return render_template('tally_tpl.html', tallies=tallies.tallies, hostname=hostname)

    if request.method == 'POST':
        content = request.get_json()
        if 'tally_id' in content:
            tally_id = int(content['tally_id'])
        else:
            tally_id = 0
        if tally_id < len(tallies.tallies):
            if 'status' in content:
                tally_status = content['status'].lower()
                real_status = tallies.set_tally(tally_id, tally_status)
            else:
                real_status = tallies.set_tally(tally_id, 'off')
            return jsonify({'tally_id': tally_id, 'status': real_status})
        else:
            return jsonify({'tally_id': tally_id, 'status': 'unknown'}), 400


@app.route('/', methods=['GET'])
def config_display():
    """
    Display a general status page
    :return: HTML page
    """
    if not videohub.connected:
        try:
            videohub.get_connection()
        except vh.NotConnected:
            pass

    if request.method == 'GET':
        return render_template('itc_status.html', tallies=tallies.tallies, buttons=buttons,
                               videohub=videohub, hostname=hostname)


def build_config():
    return hw_conf


@app.route('/config', methods=['GET'])
def config():
    """
    Return the JSON config
    :return: JSON file
    """
    if request.method == 'GET':
        config_response = build_config()

        return jsonify(config_response)


@app.route('/config/tally', methods=['POST'])
def config_tally():
    content = request.get_json()
    if 'tally_id' in content:
        tally_id = int(content['tally_id'])
    else:
        tally_id = 0
    if tally_id < len(tallies.tallies):
        if 'name' in content:
            tallies.tallies[tally_id]['name'] = content['name']
            hw_conf['tallies'][tally_id]['name'] = content['name']
            save_config(hw_conf)
            return jsonify(build_config())
        else:
            return jsonify(build_config()), 400
    else:
        return jsonify(build_config()), 400


@app.route('/config/head', methods=['POST'])
def config_head():
    content = request.get_json()
    if 'head_id' in content:
        head_id = int(content['head_id'])
    else:
        head_id = 0
    if head_id < len(heads):
        if 'name' in content:
            heads[head_id]['name'] = content['name']
            hw_conf['heads'][head_id]['name'] = content['name']
            save_config(hw_conf)
            return jsonify(build_config())
        else:
            return jsonify(build_config()), 400
    else:
        return jsonify(build_config()), 400


@app.route('/buttons', methods=['GET', 'POST'])
def config_home():
    if not videohub.connected:
        try:
            videohub.get_connection()
        except vh.NotConnected:
            pass

    if videohub.connected:
        if request.method == 'GET':
            return render_template('config_tpl.html', buttons=buttons, videohub=videohub.videohub, hostname=hostname)
        else:
            for echo_button in buttons:
                echo_button['visual_echo'] = 'off'
            for key, value in request.form.items():
                print(key, value)
                split_key = key.split("-")
                if split_key[0] == 'button_action':
                    button_conf = [conf for conf in buttons if conf['name'] == split_key[1]]
                    button_conf[0].update({'action': value})
                    if value == 'toggle' and len(button_conf[0]['matrix_in']) < 2:
                        button_conf[0].update({'matrix_in': button_conf[0]['matrix_in'] + [0]})
                    elif value == 'switch':
                        button_conf[0].update({'matrix_in': [button_conf[0]['matrix_in'][0]]})
                elif split_key[0] == 'button_input':
                    button_conf = [conf for conf in buttons if conf['name'] == split_key[2]]
                    if len(button_conf[0]['matrix_in']) > int(split_key[1]):
                        button_conf[0]['matrix_in'][int(split_key[1])] = int(value)
                elif split_key[0] == 'button_output':
                    button_conf = [conf for conf in buttons if conf['name'] == split_key[1]]
                    button_conf[0].update({'matrix_out': int(value)})
                elif split_key[0] == 'echo_button':
                    button_conf = [conf for conf in buttons if conf['name'] == split_key[1]]
                    button_conf[0].update({'visual_echo': value})
            print(f"Buttons {buttons}")
            update_all_buttons(buttons)
            save_config(hw_conf)
            return render_template('config_tpl.html', buttons=buttons, videohub=videohub.videohub, hostname=hostname)
    else:
        return render_template("videohub_not_connected.html", hostname=hostname)


@app.route('/buttons/<button_name>/add_toggle', methods=['POST'])
def add_input(button_name):
    print(f"Button name {button_name} add toggle")
    button_conf = [conf for conf in buttons if conf['name'] == button_name]
    button_conf[0].update({'matrix_in': button_conf[0]['matrix_in'] + [0]})
    update_all_buttons(buttons)
    save_config(hw_conf)
    return render_template('config_tpl.html', buttons=buttons, videohub=videohub.videohub, hostname=hostname)


@app.route('/buttons/<button_name>/del_toggle', methods=['POST'])
def del_input(button_name):
    print(f"Button name {button_name} remove toggme")
    button_conf = [conf for conf in buttons if conf['name'] == button_name]
    button_conf[0].update({'matrix_in': button_conf[0]['matrix_in'][:-1]})
    update_all_buttons(buttons)
    save_config(hw_conf)
    return render_template('config_tpl.html', buttons=buttons, videohub=videohub.videohub, hostname=hostname)


@app.route('/buttons/<button_name>/test', methods=['POST'])
def test_button(button_name):
    print(f"Button {button_name} test")
    button_instances[button_name].execute_action()
    return render_template('config_tpl.html', buttons=buttons, videohub=videohub.videohub, hostname=hostname)


if __name__ == '__main__':

    hostname = os.uname().nodename
    auto_test()
    nb_heads = len(heads)
    for head_id in range(nb_heads):
        hd.move(heads[head_id], 'stop')
        hd.set_speed(heads[head_id], 'slow')
    try:
        videohub.get_connection()
    except vh.NotConnected:
        pass

    app.run(host='0.0.0.0', port=int("80"))
