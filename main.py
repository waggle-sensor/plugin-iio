import argparse
from pathlib import Path
import time
import logging
import re
from waggle.plugin import Plugin, get_timestamp
import sched
from ttlcache import TTLCache

# TODO(sean) Decide if BME680 should be split into specialized plugin based on requirements. (Ex. if we
# need to read values in a specific order.)
#
# Background on this:
#
# We noticed certain spiking behavior when the node and beehive reads overlapped. It turns
# out that the sensor isn't really meant to be read faster than every 3s. To address this we:
#
# 1. Backed off the local node publish interval.
#
# 2. Added read caching so that if the node and beehive reads occur with --cache-seconds of each other,
#    the cached value and timestamp are used instead of rereading the sensor.
#
# In my opinion, this is more of a hack to remove spiking until the requirements are better understood.

def build_iio_param_set(rootdir, filter=""):
    filterRE = re.compile(filter)

    results = set()

    for name_path in Path(rootdir).glob("*/name"):
        sensor_name = name_path.read_text().strip()
        if not filterRE.search(sensor_name):
            continue
        sensor_path = name_path.parent
        for path in sensor_path.glob("in_*_input"):
            name = path.name.strip()
            results.add((sensor_name, name, path))

    return results


transform_names = {
    "in_humidityrelative_input": "relative_humidity",
    "in_pressure_input": "pressure",
    "in_temp_input": "temperature",
}


transform_funcs = {
    ("bme280", "in_humidityrelative_input"): lambda x: x / 1000,
    ("bme280", "in_pressure_input"): lambda x: x * 1000,
    ("bme280", "in_temp_input"): lambda x: x / 1000,
    ("bme680", "in_humidityrelative_input"): lambda x: x,
    ("bme680", "in_pressure_input"): lambda x: x * 100,
    ("bme680", "in_temp_input"): lambda x: x / 1000,
}


def transform_value(sensor_name, name, value):
    return transform_names[name], transform_funcs[sensor_name, name](value)


def read_float_from_path(path: Path) -> float:
    return float(path.read_text().strip())


def start_publishing(args, plugin):
    """
    start_publishing begins sampling and publishing iio and transformed env data
    """
    # setup cached read function get_value_and_timestamp
    cache = TTLCache()

    def get_value_and_timestamp(sensor_name, name, path):
        try:
            value, timestamp = cache[(sensor_name, name)]
            logging.info("using cached reading for %s %s: %s @ %s", sensor_name, name, value, timestamp)
            return value, timestamp
        except KeyError:
            pass

        # get timestamp and value
        logging.info("reading value for %s %s", sensor_name, name)
        timestamp = get_timestamp()
        value = read_float_from_path(path)

        # cache newly read value
        cache.set((sensor_name, name), (value, timestamp), ttl=args.cache_seconds)

        return value, timestamp

    # setup main scheduler loop
    scheduler = sched.scheduler(time.time, time.sleep)

    def sample_and_publish_task(scope, delay):
        scheduler.enter(delay, 0, sample_and_publish_task, kwargs={
            "scope": scope,
            "delay": delay,
        })

        logging.info("starting sample and publish for %s", scope)

        logging.info("scanning device tree")
        param_set = build_iio_param_set(args.rootdir, args.filter)

        logging.info("detected %d device parameters", len(param_set))
        for sensor_name, name, _ in param_set:
            logging.debug("detected sensor %r param %r", sensor_name, name)

        logging.info("publishing parameters")

        total_iio_published = 0
        total_env_published = 0

        for sensor_name, name, path in param_set:
            try:
                value, timestamp = get_value_and_timestamp(sensor_name, name, path)
            except Exception:
                logging.exception("failed to read data for %s %s", sensor_name, name)
                continue

            plugin.publish(f"iio.{name}", value, meta={"sensor": sensor_name}, scope=scope, timestamp=timestamp)
            logging.debug("published %s %s %s", sensor_name, name, value)
            total_iio_published += 1

            # transform value to standard ontology and units, if possible
            try:
                tfm_name, tfm_value = transform_value(sensor_name, name, value)
            except KeyError:
                logging.debug("no transform for %s %s - skipping", sensor_name, name)
                continue

            plugin.publish(f"env.{tfm_name}", tfm_value, meta={"sensor": sensor_name}, scope=scope)
            logging.debug("published transformed value %s %s %s", sensor_name, tfm_name, tfm_value)
            total_env_published += 1

        logging.info("published %d iio.* parameter values", total_iio_published)
        logging.info("published %d env.* parameter values", total_env_published)
        logging.info("finished sample and publish for %s", scope)

    # setup and run publishing schedule
    if args.node_publish_interval > 0:
        scheduler.enter(0, 0, sample_and_publish_task, kwargs={
            "scope": "node",
            "delay": args.node_publish_interval,
        })

    if args.beehive_publish_interval > 0:
        scheduler.enter(0, 0, sample_and_publish_task, kwargs={
            "scope": "beehive",
            "delay": args.beehive_publish_interval,
        })

    scheduler.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootdir", type=Path, default="/sys/bus/iio/devices", help="root iio device directory")
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument("--filter", default="", help="filter sensor name")
    parser.add_argument("--cache-seconds", default=3.0, type=float, help="seconds to cache read values")
    parser.add_argument("--node-publish-interval", default=1.0, type=float, help="interval to publish data to node (negative values disable node publishing)")
    parser.add_argument("--beehive-publish-interval", default=30.0, type=float, help="interval to publish data to beehive (negative values disable beehive publishing)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    with Plugin() as plugin:
        start_publishing(args, plugin)


if __name__ == "__main__":
    main()
