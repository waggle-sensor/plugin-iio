import argparse
from pathlib import Path
import time
import logging
import re
import sched
from waggle.plugin import Plugin
from processor import Processor, FileReader


def schedule_and_run_processor(processor, node_publish_interval, beehive_publish_interval):
    scheduler = sched.scheduler(time.time, time.sleep)

    def call_processor_task(scope, delay):
        scheduler.enter(delay, 0, call_processor_task, kwargs={"scope": scope, "delay": delay})
        processor.sample_and_publish(scope)

    if node_publish_interval > 0:
        scheduler.enter(0, 0, call_processor_task, kwargs={"scope": "node", "delay": node_publish_interval})

    if beehive_publish_interval > 0:
        scheduler.enter(0, 0, call_processor_task, kwargs={"scope": "beehive", "delay": beehive_publish_interval})

    scheduler.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootdir", type=Path, default="/sys/bus/iio/devices", help="root iio device directory")
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument("--filter", default="", type=re.compile, help="filter sensor name")
    parser.add_argument("--cache-seconds", default=3.0, type=float, help="seconds to cache read values")
    parser.add_argument("--node-publish-interval", default=1.0, type=float, help="interval to publish data to node (negative values disable node publishing)")
    parser.add_argument("--beehive-publish-interval", default=30.0, type=float, help="interval to publish data to beehive (negative values disable beehive publishing)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    file_reader = FileReader()

    with Plugin() as plugin:
        processor = Processor(
            file_reader=file_reader,
            plugin=plugin,
            rootdir=args.rootdir,
            filter=args.filter,
        )

        schedule_and_run_processor(
            processor=processor,
            node_publish_interval=args.node_publish_interval,
            beehive_publish_interval=args.beehive_publish_interval,
        )


if __name__ == "__main__":
    main()
