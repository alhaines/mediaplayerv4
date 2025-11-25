# mediaplayerv4

This app is my pride & joy!  I use it to play media over a Cloudflare tunnel to my local files.  I've create subdomains & can play any media file on my tablet while mobile!

This folder contains the minimal files needed to run the mediaplayer web app and the `sync_media.py` & read_audio_to_mysql.py scripts to ceate & update the database.

Files included:

- `app.py`, `OV.py`, `MySql.py` — main Flask app and DB helper
- `wsgi.py` — WSGI entry for deployment
- `requirements.txt` — Python dependencies
- `sync_media.py` — CLI sync script to update DB from media folders
- `read_audio_to_mysql.py` CLI sync script to update juust the Audio DB from media folders
- `templates/` and `static/` — HTML templates and static assets
- # html files go in templates & css files go in static  
- `config.sample.py` — sample config (copy to `config.py` and edit)
- `.gitignore` — recommended ignores

Quick start (local development):

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy sample config and edit credentials/paths:

```bash
cp config.sample.py config.py
# a table_list describes your media locations
# edit config.py to set DB credentials and table_list
# edit MySql.py to set DB credentials
```

4. Run the app locally:

```bash
cd ~/projects/mediaplayer
# reccomended environment is miniconda
~/miniconda3/envs/py/bin/gunicorn --workers 3 --bind 0.0.0.0:5002 app:app
# or config and install mediaplayer.service
sudo ~/projects/mediaplayer/mediaplayer.service /etc/systemd/system/
```
