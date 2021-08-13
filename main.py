import argparse
from pathlib import Path
import time
import logging
import waggle.plugin as plugin


def build_iio_param_list(rootdir):
    param_list = []
    for name_path in Path(rootdir).glob("*/name"):
        sensor_name = name_path.read_text().strip()
        sensor_path = name_path.parent

        for path in sensor_path.glob("in_*_input"):
            name = path.name.strip()
            param_list.append((sensor_name, name, path))

    return param_list


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootdir", type=Path, default="/sys/bus/iio/devices", help="root iio device directory")
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument("--rate", default=30.0, type=float, help="sampling rate")
    parser.add_argument("--scope", default="all", choices=["all", "node", "beehive"], help="publish scope")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(message)s",
                        datefmt="%Y/%m/%d %H:%M:%S")

    param_list = build_iio_param_list(args.rootdir)

    for sensor_name, name, _ in param_list:
        logging.info("detected sensor %r param %r", sensor_name, name)

    logging.info("will scan and publish iio sensor values every %ss", args.rate)

    plugin.init()

    while True:
        time.sleep(args.rate)
        for sensor_name, name, path in param_list:
            value = float(path.read_text())
            plugin.publish(f"iio.{name}", value, meta={"sensor": sensor_name}, scope=args.scope)
            logging.debug("published %s %s %s", sensor_name, name, value)

if __name__ == "__main__":
    main()
