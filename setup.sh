#!/bin/bash

# Install tesseract and Russian + English language packs
apt-get update
apt-get install -y tesseract-ocr
apt-get install -y tesseract-ocr-rus tesseract-ocr-eng
