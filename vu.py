#!/usr/bin/env python2
from __future__ import print_function
from __future__ import absolute_import
import argparse
import sys
import re
import time
from Queue import Queue
from ctypes import POINTER, c_ubyte, c_void_p, c_ulong, cast

# From https://github.com/Valodim/python-pulseaudio
from pulseaudio.lib_pulseaudio import *
from six.moves import range

SINK_NAME = 'alsa_output.pci-0000_02_02.0.analog-stereo'  # edit to match your sink
METER_RATE = 344
MAX_SAMPLE_VALUE = 127
DISPLAY_SCALE = 5
BAR_LEN = 24
BAR_CHAR = '='
BAR_PAD_CHAR = '='

class PeakMonitor(object):

    def __init__(self, sink_name, rate):
        self.sink_name = sink_name
        self.rate = rate

        # Wrap callback methods in appropriate ctypefunc instances so
        # that the Pulseaudio C API can call them
        self._context_notify_cb = pa_context_notify_cb_t(self.context_notify_cb)
        self._sink_info_cb = pa_sink_info_cb_t(self.sink_info_cb)
        self._stream_read_cb = pa_stream_request_cb_t(self.stream_read_cb)

        # stream_read_cb() puts peak samples into this Queue instance
        self._samples = Queue()

        # Create the mainloop thread and set our context_notify_cb
        # method to be called when there's updates relating to the
        # connection to Pulseaudio
        _mainloop = pa_threaded_mainloop_new()
        _mainloop_api = pa_threaded_mainloop_get_api(_mainloop)
        context = pa_context_new(_mainloop_api, 'peak_demo')
        pa_context_set_state_callback(context, self._context_notify_cb, None)
        pa_context_connect(context, None, 0, None)
        pa_threaded_mainloop_start(_mainloop)

    def __iter__(self):
        while True:
            yield self._samples.get()

    def context_notify_cb(self, context, _):
        state = pa_context_get_state(context)

        if state == PA_CONTEXT_READY:
            # Connected to Pulseaudio. Now request that sink_info_cb
            # be called with information about the available sinks.
            o = pa_context_get_sink_info_list(context, self._sink_info_cb, None)
            pa_operation_unref(o)


    def sink_info_cb(self, context, sink_info_p, _, __):
        if not sink_info_p:
            return

        sink_info = sink_info_p.contents

        if sink_info.name == self.sink_name:
            # Found the sink we want to monitor for peak levels.
            # Tell PA to call stream_read_cb with peak samples.
            samplespec = pa_sample_spec()
            samplespec.channels = 1
            samplespec.format = PA_SAMPLE_U8
            samplespec.rate = self.rate

            pa_stream = pa_stream_new(context, "peak detect demo", samplespec, None)
            pa_stream_set_read_callback(pa_stream,
                                        self._stream_read_cb,
                                        sink_info.index)
            pa_stream_connect_record(pa_stream,
                                     sink_info.monitor_source_name,
                                     None,
                                     PA_STREAM_PEAK_DETECT)

    def stream_read_cb(self, stream, length, index_incr):
        data = c_void_p()
        pa_stream_peek(stream, data, c_ulong(length))
        data = cast(data, POINTER(c_ubyte))
        for i in range(length):
            # When PA_SAMPLE_U8 is used, samples values range from 128
            # to 255 because the underlying audio data is signed but
            # it doesn't make sense to return signed peaks.
            self._samples.put(data[i] - 128)
        pa_stream_drop(stream)

parser = argparse.ArgumentParser(description='VU Meter for Polybar')
parser.add_argument("-l", "--left", action="store_true",
        help="Display left meter")
parser.add_argument("-r", "--right", action="store_true",
        help="Display right meter")

def main():
        args = parser.parse_args()

        c = ['%{{F#338399}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#338399}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#338399}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#4295A7}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#4295A7}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#4295A7}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#45A1B4}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#45A1B4}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#45A1B4}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#38B5C1}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#38B5C1}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#38B5C1}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#17B1B3}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#17B1B3}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#17B1B3}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#08C1C0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#08C1C0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#08C1C0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#48D7D1}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#48D7D1}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#48D7D1}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#A7FEF5}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#A7FEF5}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#A7FEF5}}{}%{{F-}}'.format(BAR_CHAR)
            ]

        while (True):
            monitor = PeakMonitor(SINK_NAME, METER_RATE)
            for sample in monitor:
                 sample = sample / DISPLAY_SCALE
                 if not sample == 0:
                     bar_pad = '%{{F#3F4551}}{}%{{F-}}'.format(BAR_PAD_CHAR)
                     if sample > BAR_LEN:
                        sample = BAR_LEN
                     if args.right:
                         c_out = c[-24:-sample] # Right
                         c_out = (c_out + BAR_LEN * [bar_pad])[:BAR_LEN]
                         c_out = reversed(c_out) # Right
                     else:
                         c_out = c[0:sample] # Left
                         c_out = (c_out + BAR_LEN * [bar_pad])[:BAR_LEN]
                         c_out = "".join(c_out)
                     print("".join(c_out))
                     #print(c_out)
                     sys.stdout.flush()
                     #time.sleep(0.0005) # Polybar needs a couple of microseconds to think ;)
                 else:
                     print ("%{F#3F4551}========================%{F-}")
                     continue

if __name__ == '__main__':
    main()
