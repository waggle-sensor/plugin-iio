import logging
from typing import NamedTuple, List
from ttlcache import TTLCache
from pathlib import Path
from os import PathLike
from waggle.plugin import Plugin, get_timestamp


class FileReader:
    """
    FileReader implements a single read_text method. This is intended to be easily pluggable to help test behavior like caching.
    """

    def read_text(self, name: PathLike) -> str:
        return Path(name).read_text()


class Measurement(NamedTuple):
    """
    Measurement represents a measurement taken for a particular IIO sensor / parameter.
    """
    sensor: str
    param: str
    value: float
    timestamp: int


class IIOItem(NamedTuple):
    """
    IIOItem represents a sensor / parameter with its underlying sysfs path.
    """
    sensor: str
    param: str
    path: Path


def scan_iio_items(root: PathLike):
    for name_path in Path(root).glob("*/name"):
        sensor = name_path.read_text().strip()
        sensor_path = name_path.parent
        for path in sensor_path.glob("in_*_input"):
            param = path.name.strip()
            yield IIOItem(sensor, param, path)


def scan_and_filter_iio_items(root: PathLike, filter_re):
    def sensor_matches_filter(item): return filter_re.search(item.sensor)
    return filter(sensor_matches_filter, scan_iio_items(root))


transform_names = {
    "iio.in_humidityrelative_input": "env.relative_humidity",
    "iio.in_pressure_input": "env.pressure",
    "iio.in_temp_input": "env.temperature",
}


transform_funcs = {
    ("bme280", "iio.in_humidityrelative_input"): lambda x: x / 1000,
    ("bme280", "iio.in_pressure_input"): lambda x: x * 1000,
    ("bme280", "iio.in_temp_input"): lambda x: x / 1000,

    ("bme680", "iio.in_humidityrelative_input"): lambda x: x,
    ("bme680", "iio.in_pressure_input"): lambda x: x * 100,
    ("bme680", "iio.in_temp_input"): lambda x: x / 1000,
}


def transform_iio_to_env_measurements(measurements: List[Measurement]) -> List[Measurement]:
    transformed = []

    for measurement in measurements:
        try:
            transformed_param = transform_names[measurement.param]
            transformed_value = transform_funcs[measurement.sensor, measurement.param](measurement.value)
        except KeyError:
            continue

        transformed.append(Measurement(
            sensor=measurement.sensor,
            param=transformed_param,
            value=transformed_value,
            timestamp=measurement.timestamp,
        ))

    return transformed


class Processor:

    def __init__(self, file_reader: FileReader, plugin: Plugin, rootdir, filter):
        self.logger = logging.getLogger("Processor")
        self.file_reader = file_reader
        self.plugin = plugin
        self.cache = TTLCache()
        self.rootdir = rootdir
        self.filter = filter
        # TODO make its own config ^

    def sample_and_publish(self, scope: str):
        self.logger.info("starting sample and publish for %s", scope)

        self.logger.info("scanning iio items")
        scanned_iio_items = list(scan_and_filter_iio_items(self.rootdir, self.filter))

        # print list of all items for debugging
        self.logger.info("scanned %d iio items", len(scanned_iio_items))
        for item in scanned_iio_items:
            self.logger.debug("scanned iio item: %s", item)

        self.logger.info("getting iio measurements...")
        iio_measurements = self._read_measurements(scanned_iio_items)

        self.logger.info("transforming iio to env measurements...")
        env_measurements = transform_iio_to_env_measurements(iio_measurements)

        measurements = iio_measurements + env_measurements

        self.logger.info("publishing measurements...")
        self._publish_measurements(measurements, scope)
        self.logger.info("published %d measurements (%d iio.*, %d env.*)", len(measurements), len(iio_measurements), len(env_measurements))

        self.logger.info("finished sample and publish for %s", scope)

    def _read_measurement(self, item):
        key = (item.sensor, item.param)

        try:
            return self.cache[key]
        except KeyError:
            pass

        timestamp = get_timestamp()
        text = self.file_reader.read_text(item.path)
        value = float(text)
        measurement = Measurement(
            sensor=item.sensor,
            param=f"iio.{item.param}",
            value=value,
            timestamp=timestamp,
        )

        self.cache.set(key, measurement, ttl=3) # TODO make ttl part of cache
        return measurement

    def _read_measurements(self, iio_items: List[IIOItem]) -> List[Measurement]:
        measurements = []

        for item in iio_items:
            try:
                measurement = self._read_measurement(item)
            except Exception:
                self.logger.exception("failed to read measurement for item: %s", item)
                continue
            measurements.append(measurement)

        return measurements

    def _publish_measurements(self, measurements: List[Measurement], scope: str):
        for measurement in measurements:
            self.plugin.publish(measurement.param, measurement.value, meta={"sensor": measurement.sensor}, timestamp=measurement.timestamp, scope=scope)
