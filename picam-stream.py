#!/usr/bin/python3

import json

from observer import Observer
from streamer import Streamer


class Main:

    def __init__(self):

        self.is_restarted = False
        self.config = self.load_config()

        host = self.config['host']
        stream_token = self.config['stream_token']
        stream_config = self.config['stream_config']

        print('### PICAM-STREAM ###')
        print('streaming to \'{}\''.format(host))

        self.s = Streamer(host, stream_token, stream_config)
        self.o = Observer(host, self.restart_streamer)

    def load_config(self, config_path='./config.json'):
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config

    def restart_streamer(self, status):
        if status in ['stopped', 'error']:
            if not self.is_restarted:
                print('observer reported status \'{}\', restarting stream ...'.format(status))
                self.s.restart_stream()
                self.is_restarted = True
        else:
            self.is_restarted = False

    def start(self):
        self.s.start_stream()
        self.o.start()


if __name__ == '__main__':
    Main().start()
