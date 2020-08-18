import time
import serial

from config import hw_conf


def int_to_nibble(value):
    value1 = value % 16
    value = int(value / 16)
    value2 = value % 16
    value = int(value / 16)
    value3 = value % 16
    value = int(value / 16)
    value4 = value % 16
    full_value = value1 + 256 * (value2 + 256 * (value3 + 256 * value4))
    hex_value = full_value.to_bytes(4, byteorder='big')
    return hex_value


def nibble_to_int(hex_string):
    value = 0
    for index in range(len(hex_string)):
        value = value * 16 + hex_string[index]
    return value


def hex_print(bytes_array):
    print('|'.join(hex(x) for x in bytes_array))


debug_mode = hw_conf.get('global', {}).get("debug", False)
serial_port = hw_conf.get('global', {}).get("serial", "COM4")
ser = serial.Serial(serial_port, 9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=1, timeout=0.1)


class Visca:

    def __init__(self, address, name, buttons=None, ceiling_mount=False):
        self.address = address
        self.name = name
        self.buttons = buttons
        self.last_button_name = None
        self.focus_mode = None
        self.ceiling_mount = ceiling_mount
        self.last_sent_values = {"pan": 408, "tilt": 126, "zoom": 0, "focus": 0}

    @staticmethod
    def set_address_with_ack(address):
        command_string = b'\x88\x30' + address.to_bytes(1, byteorder='big') + b'\xff'
        if debug_mode:
            print("Command")
            hex_print(command_string)
        ser.write(command_string)
        time.sleep(2)
        response = ser.read(50)
        if debug_mode:
            print("Response")
            hex_print(response)
        return response

    def send_command_with_ack(self, hex_bytes):
        command_string = (self.address + 0x80).to_bytes(1, byteorder='big') + hex_bytes + b'\xff'
        if debug_mode:
            hex_print(command_string)
        ser.write(command_string)
        response = ser.read(50)
        if debug_mode:
            hex_print(response)
        return response

    # PAN-TILT group of methods
    def pt_stop(self):
        pt_stop_bytes = b'\x01\x06\x01\x03\x03\x03\x03'
        return self.send_command_with_ack(pt_stop_bytes)

    def pt_reset(self):
        pt_reset_bytes = b'\x01\x06\x05'
        return self.send_command_with_ack(pt_reset_bytes)

    def pt_up(self):
        if not self.ceiling_mount:
            pt_up_bytes = b'\x01\x06\x01\x00\x00\x03\x01'
        else:
            pt_up_bytes = b'\x01\x06\x01\x00\x00\x03\x02'
        return self.send_command_with_ack(pt_up_bytes)

    def pt_down(self):
        if not self.ceiling_mount:
            pt_down_bytes = b'\x01\x06\x01\x00\x00\x03\x02'
        else:
            pt_down_bytes = b'\x01\x06\x01\x00\x00\x03\x01'
        return self.send_command_with_ack(pt_down_bytes)

    def pt_left(self):
        if not self.ceiling_mount:
            pt_left_bytes = b'\x01\x06\x01\x00\x00\x01\x03'
        else:
            pt_left_bytes = b'\x01\x06\x01\x00\x00\x02\x03'
        return self.send_command_with_ack(pt_left_bytes)

    def pt_right(self):
        if not self.ceiling_mount:
            pt_right_bytes = b'\x01\x06\x01\x00\x00\x02\x03'
        else:
            pt_right_bytes = b'\x01\x06\x01\x00\x00\x01\x03'
        return self.send_command_with_ack(pt_right_bytes)

    def pt_direct(self, pan_pos, tilt_pos, pan_speed=0, tilt_speed=0):
        """

        :param pan_pos: left=0, middle=408, right=816
        :param tilt_pos: down=0, middle=126, up=212
        :param pan_speed: 0 (slow) to 15 (fast)
        :param tilt_speed: 0 (slow) to 15 (fast)
        :return:
        """
        pan_value = pan_pos if not self.ceiling_mount else 816 - pan_pos
        pan_string = int_to_nibble(pan_value)
        tilt_value = tilt_pos if not self.ceiling_mount else 212 - tilt_pos
        tilt_string = int_to_nibble(tilt_value)
        self.last_sent_values.update({"pan": pan_value, "tilt": tilt_value})
        pt_direct_bytes = b'\x01\x06\x02' + pan_speed.to_bytes(1, byteorder='big') + \
                          tilt_speed.to_bytes(1, byteorder='big') + pan_string + tilt_string
        return self.send_command_with_ack(pt_direct_bytes)

    def pt_query(self):
        pt_query_bytes = b'\x09\x06\x12'
        pt_status = self.send_command_with_ack(pt_query_bytes)
        if pt_status and pt_status[1] == 0x50:
            pan_pos = nibble_to_int(pt_status[2:6])
            tilt_pos = nibble_to_int(pt_status[6:10])
            return pan_pos, tilt_pos
        else:
            return None, None

    # Zoom group of methods
    def zoom_stop(self):
        pt_tele_bytes = b'\x01\x04\x07\x00'
        return self.send_command_with_ack(pt_tele_bytes)

    def zoom_tele(self, speed):
        """
        Tele zoom at given speed
        :param speed: int between 0 and 15 (hex 0F)
        :return: return code of camera
        """
        if speed > 0xf:
            speed = 0xf
        if speed < 0:
            speed = 0
        pt_tele_bytes = b'\x01\x04\x07' + (0x20 + speed).to_bytes(1, byteorder='big')
        return self.send_command_with_ack(pt_tele_bytes)

    def zoom_wide(self, speed):
        """
        Wide zoom at given speed
        :param speed: int between 0 and 15 (hex 0F)
        :return: return code of camera
        """
        if speed > 0xf:
            speed = 0xf
        if speed < 0:
            speed = 0
        pt_tele_bytes = b'\x01\x04\x07' + (0x30 + speed).to_bytes(1, byteorder='big')
        return self.send_command_with_ack(pt_tele_bytes)

    def zoom_direct(self, position):
        """
        Set a direct value to zoom
        :param position: Min value = 0, max value = 2880
        :return:
        """
        self.last_sent_values.update({"zoom": position})
        position_bytes = int_to_nibble(position)
        zoom_bytes = b'\x01\x04\x47' + position_bytes
        return self.send_command_with_ack(zoom_bytes)

    def zoom_query(self):
        zoom_query_bytes = b'\x09\x04\x47'
        zoom_status = self.send_command_with_ack(zoom_query_bytes)
        if zoom_status and zoom_status[1] == 0x50:
            zoom_pos = nibble_to_int(zoom_status[2:6])
            return zoom_pos

    # Focus group of methods
    def focus_stop(self):
        focus_bytes = b'\x01\x04\x08\x00'
        return self.send_command_with_ack(focus_bytes)

    def focus_far(self, speed):
        """
        Move focus to far at given speed
        :param speed: int between 0 and 15 (hex 0F)
        :return: return code of camera
        """
        if speed > 0xf:
            speed = 0xf
        if speed < 0:
            speed = 0
        focus_bytes = b'\x01\x04\x08' + (0x20 + speed).to_bytes(1, byteorder='big')
        return self.send_command_with_ack(focus_bytes)

    def focus_near(self, speed):
        """
        Move focus to near at given speed
        :param speed: int between 0 and 15 (hex 0F)
        :return: return code of camera
        """
        if speed > 0xf:
            speed = 0xf
        if speed < 0:
            speed = 0
        focus_bytes = b'\x01\x04\x08' + (0x30 + speed).to_bytes(1, byteorder='big')
        return self.send_command_with_ack(focus_bytes)

    def focus_direct(self, position):
        """
        Set a direct value to focus
        :param position: Min value = 0, max value = 2880
        :return:
        """
        self.last_sent_values.update({"focus": position})
        position_bytes = int_to_nibble(position + 4096)
        focus_bytes = b'\x01\x04\x48' + position_bytes
        return self.send_command_with_ack(focus_bytes)

    def focus_auto(self):
        focus_bytes = b'\x01\x04\x38\x02'
        return self.send_command_with_ack(focus_bytes)

    def focus_manual(self):
        focus_bytes = b'\x01\x04\x38\x03'
        return self.send_command_with_ack(focus_bytes)

    def focus_query(self):
        focus_bytes = b'\x09\x04\x48'
        focus_status = self.send_command_with_ack(focus_bytes)
        if focus_status and focus_status[1] == 0x50:
            zoom_pos = nibble_to_int(focus_status[2:6])
            return zoom_pos - 4096

    def focus_mode_query(self):
        focus_bytes = b'\x09\x04\x38'
        focus_status = self.send_command_with_ack(focus_bytes)
        if focus_status and focus_status[1] == 0x50:
            if focus_status[2] == 0x02:
                return "Auto"
            elif focus_status[2] == 0x03:
                return "Manual"


