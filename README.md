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
