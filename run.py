import time
import serial


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

def hex_print(bytes_array):
    print('|'.join(hex(x) for x in bytes_array))

class Visca():

    def __init__(self, address):
        self.ser = serial.Serial('COM4', 9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=1, timeout=1)
        self.address = address

    def send_command_with_ack(self, hex_bytes):
        self.ser.write(self.address + hex_bytes + b'\xff')
        return self.ser.read(50)

    # PAN-TILT group of methods
    def pt_stop(self):
        pt_stop_bytes = b'\x01\x06\x01\x03\x03\x03\x03'
        return self.send_command_with_ack(pt_stop_bytes)

    def pt_reset(self):
        pt_reset_bytes = b'\x01\x06\x05'
        return self.send_command_with_ack(pt_reset_bytes)

    def pt_up(self):
        pt_right_bytes = b'\x01\x06\x01\x00\x00\x03\x01'
        return self.send_command_with_ack(pt_right_bytes)

    def pt_down(self):
        pt_right_bytes = b'\x01\x06\x01\x00\x00\x03\x02'
        return self.send_command_with_ack(pt_right_bytes)

    def pt_left(self):
        pt_right_bytes = b'\x01\x06\x01\x00\x00\x01\x03'
        return self.send_command_with_ack(pt_right_bytes)

    def pt_right(self):
        pt_right_bytes = b'\x01\x06\x01\x00\x00\x02\x03'
        return self.send_command_with_ack(pt_right_bytes)

    def pt_direct(self, pan_pos, tilt_pos):
        """

        :param pan_pos: left=0, middle=408, right=816
        :param tilt_pos: down=0, middle=126, up=212
        :return:
        """
        pan_string = int_to_nibble(pan_pos)
        tilt_string = int_to_nibble(tilt_pos)
        pt_direct_bytes = b'\x01\x06\x02\x00\x00' + pan_string + tilt_string
        print('|'.join(hex(x) for x in pt_direct_bytes))
        return self.send_command_with_ack(pt_direct_bytes)

    def pt_query(self):
        pt_reset_bytes = b'\x09\x06\x12'
        return self.send_command_with_ack(pt_reset_bytes)

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
        hex_print(pt_tele_bytes)
        return self.send_command_with_ack(pt_tele_bytes)

    def zoom_direct(self, position):
        """
        Set a direct value to zoom
        :param position: Min value = 0, max value = 2880
        :return:
        """
        position_bytes = int_to_nibble(position)
        zoom_bytes = b'\x01\x04\x47' + position_bytes
        hex_print(zoom_bytes)
        return self.send_command_with_ack(zoom_bytes)

    def zoom_query(self):
        pt_reset_bytes = b'\x09\x04\x47'
        return self.send_command_with_ack(pt_reset_bytes)

# TEST code
if __name__ == '__main__':
    camera = Visca(b'\x81')

    hex_print(camera.zoom_query())
    resp = camera.pt_reset()
    hex_print(resp)

    resp = camera.zoom_direct(1440)
    hex_print(resp)

    time.sleep(2)
    hex_print(camera.zoom_query())

    resp = camera.zoom_direct(0)
    hex_print(resp)

    time.sleep(2)
    hex_print(camera.zoom_query())

    resp = camera.zoom_direct(2880)
    hex_print(resp)

    time.sleep(2)
    hex_print(camera.zoom_query())

    resp = camera.pt_query()
    hex_resp = '|'.join(hex(x) for x in resp)
    print(f"Camera position {hex_resp}")

    resp = camera.pt_down()
    hex_resp = '|'.join(hex(x) for x in resp)
    print(hex_resp)

    time.sleep(3)

    resp = camera.pt_query()
    hex_resp = '|'.join(hex(x) for x in resp)
    print(f"Camera position down {hex_resp}")


    resp = camera.pt_stop()
    hex_resp = '|'.join(hex(x) for x in resp)
    print(hex_resp)

    resp = camera.pt_query()
    hex_resp = '|'.join(hex(x) for x in resp)
    print(f"Camera position {hex_resp}")

    # resp = camera.pt_direct(600, 150)
    # hex_resp = '|'.join(hex(x) for x in resp)
    # print(f"Camera response {hex_resp}")

    time.sleep(4)

    resp = camera.pt_query()
    hex_resp = '|'.join(hex(x) for x in resp)
    print(f"Camera position {hex_resp}")
