import os
import time
import signal
import logging
import threading
import subprocess


class Streamer:

    def __init__(self, host, stream_token, stream_config=None):

        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s %(levelname)-8s %(message)s')

        self.is_streaming = False
        self.stream_process = None
        self.stream_thread = None
        self.stream_pid = -1

        self.do_auto_restart = True
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

    def restart_stream(self):
        if self.is_streaming:
            logging.warning('is already streaming!')
            return
        else:
            self.is_streaming = True

        """
        Runs subprocess.Popen, and then calls the function
        self.on_stream_stop when the subprocess completes.
        """
        def run():
            logging.debug('test0')

            self.stream_thread_proc = subprocess.Popen(
                self.stream_command,
                shell=True,
                preexec_fn=os.setsid
            )
            self.stream_pid = self.stream_thread_proc.pid
            self.on_stream_start()

            threading.Thread(target=self.log_subprocess_output, name="StreamerLogThread").start()
            #self.log_subprocess_output()

            logging.debug('test1')


            return_code = self.stream_thread_proc.wait()

            logging.debug('test2')

            logging.info('stream process terminated with return code {}'.format(return_code))

            self.on_stream_stop()

            logging.debug('test3')

            return

        self.stream_thread = threading.Thread(target=run, name="StreamerThread")
        self.stream_thread.start()

    def on_stream_start(self):
        logging.info('stream started (PID: {})'.format(self.stream_pid))

    def on_stream_stop(self):
        logging.info('stream stopped (PID: {})'.format(self.stream_pid))
        self.is_streaming = False

        if self.do_auto_restart:
            self.restart_stream()

        # reset to auto restart
        self.do_auto_restart = True

    def start_stream(self):
        self.restart_stream()

    def stop_stream(self):
        if self.is_streaming:
            logging.info('stopping streamer ...')

            self.do_auto_restart = False

            if self.stream_pid == -1:
                logging.error('stream PID is not yet set, cannot kill')

            try:
                logging.debug('about to kill stream with PID {}'.format(self.stream_pid))
                os.killpg(os.getpgid(self.stream_pid), signal.SIGTERM)
            except Exception as e:
                logging.error(e)

            # wait until not longer streaming
            while self.is_streaming:
                logging.debug('waiting for streaming finished')
                time.sleep(0.5)
            return
        else:
            logging.warning('asked to stop, but not streaming')
            return

    def log_subprocess_output(self):
        (out, _) = self.stream_thread_proc.communicate()
        logging.warning(out)
