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

    param_set = build_iio_param_set(args.rootdir, args.filter)

    for sensor_name, name, _ in param_set:
        logging.info("detected sensor %r param %r", sensor_name, name)

    logging.info("will scan and publish iio sensor values every %ss", args.rate)

    plugin.init()

    while True:
        time.sleep(args.rate)
        for sensor_name, name, path in param_set:
            text = path.read_text()

            try:
                value = float(text)
            except ValueError:
                logging.info("failed to parse %s %s data %s as numeric", sensor_name, name, text)
                continue

            plugin.publish(f"iio.{name}", value, meta={"sensor": sensor_name}, scope=args.scope)
            logging.debug("published %s %s %s", sensor_name, name, value)

if __name__ == "__main__":
    main()
