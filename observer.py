import time
import json
import threading
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


class Observer:

    def __init__(self, host, event_callback):
        self.host = host.replace('rtmp://', '').replace('http://', '').replace('https://', '')
        if self.host and self.host[-1] == '/':  # remove if string ends with dash
            self.host = self.host[:-1]

        self.thread = None
        self.is_running = False

        self.event_callback = event_callback
        self.polling_interval = 5  # seconds

    def run(self):
        print('observer started')
        while True:

            try:
                with urlopen('http://' + self.host + '/v1/states') as res:
                    response = json.loads(res.read().decode())

                    status = response['repeat_to_local_nginx']['type']
                    self.handle_status(status)
            except HTTPError as e:
                self.handle_status('http_error')
                print(e)
            except URLError as e:
                if 'Connection refused' in str(e.reason):
                    self.handle_status('server_not_reachable')
                else:
                    self.handle_status('url_error')
                    print('URLError:', e)

            # check if loop should be exited
            start_time = time.time()
            while (time.time()-start_time) < self.polling_interval:
                if not self.is_running:
                    return
                time.sleep(0.5)

    '''
    This function gets called for each request, status contains a string identifier, 
    which gets passed to the event_callback method. The id is one of the following:
    
    [ 'connected', 'connecting', 'stopped', 'error', 'server_not_reachable', 'http_error', 'url_error' ]
    '''
    def handle_status(self, status):
        if self.is_running:
            self.event_callback(status)
        else:
            print('Not sending event_callback with status \'{}\', because observer should be stopped'.format(status))

    def start(self):
        if not self.is_running:
            self.is_running = True

            self.thread = threading.Thread(target=self.run)
            self.thread.start()
        else:
            print('observer already running')

    def stop(self):
        print('stopping observer ...')
        self.is_running = False
        self.thread.join()
