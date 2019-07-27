#!/usr/bin/python3

import json
import signal

from observer import Observer
from streamer import Streamer


class Main:

    def __init__(self):

        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

        self.is_restarted = False
        self.config = self.load_config()

        host = self.config['host']
        stream_token = self.config['stream_token']
        stream_config = self.config['stream_config']

        self.previous_status = ""

        print('### PICAM-STREAM ###')
        print('streaming to \'{}\''.format(host))

        self.s = Streamer(host, stream_token, stream_config)
        self.o = Observer(host, self.observer_event_handler)

    def load_config(self, config_path='./config.json'):
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config

    def observer_event_handler(self, status):

        if self.previous_status != status: # status has changed
            print('observer reported status \'{}\''.format(status))
            self.previous_status = status

        if status in ['stopped', 'error']:
            if not self.is_restarted:
                print('restarting stream ...'.format(status))
                self.s.restart_stream()
                self.is_restarted = True
        else:
            self.is_restarted = False

    def start(self):
        self.o.start()

    def exit(self):
        print('SIGTERM or SIGINT was signaled, exiting')

        self.s.stop_stream()
        self.o.stop()

        exit(0)


if __name__ == '__main__':
    Main().start()
