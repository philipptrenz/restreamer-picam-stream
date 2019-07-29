#!/usr/bin/python3

import json
import signal
import logging

from observer import Observer
from streamer import Streamer


class Main:

    def __init__(self):

        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s\t%(levelname)-8s\t%(message)s')

        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

        self.is_restarted = False
        self.config = self.load_config()

        host = self.config['host']
        stream_token = self.config['stream_token']
        stream_config = self.config['stream_config']

        self.previous_status = ""

        logging.info('### PICAM-STREAM ###')
        logging.info('streaming to \'{}\''.format(host))

        self.s = Streamer(host, stream_token, stream_config)
        self.o = Observer(host, self.observer_event_handler)

    def load_config(self, config_path='./config.json'):
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config

    def observer_event_handler(self, status):

        if self.previous_status != status: # status has changed
            logging.debug('observer reported status \'{}\''.format(status))
            self.previous_status = status

        if status in ['disconnected', 'stopped', 'error']:
            if not self.is_restarted:
                logging.warning('(re)starting stream ...'.format(status))
                self.s.restart_stream()
                self.is_restarted = True
        else:
            self.is_restarted = False

    def start(self):
        self.o.start()

    def exit(self, signum, frame):
        logging.debug('SIGTERM was sent, exiting')

        self.o.stop()
        self.s.stop_stream()

        logging.info('bye!')

if __name__ == '__main__':
    Main().start()
