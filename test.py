import unittest
from main import build_iio_param_list
from pathlib import Path


class TestUtils(unittest.TestCase):

    def test_build_iio_param_list(self):
        param_list = build_iio_param_list("test/sys/bus/iio/devices")

        expected = [
            ('test1', 'in_temperature_input', Path('test/sys/bus/iio/devices/iio:1/in_temperature_input')),
            ('test1', 'in_pressure_input', Path('test/sys/bus/iio/devices/iio:1/in_pressure_input')),
            ('test2', 'in_resistance_input', Path('test/sys/bus/iio/devices/iio:2/in_resistance_input')),
        ]

        self.assertEqual(sorted(param_list), sorted(expected))


if __name__ == "__main__":
    unittest.main()
