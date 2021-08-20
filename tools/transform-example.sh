#!/bin/sh

curl -s -H 'Content-Type: application/json' https://sdr.sagecontinuum.org/api/v1/query -d '
{
  "start": "-15m",
  "tail": 1,
    "filter": {
        "name": "iio.*"
    }
}
' | ./transform.py | jq .

