import os
import time
import signal
import logging
import threading
import subprocess


class Streamer:

    def __init__(self, host, stream_token, stream_config=None):

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(threadName)s %(levelname)-8s %(message)s')

        self.is_streaming = False
        self.stream_process = None
        self.stream_thread = None
        self.is_forced_stream_stop = False
        self.stream_pid = -1

        self.stream_command = self.get_stream_command(host, stream_token, stream_config)

    def get_stream_command(self, host, stream_token, stream_config):

        cmd = 'raspivid -o - -t 0 -w {2} -h {3} -md {5} -fps {4} -stm -b 1000000 -g {6} | ' \
              'ffmpeg -loglevel warning -re -ar 44100 -ac 2 -acodec pcm_s16le -f s16le -ac 1 -i /dev/zero -f h264 -i - ' \
              '-vcodec copy -acodec aac -ab 64k -g {6} -strict experimental -crf {7} -f ' \
              'flv rtmp://{0}/live/external.stream?token={1}'

        host = self.strip_host_name(host)

        return cmd.format(
            host,
            stream_token,
            stream_config['width'],
            stream_config['height'],
            stream_config['fps'],
            stream_config['raspivid_mode'],
            stream_config['group_of_pictures'],
            stream_config['h264_constant_rate_factor']
        )

    def strip_host_name(self, host):
        host = host.replace('rtmp://', '').replace('http://', '').replace('https://', '')
        if host and host[-1] == '/':
            return host[:-1]  # if host ends with /: strip it off
        else:
            return host

    def start_stream(self):
        if self.is_streaming:
            logging.debug('is already streaming')
            return
        """
        Runs subprocess.Popen, and then calls the function
        self.on_stream_stop when the subprocess completes.
        """
        def run():
            self.stream_thread_proc = subprocess.Popen(
                self.stream_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )

            (out, _) = self.stream_thread_proc.communicate()
            self.log_subprocess_output(out)
            self.stream_pid = self.stream_thread_proc.pid

            self.on_stream_start()

            self.stream_thread_proc.wait()

            self.on_stream_stop()
            return

        if not self.is_streaming:
            self.stream_thread = threading.Thread(target=run, name="streamerThread")
            self.stream_thread.start()
        else:
            logging.debug('already streaming!')

    def on_stream_start(self):
        logging.info('stream started (PID: {})'.format(self.stream_pid))

    def on_stream_stop(self):
        logging.info('stream stopped (PID: {})'.format(self.stream_pid))
        forced = self.is_forced_stream_stop

        self.is_forced_stream_stop = False
        self.is_streaming = False

        if not forced:
            # auto restart stream if it was not forced to stop
            self.restart_stream()

    def log_subprocess_output(self, out):
        logging.warning(out)

    def stop_stream(self):
        self.is_forced_stream_stop = True

        if self.is_streaming:
            logging.debug('stopping streamer ...')
            os.killpg(os.getpgid(self.stream_pid), signal.SIGTERM)

            # wait until stream is not longer streaming
            while self.is_streaming:
                time.sleep(0.5)
        return

    def restart_stream(self):

        if self.is_streaming:
            self.stop_stream()

        if self.is_forced_stream_stop:
            logging.debug('restart requested, but is_forced_stream_stop flag is set')
        else:
            self.is_streaming = True
            self.start_stream()
