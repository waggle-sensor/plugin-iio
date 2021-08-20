#!/usr/bin/env python3
#
# transformer pipeline program which converts data from sdr
# to scientifically meaningful units
#
import json
import sys

tfm_names = {
    "iio.in_humidityrelative_input": "env.relative_humidity",
    "iio.in_pressure_input": "env.pressure",
    "iio.in_temp_input": "env.temperature",
}

tfm_funcs = {
    ("bme280", "iio.in_humidityrelative_input"): lambda x: x/1000,
    ("bme280", "iio.in_pressure_input"): lambda x: x*1000,
    ("bme280", "iio.in_temp_input"): lambda x: x/1000,

    ("bme680", "iio.in_humidityrelative_input"): lambda x: x,
    ("bme680", "iio.in_pressure_input"): lambda x: x*100,
    ("bme680", "iio.in_temp_input"): lambda x: x/1000,
}

for r in map(json.loads, sys.stdin):
    # output original sample
    json.dump(r, sys.stdout)

    # transform sample, if transform exists
    try:
        name = tfm_names[r["name"]]
        tfm = tfm_funcs[(r["meta"]["sensor"], r["name"])]
    except KeyError:
        continue
    r["name"] = name
    r["value"] = tfm(r["value"])

    # output transformed sample
    json.dump(r, sys.stdout)
