# IIO Plugin

This plugin scans for all Linux IIO subsystem sensors on a device a reports their values.

_Note: This plugin must be deployed in priviledged mode or be able to read `/sys`._


## TODOs and Notes

* Decide if BME680 should be split into specialized plugin based on requirements. (Ex. if we
need to read values in a specific order.)

Background on this:

We noticed certain spiking behavior when the node and beehive reads overlapped. It turns
out that the sensor isn't really meant to be read faster than every 3s. To address this we:
1. Backed off the local node publish interval.
2. Added read caching so that if the node and beehive reads occur with --cache-seconds of each other,
   the cached value and timestamp are used instead of rereading the sensor.

In my opinion, this is more of a hack to remove spiking until the requirements are better understood.
