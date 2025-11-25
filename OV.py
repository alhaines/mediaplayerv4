#!/home/al/miniconda3/envs/py/bin/python3
# -*- coding: utf-8 -*-
#
#  filename:   /home/al/projects/mediaplayerv1/OV.py
#
#  Copyright 2025 AL Haines
#
#  Definitive Version: Correctly implements track number sorting
#                      AND the resume playback functionality.

from flask import render_template, jsonify, request, Response, stream_with_context
import os
import re
from MySql import MySQL
import config

def _get_db_connection():
    return MySQL(**config.mysql_config)

def _get_item_details(table_name, item_id):
    db = _get_db_connection()
    query = f"SELECT * FROM `{table_name}` WHERE id = %s"
    results = db.get_data(query, (item_id,))
    return results[0] if results else None

def get_resume_items():
    db = _get_db_connection()
    all_tables_raw = db.get_data("SHOW TABLES")
    if not all_tables_raw:
        return []

    # Filter tables to only include those in config.table_list
    config_tables = [row[1] for row in config.table_list]
    all_tables = [list(t.values())[0] for t in all_tables_raw if list(t.values())[0] in config_tables]
    union_queries = []

    for table in all_tables:
        columns = db.get_field_names(table)
        if 'resume_position' in columns and 'last_played' in columns:

            # CRITICAL FIX: Check if 'album' exists.
            # If not, use CAST(NULL AS CHAR) with COLLATE to create a valid, collated placeholder.
            if 'album' in columns:
                # If column exists, select it and apply collation
                album_select = "album COLLATE utf8mb4_unicode_ci"
            else:
                # If column is missing, cast NULL as a collated character field
                # This fixes the SQL syntax error (Error 1064)
                album_select = "CAST(NULL AS CHAR) COLLATE utf8mb4_unicode_ci"

            # Apply consistent collation to other string columns (title, file_path)
            query_part = f"""
            (SELECT
                id,
                title COLLATE utf8mb4_unicode_ci as title,
                file_path COLLATE utf8mb4_unicode_ci as file_path,
                {album_select} as album,
                '{table}' as category,
                last_played,
                resume_position
            FROM `{table}`
            WHERE resume_position > 0.1)
            """
            union_queries.append(query_part.strip())

    if not union_queries:
        return []

    full_query = " UNION ALL ".join(union_queries) + " ORDER BY last_played DESC LIMIT 20"
    return db.get_data(full_query)

def update_resume_position(table_name, item_id, position, duration):
    db = _get_db_connection()
    position_to_save = float(position)
    if (float(duration) - position_to_save) < 15:
        position_to_save = 0
    query = f"UPDATE `{table_name}` SET resume_position = %s, last_played = NOW() WHERE id = %s"
    db.put_data(query, (position_to_save, item_id))
    return jsonify(status='success')

def clear_resume_position(table_name, item_id):
    db = _get_db_connection()
    query = f"UPDATE `{table_name}` SET resume_position = 0 WHERE id = %s"
    db.put_data(query, (item_id,))
    return jsonify(status='success')

def render_index_page():
    db = _get_db_connection()
    all_tables_raw = db.get_data("SHOW TABLES")

    # --- START OF CATEGORY FIX ---
    # Ensure config.table_list is passed to the template for the category selection logic
    if not all_tables_raw:
        return render_template('index.html', categories=[], resume_items=[], table_list=config.table_list)

    all_tables = [list(t.values())[0] for t in all_tables_raw]
    categories = [t for t in all_tables if t in [row[1] for row in config.table_list]]
    categories.sort()

    resume_items = get_resume_items()

    # Pass the table_list to the template
    return render_template('index.html', categories=categories, resume_items=resume_items, table_list=config.table_list)
    # --- END OF CATEGORY FIX ---

def get_folders_for_table(table_name):
    db = _get_db_connection()
    query = f"SELECT DISTINCT SUBSTRING_INDEX(SUBSTRING_INDEX(file_path, '/', 6), '/', -1) AS folder FROM `{table_name}`"
    results = db.get_data(query)
    folders = [row['folder'] for row in results if row['folder']]
    folders.sort()
    return jsonify(folders)

