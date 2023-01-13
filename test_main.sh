#!/bin/sh

python3 main.py \
    --root test/sys/bus/iio/devices/ \
    --cache-seconds 3 \
    --node-publish-interval 5 \
    --beehive-publish-interval 10 \
    $*
