import argparse
from pathlib import Path
import time
import logging
import waggle.plugin as plugin
import re


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
    ("bme280", "in_humidityrelative_input"): lambda x: x/1000,
    ("bme280", "in_pressure_input"): lambda x: x*1000,
    ("bme280", "in_temp_input"): lambda x: x/1000,

    ("bme680", "in_humidityrelative_input"): lambda x: x,
    ("bme680", "in_pressure_input"): lambda x: x*100,
    ("bme680", "in_temp_input"): lambda x: x/1000,
}


def transform_value(sensor_name, name, value):
    return transform_names[name], transform_funcs[sensor_name, name](value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootdir", type=Path, default="/sys/bus/iio/devices", help="root iio device directory")
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument("--rate", default=30.0, type=float, help="sampling rate")
    parser.add_argument("--scope", default="all", choices=["all", "node", "beehive"], help="publish scope")
    parser.add_argument("--filter", default="", help="filter sensor name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(message)s",
                        datefmt="%Y/%m/%d %H:%M:%S")

    logging.info("will scan and publish iio sensor values every %ss", args.rate)

    plugin.init()

    while True:
        time.sleep(args.rate)

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
                text = path.read_text()
            except Exception:
                logging.exception("failed to read data for %s %s", sensor_name, name)
                continue

            # clean up value to make it easier to read if parse to numeric fails
            text = text.strip()

            try:
                value = float(text)
            except Exception:
                logging.info("failed to parse %s %s data %r as numeric", sensor_name, name, text)
                continue

            plugin.publish(f"iio.{name}", value, meta={"sensor": sensor_name}, scope=args.scope)
            logging.debug("published %s %s %s", sensor_name, name, value)
            total_iio_published += 1

            # transform value to standard ontology and units, if possible
            try:
                tfm_name, tfm_value = transform_value(sensor_name, name, value)
            except KeyError:
                logging.debug("no transform for %s %s - skipping", sensor_name, name)
                continue

            plugin.publish(f"env.{tfm_name}", tfm_value, meta={"sensor": sensor_name}, scope=args.scope)
            logging.debug("published transformed value %s %s %s", sensor_name, tfm_name, tfm_value)
            total_env_published += 1

        logging.info("published %d iio.* parameter values", total_iio_published)
        logging.info("published %d env.* parameter values", total_env_published)

if __name__ == "__main__":
    main()