def get_videos_for_folder(table_name, folder):
    db = _get_db_connection()
    query = f"SELECT id, title, file_path, resume_position FROM `{table_name}` WHERE file_path LIKE %s ORDER BY title ASC"
    videos = db.get_data(query, (f'%/{folder}/%',))
    return jsonify(videos)

def get_albums_for_table(table_name):
    db = _get_db_connection()
    #query = f"SELECT DISTINCT album FROM `{table_name}` WHERE album IS NOT NULL ORDER BY album ASC"
    query = f"SELECT DISTINCT album FROM `{table_name}` ORDER BY album ASC"
    results = db.get_data(query)
    albums = [row['album'] for row in results] if results else []
    return jsonify(albums)

def get_tracks_for_album(table_name, album):
    db = _get_db_connection()
    columns = db.get_field_names(table_name)
    # FIX: Only order by track_number if the column exists in the table.
    order_by_clause = "track_number, title ASC" if 'track_number' in columns else "title ASC"
    query = f"SELECT id, title, resume_position FROM `{table_name}` WHERE album = %s ORDER BY {order_by_clause}"
    tracks = db.get_data(query, (album,))
    return jsonify(tracks)

def render_player_page(table_name, item_id):
    current_item = _get_item_details(table_name, item_id)
    if not current_item:
        return "Media item not found", 404

    db = _get_db_connection()
    playlist, current_track_index = [], -1
    columns = db.get_field_names(table_name) # Get column names for conditional ordering

    # Logic to build playlist based on media type
    if 'album' in current_item and current_item['album'] is not None:
        # FIX: Only order by track_number if the column exists in the table.
        order_by_clause = "track_number, title ASC" if 'track_number' in columns else "title ASC"
        query = f"SELECT id, title FROM `{table_name}` WHERE album = %s ORDER BY {order_by_clause}"
        playlist = db.get_data(query, (current_item['album'],))
    elif 'file_path' in current_item:
        folder = os.path.basename(os.path.dirname(current_item['file_path']))
        query = f"SELECT id, title, file_path FROM `{table_name}` WHERE file_path LIKE %s ORDER BY title ASC"
        playlist = db.get_data(query, (f'%/{folder}/%',))

    if playlist:
        for i, track in enumerate(playlist):
            if track['id'] == item_id:
                current_track_index = i
                break

    file_path = current_item.get('file_path', '')
    is_audio = file_path.endswith(('.mp3', '.m4a', '.wav', '.flac'))

    return render_template('player.html',
                           item=current_item,
                           category=table_name,
                           playlist=playlist,
                           current_track_index=current_track_index,
                           is_audio=is_audio)

def stream_with_range_support(table_name, item_id):
    item = _get_item_details(table_name, item_id)
    if not (item and item.get('file_path')):
        return "File path not found", 404
    path = item['file_path']
    if not os.path.exists(path):
        return "File on disk not found", 404
    file_size = os.path.getsize(path)
    range_header = request.headers.get('Range', None)

    file_extension = os.path.splitext(path)[1].lower()
    if file_extension in ['.mp3', '.m4a', '.wav', '.flac']:
        mime_type = 'audio/mpeg'
    elif file_extension in ['.mp4', '.mkv', '.avi', '.mov']:
        mime_type = 'video/mp4'
    else:
        mime_type = 'application/octet-stream'

    def generate_chunks(file, start, length):
        with file:
            file.seek(start)
            remaining = length
            while remaining > 0:
                chunk_size = min(remaining, 1024 * 1024)
                data = file.read(chunk_size)
                if not data: break
                yield data
                remaining -= len(data)

    if range_header:
        byte1, byte2 = 0, None
        m = re.search(r'(\d+)-(\d*)', range_header)
        g = m.groups()
        if g[0]: byte1 = int(g[0])
        if g[1]: byte2 = int(g[1])
        if byte2 is None: byte2 = file_size - 1
        length = byte2 - byte1 + 1
        resp = Response(
            stream_with_context(generate_chunks(open(path, 'rb'), byte1, length)),
            206,
            mimetype=mime_type,
            direct_passthrough=True
        )
        resp.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
        return resp
    else:
        resp = Response(
            stream_with_context(generate_chunks(open(path, 'rb'), 0, file_size)),
            200,
            mimetype=mime_type,
            direct_passthrough=True
        )
        resp.headers.add('Content-Length', file_size)
        return resp
