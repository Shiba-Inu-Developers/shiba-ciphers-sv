#!/usr/bin/env bash

curl -L -F "name=inu.jpg" -F "file=@inu.jpg" localhost/detection --output detection.jpg
curl -L -F "name=inu.jpg" -F "file=@inu.jpg" localhost/segmentation --output segmentation.jpg
