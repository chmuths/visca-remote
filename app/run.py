# coding: utf-8

import json
import os.path
import socket
from flask import Flask, render_template, send_file, request
from controllers import visca
from config import hw_conf

host_name = socket.gethostname()
host_ip = str(socket.gethostbyname(host_name))

debug_mode = hw_conf.get('global', {}).get("debug", False)

visca.Visca.set_address_with_ack(1)

cameras = []
for camera in hw_conf.get('cameras'):
    address = camera.get("address", 0x81)
    name = camera.get("name", "No Name")
    ceiling = camera.get("ceiling_mount", False)
    buttons_list = camera.get("buttons")
    this_camera = visca.Visca(address, name, buttons=buttons_list, ceiling_mount=ceiling)
    cameras.append(this_camera)


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

    folder_name = os.path.dirname(__file__)
    path = os.path.join(folder_name, "..", 'config.json')
    with open(path, 'w') as config_file:
        json.dump(final_dict, config_file)


def execute_action(camera, button):
    camera.pt_direct(button['pan_pos'], button['tilt_pos'], button['pan_speed'], button['tilt_speed'])

    zoom_value = button.get('zoom_value')
    if zoom_value:
        camera.zoom_direct(zoom_value)

    focus_value = button.get('focus_value')
    if focus_value is not None:
        camera.focus_manual()
        camera.focus_direct(focus_value)

    camera.last_button_name = button['name']


def get_camera_status(camera_to_query):
    pan, tilt = camera_to_query.pt_query()
    zoom = camera_to_query.zoom_query()
    focus = camera_to_query.focus_query()
    focus_mode = camera_to_query.focus_mode_query()
    return {"pan": pan, "tilt": tilt, "zoom": zoom, "focus": focus, "focus_mode": focus_mode}


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


@app.route('/', methods=['GET', 'POST'])
def main_board():
    """
    Display the main buttons page
    :return: HTML page
    """
    if request.method == 'GET':
        for cam in cameras:
            cam.focus_mode = cam.focus_mode_query()
        return render_template('main_board.html', cameras=cameras, ip_address=host_ip)
    elif request.method == 'POST':
        for key, value in request.form.items():
            split_key = key.split("-")
            camera_address = int(split_key[0])
            filtered_cameras = [cam for cam in cameras if cam.address == camera_address]
            found_button = None
            for button_row in filtered_cameras[0].buttons:
                for button_item in button_row:
                    if button_item['name'] == value:
                        found_button = button_item
            if found_button:
                execute_action(filtered_cameras[0], found_button)
            elif debug_mode:
                print("Button not found")
            if split_key[1] == 'focus':
                if value == "Auto":
                    filtered_cameras[0].focus_manual()
                else:
                    filtered_cameras[0].focus_auto()
                filtered_cameras[0].focus_mode = filtered_cameras[0].focus_mode_query()
        return render_template('main_board.html', cameras=cameras)


