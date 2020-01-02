#!/bin/python2
from __future__ import print_function
import sys
import re
import time
from Queue import Queue
from ctypes import POINTER, c_ubyte, c_void_p, c_ulong, cast

# From https://github.com/Valodim/python-pulseaudio
from pulseaudio.lib_pulseaudio import *

SINK_NAME = 'alsa_output.pci-0000_00_1f.3.analog-stereo'  # edit to match your sink
METER_RATE = 344
MAX_SAMPLE_VALUE = 127
DISPLAY_SCALE = 5
BAR_LEN = 24
BAR_CHAR = '='

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
        for i in xrange(length):
            # When PA_SAMPLE_U8 is used, samples values range from 128
            # to 255 because the underlying audio data is signed but
            # it doesn't make sense to return signed peaks.
            self._samples.put(data[i] - 128)
        pa_stream_drop(stream)

def main():

        c = ['%{{F#080}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#090}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#0a0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#0b0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#0c0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#0d0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#0e0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#0f0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#fd0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#fe0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#ff0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#ff0}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#f90}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#f80}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#f70}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#f60}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#f00}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#e00}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#d00}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#c00}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#b00}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#a00}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#900}}{}%{{F-}}'.format(BAR_CHAR),
             '%{{F#800}}{}%{{F-}}'.format(BAR_CHAR)
            ]

        monitor = PeakMonitor(SINK_NAME, METER_RATE)
        for sample in monitor:
             sample = sample / DISPLAY_SCALE
             if sample > BAR_LEN:
                sample = BAR_LEN
#             c_out = c[-24:-sample] # Right
#             c_out = reversed(c_out) # Right
             c_out = c[0:sample] # Left
             c_out = (c_out + BAR_LEN * ['%{F#060}=%{F-}'])[:BAR_LEN]
             print(*c_out)
             sys.stdout.flush()
             time.sleep(0.0005) # Polybar needs a couple of microseconds to think ;)

if __name__ == '__main__':
    main()
