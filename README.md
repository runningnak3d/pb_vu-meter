# pb_vu-meter
VU Meter for Polybar

This is based on Menno Finlay-Smits Pulse audio monitoring code: https://menno.io/posts/pulseaudio_monitoring/


I still have some work to do, but I figured it was at least in a usable state, and I did find out that PA code is redistributable, so I figured it was time to throw this out there.

You need Python 2, and the python-pulseaudio module.

One of the things I am going to add is auto-detection of the sink, but for now you will have to edit the file and set it. You can find your sink with: pacmd list-sink-inputs

I will alse add some switches for things like changing the bar character, and combining left and right into one file.
