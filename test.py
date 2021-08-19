import unittest
from main import build_iio_param_set
from pathlib import Path


class TestUtils(unittest.TestCase):

    def test_build_iio_param_list(self):
        param_list = build_iio_param_set("test/sys/bus/iio/devices")
        expected = {
            ("ina3221x", "in_voltage0_input", Path("test/sys/bus/iio/devices/iio:device0/in_voltage0_input")),
            ("ina3221x", "in_current1_input", Path("test/sys/bus/iio/devices/iio:device0/in_current1_input")),
            ("ina3221x", "in_voltage2_input", Path("test/sys/bus/iio/devices/iio:device0/in_voltage2_input")),
            ("ina3221x", "in_current_sum_input", Path("test/sys/bus/iio/devices/iio:device0/in_current_sum_input")),
            ("ina3221x", "in_power1_trigger_input", Path("test/sys/bus/iio/devices/iio:device0/in_power1_trigger_input")),
            ("ina3221x", "in_power2_trigger_input", Path("test/sys/bus/iio/devices/iio:device0/in_power2_trigger_input")),
            ("ina3221x", "in_current0_input", Path("test/sys/bus/iio/devices/iio:device0/in_current0_input")),
            ("ina3221x", "in_current0_trigger_input", Path("test/sys/bus/iio/devices/iio:device0/in_current0_trigger_input")),
            ("ina3221x", "in_current2_input", Path("test/sys/bus/iio/devices/iio:device0/in_current2_input")),
            ("ina3221x", "in_voltage1_input", Path("test/sys/bus/iio/devices/iio:device0/in_voltage1_input")),
            ("ina3221x", "in_current2_trigger_input", Path("test/sys/bus/iio/devices/iio:device0/in_current2_trigger_input")),
            ("ina3221x", "in_power0_input", Path("test/sys/bus/iio/devices/iio:device0/in_power0_input")),
            ("ina3221x", "in_power2_input", Path("test/sys/bus/iio/devices/iio:device0/in_power2_input")),
            ("ina3221x", "in_current1_trigger_input", Path("test/sys/bus/iio/devices/iio:device0/in_current1_trigger_input")),
            ("ina3221x", "in_power0_trigger_input", Path("test/sys/bus/iio/devices/iio:device0/in_power0_trigger_input")),
            ("ina3221x", "in_power1_input", Path("test/sys/bus/iio/devices/iio:device0/in_power1_input")),

            ("bme280", "in_humidityrelative_input", Path("test/sys/bus/iio/devices/iio:device1/in_humidityrelative_input")),
            ("bme280", "in_pressure_input", Path("test/sys/bus/iio/devices/iio:device1/in_pressure_input")),
            ("bme280", "in_temp_input", Path("test/sys/bus/iio/devices/iio:device1/in_temp_input")),

            ("bme680", "in_humidityrelative_input", Path("test/sys/bus/iio/devices/iio:device2/in_humidityrelative_input")),
            ("bme680", "in_resistance_input", Path("test/sys/bus/iio/devices/iio:device2/in_resistance_input")),
            ("bme680", "in_pressure_input", Path("test/sys/bus/iio/devices/iio:device2/in_pressure_input")),
            ("bme680", "in_temp_input", Path("test/sys/bus/iio/devices/iio:device2/in_temp_input")),
        }
        self.assertEqual(param_list, expected)
    
    def test_build_iio_param_list_filter(self):
        param_list = build_iio_param_set("test/sys/bus/iio/devices", "bme280")
        expected = {
            ("bme280", "in_humidityrelative_input", Path("test/sys/bus/iio/devices/iio:device1/in_humidityrelative_input")),
            ("bme280", "in_pressure_input", Path("test/sys/bus/iio/devices/iio:device1/in_pressure_input")),
            ("bme280", "in_temp_input", Path("test/sys/bus/iio/devices/iio:device1/in_temp_input")),
        }
        self.assertEqual(param_list, expected)


if __name__ == "__main__":
    unittest.main()
