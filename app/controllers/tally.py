# coding: utf-8

# noinspection PyUnresolvedReferences
import RPi.GPIO as GPIO

# Set GPIO naming convention
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class Tally:

    def __init__(self, tally_config):
        self.tallies = []
        tally_id = 0
        for tally in tally_config:
            self.tallies = self.tallies + [{'name': tally['name'],
                                            'id': tally_id,
                                            'pgm': tally['ports']['pgm'],
                                            'pvw': tally['ports']['pvw'],
                                            'logic': tally['ports'].get('logic', 'active_high'),
                                            'current_status': 'OFF'}]
            tally_id += 1

        # Initialize ports
        for tally in self.tallies:
            for port in tally['pgm']:
                GPIO.setup(port, GPIO.OUT)
            for port in tally['pvw']:
                GPIO.setup(port, GPIO.OUT)


    def set_tally(self, tally_id, status):
        # Set the tally physical output according to request
        if status == 'pgm':
            if self.tallies[tally_id]['logic'] == 'active_high':
                for port in self.tallies[tally_id]['pvw']:
                    GPIO.output(port, GPIO.LOW)
                for port in self.tallies[tally_id]['pgm']:
                    GPIO.output(port, GPIO.HIGH)
            else:
                for port in self.tallies[tally_id]['pvw']:
                    GPIO.output(port, GPIO.HIGH)
                for port in self.tallies[tally_id]['pgm']:
                    GPIO.output(port, GPIO.LOW)
            self.tallies[tally_id]['current_status'] = 'PGM'
        elif status == 'pvw':
            if self.tallies[tally_id]['logic'] == 'active_high':
                for port in self.tallies[tally_id]['pgm']:
                    GPIO.output(port, GPIO.LOW)
                for port in self.tallies[tally_id]['pvw']:
                    GPIO.output(port, GPIO.HIGH)
            else:
                for port in self.tallies[tally_id]['pgm']:
                    GPIO.output(port, GPIO.HIGH)
                for port in self.tallies[tally_id]['pvw']:
                    GPIO.output(port, GPIO.LOW)
            self.tallies[tally_id]['current_status'] = 'PVW'
        else:
            status = 'off'
            if self.tallies[tally_id]['logic'] == 'active_high':
                for port in self.tallies[tally_id]['pgm']:
                    GPIO.output(port, GPIO.LOW)
                for port in self.tallies[tally_id]['pvw']:
                    GPIO.output(port, GPIO.LOW)
            else:
                for port in self.tallies[tally_id]['pgm']:
                    GPIO.output(port, GPIO.HIGH)
                for port in self.tallies[tally_id]['pvw']:
                    GPIO.output(port, GPIO.HIGH)
            self.tallies[tally_id]['current_status'] = 'OFF'
        return status
