import unittest
import re
from main import Processor, FileReader
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import ExitStack
from unittest.mock import MagicMock
from typing import NamedTuple


def make_test_filesystem(root, tree):
    root = TemporaryDirectory()

    for device, items in tree:
        for name, text in items:
            path = Path(root, device, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    return root


class TestProcessor(unittest.TestCase):

    def setUp(self):
        self.exit_stack = ExitStack()
        self.root = self.exit_stack.enter_context(make_test_filesystem([
            ("iio:device0", [
                ("name", "ina3221x\n"),
                ("in_voltage0_input", "123\n"),
                ("in_current1_input", "4321\n"),
                # NOTE This file has invalid contents and should be included as part of the test case to probe caching behavior.
                ("in_invalid_value_input", "0 ma\n"),
            ]),
            ("iio:device1", [
                ("name", "bme280\n"),
                ("in_humidityrelative_input", "9627\n"),
                ("in_pressure_input", "99.198292968\n"),
                ("in_temp_input", "52680\n"),
            ]),
            ("iio:device2", [
                ("name", "bme680\n"),
                ("in_humidityrelative_input", "65.129000000\n"),
                ("in_resistance_input", "38846\n"),
                ("in_pressure_input", "992.780000000\n"),
                ("in_temp_input", "25430\n"),
            ]),
            ("iio:device3", [
                # NOTE This device is missing a name and should not be read.
                ("in_missing_name_input", "0\n"),
            ]),
        ])

    def tearDown(self):
        self.exit_stack.close()
    
    def setUpTestFilesystem(self, tree):
        root = self.exit_stack.enter_context(TemporaryDirectory())

        for device, items in tree:
            for name, text in items:
                path = Path(root, device, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
        
        return root
    
    def test_processor_publish_node(self):
        plugin = MockPlugin()
        processor = Processor(
            file_reader=FileReader(),
            plugin=plugin,
            rootdir=self.root,
            filter=re.compile(""),
        )
        processor.logger.disabled = True

        processor.sample_and_publish("node")

        for call in plugin.publish.call_args_list:
            del call.kwargs["timestamp"]

        want_publish = [
            ('iio.in_humidityrelative_input', 65.129, {"meta": {'sensor': 'bme680'}, "scope": 'node'}),
        ]

        plugin.publish.assert_any_call('iio.in_humidityrelative_input', 65.129, meta={'sensor': 'bme680'}, scope='node')
        plugin.publish.assert_any_call('iio.in_resistance_input', 38846.0, meta={'sensor': 'bme680'}, scope='node')
        plugin.publish.assert_any_call('iio.in_pressure_input', 992.78, meta={'sensor': 'bme680'}, scope='node')
        plugin.publish.assert_any_call('iio.in_temp_input', 25430.0, meta={'sensor': 'bme680'}, scope='node')
        plugin.publish.assert_any_call('iio.in_voltage0_input', 123.0, meta={'sensor': 'ina3221x'}, scope='node')
        plugin.publish.assert_any_call('iio.in_current1_input', 4321.0, meta={'sensor': 'ina3221x'}, scope='node')
        plugin.publish.assert_any_call('iio.in_humidityrelative_input', 9627.0, meta={'sensor': 'bme280'}, scope='node')
        plugin.publish.assert_any_call('iio.in_pressure_input', 99.198292968, meta={'sensor': 'bme280'}, scope='node')
        plugin.publish.assert_any_call('iio.in_temp_input', 52680.0, meta={'sensor': 'bme280'}, scope='node')
        plugin.publish.assert_any_call('env.relative_humidity', 65.129, meta={'sensor': 'bme680'}, scope='node')
        plugin.publish.assert_any_call('env.pressure', 99278.0, meta={'sensor': 'bme680'}, scope='node')
        plugin.publish.assert_any_call('env.temperature', 25.43, meta={'sensor': 'bme680'}, scope='node')
        plugin.publish.assert_any_call('env.relative_humidity', 9.627, meta={'sensor': 'bme280'}, scope='node')
        plugin.publish.assert_any_call('env.pressure', 99198.29296800001, meta={'sensor': 'bme280'}, scope='node')
        plugin.publish.assert_any_call('env.temperature', 52.68, meta={'sensor': 'bme280'}, scope='node')

    def test_processor_publish_node(self):
        plugin = MockPlugin()
        processor = Processor(
            file_reader=FileReader(),
            plugin=plugin,
            rootdir=self.root,
            filter=re.compile(""),
        )
        processor.logger.disabled = True

        processor.sample_and_publish("beehive")

        for call in plugin.publish.call_args_list:
            del call.kwargs["timestamp"]

        plugin.publish.assert_any_call('iio.in_humidityrelative_input', 65.129, meta={'sensor': 'bme680'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_resistance_input', 38846.0, meta={'sensor': 'bme680'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_pressure_input', 992.78, meta={'sensor': 'bme680'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_temp_input', 25430.0, meta={'sensor': 'bme680'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_voltage0_input', 123.0, meta={'sensor': 'ina3221x'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_current1_input', 4321.0, meta={'sensor': 'ina3221x'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_humidityrelative_input', 9627.0, meta={'sensor': 'bme280'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_pressure_input', 99.198292968, meta={'sensor': 'bme280'}, scope='beehive')
        plugin.publish.assert_any_call('iio.in_temp_input', 52680.0, meta={'sensor': 'bme280'}, scope='beehive')
        plugin.publish.assert_any_call('env.relative_humidity', 65.129, meta={'sensor': 'bme680'}, scope='beehive')
        plugin.publish.assert_any_call('env.pressure', 99278.0, meta={'sensor': 'bme680'}, scope='beehive')
        plugin.publish.assert_any_call('env.temperature', 25.43, meta={'sensor': 'bme680'}, scope='beehive')
        plugin.publish.assert_any_call('env.relative_humidity', 9.627, meta={'sensor': 'bme280'}, scope='beehive')
        plugin.publish.assert_any_call('env.pressure', 99198.29296800001, meta={'sensor': 'bme280'}, scope='beehive')
        plugin.publish.assert_any_call('env.temperature', 52.68, meta={'sensor': 'bme280'}, scope='beehive')

    def test_cache(self):
        file_reader = AccountingFileReader(FileReader())
        plugin = MockPlugin()

        # ah... we can further separate the scheduling aspect from the core processor by 

        processor = Processor(
            file_reader=file_reader,
            plugin=plugin,
            rootdir=self.root,
            filter=re.compile(""),
        )
        processor.logger.disabled = True

        # run two iterations of plugin
        processor.sample_and_publish("node")
        processor.sample_and_publish("beehive")

        # assert that all file have been read exactly once
        for name, count in file_reader.read_count.items():
            self.assertEqual(count, 1, f"must have exactly one read for file {name}")


class MockPublishNoTimestamp(NamedTuple):
    name: str
    value: any
    scope: str
    meta: dict


class MockPlugin:

    def __init__(self):
        self.published = [] 


class AccountingFileReader:
    """
    AccountingFileReader implements FileReader behavior and additionally tracks
    the number of times each file has been read to aid testing.
    """

    def __init__(self, file_reader):
        self.file_reader = file_reader
        self.read_count = {}

    def read_text(self, name):
        self.read_count[name] = self.read_count.get(name, 0) + 1
        return self.file_reader.read_text(name)


if __name__ == "__main__":
    unittest.main()
