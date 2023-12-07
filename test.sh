#!/usr/bin/env bash

curl -L -F "name=inu.jpg" -F "file=@inu.jpg" localhost:6001/detection --output detection.jpg
curl -L -F "name=inu.jpg" -F "file=@inu.jpg" localhost:6001/segmentation --output segmentation.jpg
