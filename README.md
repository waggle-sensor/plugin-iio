# IIO Plugin

This plugin scans for all Linux IIO subsystem sensors on a device a reports their values.

_Note: This plugin must be deployed in priviledged mode or be able to read `/sys`._

## Usage

The follow parameters are intended for end users:

* `--debug`. Enables debugging level logging.
* `--filter`. Restricts sampling to only IIO devices matching the provided filter. (Ex. `bme680`.)
* `--cache-seconds`. Duration (in seconds) to cache a successful parameter reading and timestamp from sysfs. (Default: 3 seconds)
* `--node-publish-interval`. Interval (in seconds) of how often to publish measurement within the node. (Default: 10 seconds)
* `--beehive-publish-interval`. Interval (in seconds) of how often to publish measurement to cloud. (Default: 30 seconds)

A couple notes relating the cache time and publish time:

* A sensor parameter's read rate is at most `--cache-seconds`. This is intended to limit the number of interactions with the physical sensor.
* If a node and beehive publish occur within `--cache-seconds` of each other, the value _and_ timestamp of the first publish will also be used for the second.
  * This is functionally the same as combining the first and second publishes with a potentially small delay on availability of the second measurement.

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
