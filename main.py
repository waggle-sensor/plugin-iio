import os
import argparse
from pathlib import Path
import time
import logging
import re
from waggle.plugin import Plugin
import sched


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


def start_publishing(args, plugin):
    """
    start_publishing begins sampling and publishing iio and transformed env data
    """
    sch = sched.scheduler(time.time, time.sleep)

    def sample_and_publish_task(scope, delay):
        sch.enter(delay, 0, sample_and_publish_task, kwargs={
            "scope": scope,
            "delay": delay,
        })

        logging.info("requesting sample for scope %s", scope)

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
                text = path.read_text().strip()
            except Exception:
                logging.exception("failed to read data for %s %s", sensor_name, name)
                continue

            try:
                value = float(text)
            except Exception:
                logging.info("failed to parse %s %s data %r as numeric", sensor_name, name, text)
                continue

            plugin.publish(f"iio.{name}", value, meta={"sensor": sensor_name, "zone": args.host}, scope=scope)
            logging.debug("published %s with zone %s %s %s", sensor_name, args.host, name, value)
            total_iio_published += 1

            # transform value to standard ontology and units, if possible
            try:
                tfm_name, tfm_value = transform_value(sensor_name, name, value)
            except KeyError:
                logging.debug("no transform for %s %s - skipping", sensor_name, name)
                continue

            plugin.publish(f"env.{tfm_name}", tfm_value, meta={"sensor": sensor_name, "zone": args.host}, scope=scope)
            logging.debug("published transformed value %s with zone %s %s %s", sensor_name, args.host, tfm_name, tfm_value)
            total_env_published += 1

        logging.info("published %d iio.* parameter values", total_iio_published)
        logging.info("published %d env.* parameter values", total_env_published)

    # setup and run publishing schedule
    if args.node_publish_interval > 0:
        sch.enter(0, 0, sample_and_publish_task, kwargs={
            "scope": "node",
            "delay": args.node_publish_interval,
        })

    if args.beehive_publish_interval > 0:
        sch.enter(0, 0, sample_and_publish_task, kwargs={
            "scope": "beehive",
            "delay": args.beehive_publish_interval,
        })

    sch.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootdir", type=Path, default="/sys/bus/iio/devices", help="root iio device directory")
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument("--filter", default="", help="filter sensor name")
    parser.add_argument("--node-publish-interval", default=1.0, type=float, help="interval to publish data to node (negative values disable node publishing)")
    parser.add_argument("--beehive-publish-interval", default=30.0, type=float, help="interval to publish data to beehive (negative values disable beehive publishing)")
    parser.add_argument("--host", default=os.getenv("HOST", ""), type=str, help="full name of the computing host (e.g., 012345678901234-ws-nxcore)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    if args.host == "":
        logging.error("--host is not set")
        exit(1)
    sp = args.host.split("-")
    if len(sp) < 2:
        logging.erorr(f'--host {args.host} is in wrong format')
        exit(1)
    args.host = sp[-1]

    with Plugin() as plugin:
        start_publishing(args, plugin)


if __name__ == "__main__":
    main()
