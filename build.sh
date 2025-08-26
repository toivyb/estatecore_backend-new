#!/usr/bin/env bash
# exit on error
set -o errexit

# Navigate to backend directory and install dependencies
cd estatecore_backend
pip install --upgrade pip
pip install -r requirements.txt