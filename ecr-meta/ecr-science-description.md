# IIO Sensor Data Collector

Linux provides an Industrial IO (IIO) subsystem which supports a large variety of sensors. Some examples we've used are:

* BME280 / BME680: Provide temperature, relative humidity and atmospheric pressure.

This edge app automatically scans for available sensors and publishes their data.