@app.route('/config', methods=['GET', 'POST'])
def edit_buttons():
    """
    Display the main buttons page
    :return: HTML page
    """

    if request.method == 'GET':
        camera_address = int(request.args.get('camera'))
        filtered_cameras = [cam for cam in cameras if cam.address == camera_address]
        if len(filtered_cameras) > 0:
            camera_status = get_camera_status(filtered_cameras[0])
        else:
            print(f"No camera at address {camera_address}")
            camera_status = {}
        return render_template('edit_buttons.html', camera=filtered_cameras[0], camera_status=camera_status,
                               ip_address=host_ip)
    elif request.method == 'POST':
        camera_address = int(request.form.get('camera'))
        filtered_cameras = [cam for cam in cameras if cam.address == camera_address]
        if len(filtered_cameras) == 1:
            cam = filtered_cameras[0]
            for key, value in request.form.items():
                split_key = key.split("-")
                input_name = split_key[0]
                if len(split_key) > 2:
                    button_row = int(split_key[1])
                    button_col = int(split_key[2])
                    if input_name == "button_name":
                        cam.buttons[button_row][button_col]['name'] = value
                    elif input_name == "button_action":
                        cam.buttons[button_row][button_col]['action'] = value
                    elif input_name == "pan_value":
                        if value != '':
                            cam.buttons[button_row][button_col]['pan_pos'] = int(value)
                    elif input_name == "pan_speed":
                        if value != '':
                            cam.buttons[button_row][button_col]['pan_speed'] = int(value)
                    elif input_name == "tilt_value":
                        if value != '':
                            cam.buttons[button_row][button_col]['tilt_pos'] = int(value)
                    elif input_name == "tilt_speed":
                        if value != '':
                            cam.buttons[button_row][button_col]['tilt_speed'] = int(value)
                    elif input_name == "zoom_value":
                        if value != '':
                            cam.buttons[button_row][button_col]['zoom_value'] = int(value)
                        else:
                            if 'zoom_value' in cam.buttons[button_row][button_col].keys():
                                cam.buttons[button_row][button_col].pop('zoom_value')
                    elif input_name == "focus_value":
                        if value != '':
                            cam.buttons[button_row][button_col]['focus_value'] = int(value)
                        else:
                            if 'focus_value' in cam.buttons[button_row][button_col].keys():
                                cam.buttons[button_row][button_col].pop('focus_value')

            special_button = False
            pan_inc = 0
            tilt_inc = 0
            for key, value in request.form.items():
                if value == 'Test':
                    special_button = True
                    split_key = key.split("-")
                    if len(split_key) > 2:
                        button_row = int(split_key[1])
                        button_col = int(split_key[2])
                        execute_action(cam, cam.buttons[button_row][button_col])
                elif key == 'autofocus':
                    special_button = True
                    if value == 'Manual':
                        cam.focus_auto()
                    else:
                        cam.focus_manual()
                elif 'add-' in key:
                    special_button = True
                    split_key = key.split("-")
                    if len(split_key) > 1:
                        button_row = int(split_key[1])
                        cam.buttons[button_row] += [{
                            "name": "nouveau bouton",
                            "pan_pos": 408,
                            "tilt_pos": 126,
                            "pan_speed": 0,
                            "tilt_speed": 0,
                            "zoom_value": 0,
                            "focus_value": 288
                        }]
                elif key == "pan+1":
                    pan_inc = 1
                elif key == "pan-1":
                    pan_inc = -1
                elif key == "tilt+1":
                    tilt_inc = 1
                elif key == "tilt-1":
                    tilt_inc = -1

                elif key == 'copy_to_button':
                    for button_row in cam.buttons:
                        for button in button_row:
                            if button['name'] == cam.last_button_name:
                                button['pan_pos'] = int(request.form.get('pan_slider'))
                                button['tilt_pos'] = int(request.form.get('tilt_slider'))
                                button['zoom_value'] = int(request.form.get('zoom_slider'))

            if not special_button:
                pan_value = int(request.form.get('pan_slider')) + pan_inc
                tilt_value = int(request.form.get('tilt_slider')) + tilt_inc
                zoom_value = int(request.form.get('zoom_slider'))
                cam.pt_direct(pan_value, tilt_value, pan_speed=15, tilt_speed=15)
                cam.zoom_direct(zoom_value)

            save_config(cameras)
            camera_status = get_camera_status(cam)

            return render_template('edit_buttons.html', camera=cam, camera_status=camera_status, ip_address=host_ip)
        else:
            return render_template('main_board.html', cameras=cameras)


@app.route('/button/<row>/<column>/delete', methods=['POST'])
def delete_button(row, column):
    """
    Display the main buttons page
    :return: HTML page
    """

    camera_address = int(request.form.get('camera'))
    filtered_cameras = [cam for cam in cameras if cam.address == camera_address]
    if len(filtered_cameras) == 1:
        cam = filtered_cameras[0]

        del cam.buttons[int(row)][int(column)]

        save_config(cameras)
        camera_status = get_camera_status(cam)

        return render_template('edit_buttons.html', camera=cam, camera_status=camera_status, ip_address=host_ip)
    else:
        return render_template('main_board.html', cameras=cameras)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int("80"))