# TEST code
if __name__ == '__main__':
    Visca.set_address_with_ack(1)
    Visca.set_address_with_ack(1)
    Visca.set_address_with_ack(1)

    camera = Visca(1, 'Test camera')

    # hex_print(camera.zoom_query())
    # resp = camera.pt_reset()
    # hex_print(resp)
    #
    # resp = camera.zoom_direct(1440)
    # hex_print(resp)
    #
    # time.sleep(2)
    # hex_print(camera.zoom_query())
    #
    # resp = camera.zoom_direct(0)
    # hex_print(resp)
    #
    # time.sleep(2)
    # hex_print(camera.zoom_query())
    #
    # resp = camera.zoom_direct(2880)
    # hex_print(resp)
    #
    # time.sleep(2)
    # hex_print(camera.zoom_query())

    pan, tilt = camera.pt_query()
    print(f"Camera position {pan} {tilt}")

    # resp = camera.pt_down()
    # hex_resp = '|'.join(hex(x) for x in resp)
    # print(hex_resp)

    # time.sleep(3)
    #
    # resp = camera.pt_query()
    # hex_resp = '|'.join(hex(x) for x in resp)
    # print(f"Camera position down {hex_resp}")
    #
    #
    # resp = camera.pt_stop()
    # hex_resp = '|'.join(hex(x) for x in resp)
    # print(hex_resp)
    #
    # resp = camera.pt_query()
    # hex_resp = '|'.join(hex(x) for x in resp)
    # print(f"Camera position {hex_resp}")

    # resp = camera.pt_direct(600, 150)
    # hex_resp = '|'.join(hex(x) for x in resp)
    # print(f"Camera response {hex_resp}")

    # time.sleep(4)
    #
    # resp = camera.pt_query()
    # hex_resp = '|'.join(hex(x) for x in resp)
    # print(f"Camera position {hex_resp}")
    camera.zoom_wide(15)
    time.sleep(2)

    camera.focus_manual()
    camera.focus_far(10)
    time.sleep(4)
    print(camera.focus_query())

    camera.focus_near(10)
    time.sleep(4)
    print(camera.focus_query())

    camera.focus_auto()
    time.sleep(4)
    print(camera.focus_query())
