# picam-stream for Restreamer

This project wants to provide an easy and stable way to stream the video
feed of a Raspberry Pi camera module to a
[Restreamer](https://datarhei.github.io/restreamer/) cloud instance.
Restreamer can redistributed the live feed as HLS stream, so that the
video can be embedded into websites, and also redirect to other
streaming providers like Youtube.

picam-stream actively checks if Restreamer has encountered a problem and
if so restarts the stream.

Currently most of the parameters are fixed

## Install

```bash

sudo apt update && sudo apt upgrade
sudo apt install `ffmpeg python3 python3-pip git`

git clone https://github.com/philipptrenz/restreamer-picam-stream.git picam-stream
cd picam-stream

sudo chmod 755 picam-stream.py

sudo cp picam-stream /etc/init.d/
sudo chmod 755 /etc/init.d/picam-stream
sudo update-rc.d picam-stream defaults
```

## Configure

Create a JSON file in the root of the project directory, which follows
this scheme:

```json
{
  "host": "example.com",
  "stream_token": "abc123",
  "stream_config": {
    "width": 1269,
    "height": 730,
    "fps": 2,
    "raspivid_mode": 4,
    "group_of_pictures": 10,
    "h264_constant_rate_factor": 23
  }
}

```

## Start

```bash
sudo service picam-stream start
``` 

It will also automatically be started on boot.
