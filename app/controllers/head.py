# coding: utf-8

# noinspection PyUnresolvedReferences
import RPi.GPIO as GPIO

default_dir_pictures = ['left_up_bw', 'up_bw', 'right_up_bw',
                        'left_bw', 'stop_bw', 'right_bw',
                        'left_down_bw', 'down_bw', 'right_down_bw']
default_speed_pictures = ['slow_bw', 'medium_bw', 'fast_bw']


def init_heads(head_config):
    # Define GPIO ports associated to each moving head feature and other properties
    heads = []
    head_id = 0
    for head in head_config:
        heads = heads + [{'name': head['name'],
                          'id': head_id,
                          'left': head['ports']['left'],
                          'right': head['ports']['right'],
                          'up': head['ports']['up'],
                          'down': head['ports']['down'],
                          'slow': head['ports']['slow'],
                          'medium': 0,
                          'has_medium': False,
                          'current_dir': 'stop',
                          'current_speed': 'slow',
                          'dir_pictures': default_dir_pictures.copy(),
                          'speed_pictures': default_speed_pictures.copy()}]
        if 'medium' in head['ports']:
            heads[head_id]['has_medium'] = True
            heads[head_id]['medium'] = head['ports']['medium']
        head_id += 1

    # Set GPIO naming convention
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Initialize ports
    for head in heads:
        GPIO.setup(head['left'], GPIO.OUT)
        GPIO.setup(head['right'], GPIO.OUT)
        GPIO.setup(head['up'], GPIO.OUT)
        GPIO.setup(head['down'], GPIO.OUT)
        GPIO.setup(head['slow'], GPIO.OUT)
        if head['has_medium']:
            GPIO.setup(head['medium'], GPIO.OUT)

    return heads


# Unitary features
def stop(head):
    GPIO.output(head['left'], GPIO.HIGH)
    GPIO.output(head['right'], GPIO.HIGH)
    GPIO.output(head['up'], GPIO.HIGH)
    GPIO.output(head['down'], GPIO.HIGH)


def go_left(head):
    GPIO.output(head['left'], GPIO.LOW)
    GPIO.output(head['right'], GPIO.HIGH)


def go_right(head):
    GPIO.output(head['left'], GPIO.HIGH)
    GPIO.output(head['right'], GPIO.LOW)


def pan_stop(head):
    GPIO.output(head['left'], GPIO.HIGH)
    GPIO.output(head['right'], GPIO.HIGH)


def go_up(head):
    GPIO.output(head['up'], GPIO.LOW)
    GPIO.output(head['down'], GPIO.HIGH)


def go_down(head):
    GPIO.output(head['up'], GPIO.HIGH)
    GPIO.output(head['down'], GPIO.LOW)


def tilt_stop(head):
    GPIO.output(head['up'], GPIO.HIGH)
    GPIO.output(head['down'], GPIO.HIGH)


def move(head, direction):
    head['dir_pictures'] = default_dir_pictures.copy()
    if direction == 'stop':
        stop(head)
        head['dir_pictures'][4] = 'stop'
        head['current_dir'] = direction
    elif direction == 'up':
        go_up(head)
        pan_stop(head)
        head['dir_pictures'][1] = 'up'
        head['current_dir'] = direction
    elif direction == 'down':
        go_down(head)
        pan_stop(head)
        head['dir_pictures'][7] = 'down'
        head['current_dir'] = direction
    elif direction == 'left':
        go_left(head)
        tilt_stop(head)
        head['dir_pictures'][3] = 'left'
        head['current_dir'] = direction
    elif direction == 'right':
        go_right(head)
        tilt_stop(head)
        head['dir_pictures'][5] = 'right'
        head['current_dir'] = direction
    elif direction == 'left_up':
        go_left(head)
        go_up(head)
        head['dir_pictures'][0] = 'left_up'
        head['current_dir'] = direction
    elif direction == 'left_down':
        go_left(head)
        go_down(head)
        head['dir_pictures'][6] = 'left_down'
        head['current_dir'] = direction
    elif direction == 'right_up':
        go_right(head)
        go_up(head)
        head['dir_pictures'][2] = 'right_up'
        head['current_dir'] = direction
    elif direction == 'right_down':
        go_right(head)
        go_down(head)
        head['dir_pictures'][8] = 'right_down'
        head['current_dir'] = direction


def low_speed(head):
    GPIO.output(head['slow'], GPIO.LOW)
    if head['has_medium']:
        GPIO.output(head['medium'], GPIO.HIGH)


def medium_speed(head):
    GPIO.output(head['slow'], GPIO.HIGH)
    if head['medium']:
        GPIO.output(head['medium'], GPIO.LOW)


def high_speed(head):
    GPIO.output(head['slow'], GPIO.HIGH)
    if head['has_medium']:
        GPIO.output(head['medium'], GPIO.HIGH)


def set_speed(head, speed_setting):
    """
    Sets speed of MHP100 head. In case of wrong argument, no change is done.
    :param head: Structure of the head to be updated
    :param speed_setting: string with values slow, medium or fast
    :return: nothing
    """
    head['speed_pictures'] = default_speed_pictures.copy()
    if speed_setting == 'slow':
        low_speed(head)
        head['speed_pictures'][0] = 'slow'
        head['current_speed'] = speed_setting
    elif speed_setting == 'medium' and head['has_medium']:
        medium_speed(head)
        head['speed_pictures'][1] = 'medium'
        head['current_speed'] = speed_setting
    elif speed_setting == 'fast':
        high_speed(head)
        head['speed_pictures'][2] = 'fast'
        head['current_speed'] = speed_setting
