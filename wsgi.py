#!/home/al/miniconda3/envs/py/bin/python3
# -*- coding: utf-8 -*-
#
# filename:   /home/al/projects/mediaplayer/wsgi.py
#
# This is the WSGI entry point for the Gunicorn server.
# It also provides a way to run the application directly for local testing and debugging.
#

from app import app

if __name__ == "__main__":
    # This part allows running the app directly for debugging.
    # Gunicorn will import the 'app' object directly without using this block.
    app.run(host='0.0.0.0', port=5002, debug=True)
