#!/bin/bash
# Simple CGI wrapper for real-time data API
# This allows the Python script to be called from web server

cd "$(dirname "$0")/.."
python3 api/get_realtime_data.py
