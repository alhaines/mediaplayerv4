# mediaplayer (minimal package)

This folder contains the minimal files needed to run the mediaplayer web app and the `sync_media.py` script.

Files included:

- `app.py`, `OV.py`, `MySql.py` — main Flask app and DB helper
- `wsgi.py` — WSGI entry for deployment
- `requirements.txt` — Python dependencies
- `sync_media.py` — CLI sync script to update DB from media folders
- `templates/` and `static/` — HTML templates and static assets
- `config.sample.py` — sample config (copy to `config.py` and edit)
- `.gitignore` — recommended ignores
- `prepare_repo.sh` — helper to create a clean repo folder ready to push

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
# edit config.py to set DB credentials and table_list
```

4. Run the app locally:

```bash
python app.py
# or with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Publishing a minimal repo

Use `prepare_repo.sh` from the project root to gather only the needed files into a clean folder and initialize git there. Example:

```bash
./prepare_repo.sh mediaplayerv4 git@github.com:you/mediaplayerv4.git
```

The script will create the folder `mediaplayerv4`, copy files, make an initial commit, and push to the provided remote if given.

Security

- Do not commit `config.py` with real credentials. Use `config.sample.py` as a template and use environment variables in production where appropriate.
- Exclude media files from the repo.
