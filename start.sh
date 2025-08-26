#!/usr/bin/env bash
cd estatecore_backend
gunicorn wsgi:app