"""
Sample configuration for the mediaplayer app.

Copy this file to `config.py` and fill in the real values. Do NOT
commit `config.py` with real credentials to a public repository.

Recommended workflow:
 - Copy: `cp config.sample.py config.py`
 - Edit `config.py` and fill in credentials and paths.

This sample exposes the keys and structures the application expects:
 - `mysql_config` : dict used by many modules to connect to MySQL.
 - `table_list` : list of [folder_path, table_name] pairs used by sync scripts.
 - `audio_table_list` : list used by audio cataloging scripts.
 - `Media` : placeholder expected by some utility scripts.
"""

import os

# MySQL connection dictionary used throughout the app.
# Populate with your real database credentials in `config.py` (NOT in this sample).
mysql_config = {
    'host': 'localhost',        # e.g. '127.0.0.1' or 'db.example.com'
    'user': 'your_db_user',     # database user
    'password': 'your_db_pass', # database password
    'database': 'mediaplayer',  # database name
    'port': 3306,
    'charset': 'utf8mb4',
}

# Legacy / fallback variables — MySql.py will accept either style.
SERVER = mysql_config.get('host')
USER = mysql_config.get('user')
PASSWORD = mysql_config.get('password')
DATABASE = mysql_config.get('database')


# table_list is a list of [folder_path, table_name] pairs. The sync and
# catalog scripts iterate this list to scan media folders and update DB tables.
# Use absolute paths and ensure the process running the script can read them.
table_list = [
    # Example entries:
    # ['/media/videos/movies', 'movies'],
    # ['/media/videos/tv_shows', 'tv_shows'],
]


# audio_table_list is similar but used by audio import scripts.
audio_table_list = [
    # ['/media/music/Albums', 'audio_albums_table'],
]


# Placeholder or helper structure referenced by some scripts that import
# `Media` from config. If your workflow requires a richer object, replace
# this with the appropriate structure.
Media = {}


# Optional settings
DEBUG = False


# Notes for secure deployment:
# - Keep `config.py` out of version control (add it to .gitignore).
# - Prefer environment variables for secrets in production, or a secret
#   manager. For local dev it's convenient to use a copy of this file.
# - Some features (e.g., `pymediainfo`) require system packages
#   (libmediainfo/mediainfo, ffmpeg) installed on the host.
