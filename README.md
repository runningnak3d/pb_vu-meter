# pb_vu-meter
VU Meter for Polybar

This is based on Menno Finlay-Smits Pulse audio monitoring code: https://menno.io/posts/pulseaudio_monitoring/


I still have some work to do, but I figured it was at least in a usable state, and I did find out that PA code is redistributable, so I figured it was time to throw this out there.

You need Python 2 because unfortunately I don't have time to port this to Python 3.

One of the things I am going to add is auto-detection of the sink, but for now you will have to edit the file and set it. You can find your sink with: pacmd list-sink-inputs

The -r option to display the right meter is for display purposes only to display on the right side of the screen. I just don't have time to finish this so left and right are processed seperately.
