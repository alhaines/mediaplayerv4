#!/home/al/miniconda3/envs/py/bin/python3
# -*- coding: utf-8 -*-
#
#  filename:   /home/al/projects/mediaplayerv1/app.py
#
#  Copyright 2025 AL Haines

from flask import Flask, render_template, request, url_for
import OV

app = Flask(__name__, static_folder='static')

@app.route('/', methods=['GET'])
def index():
    return OV.render_index_page()

@app.route('/get_folders/<table_name>', methods=['GET'])
def get_folders(table_name):
    return OV.get_folders_for_table(table_name)

@app.route('/get_videos/<table_name>/<folder>', methods=['GET'])
def get_videos(table_name, folder):
    return OV.get_videos_for_folder(table_name, folder)

@app.route('/get_albums/<table_name>', methods=['GET'])
def get_albums(table_name):
    return OV.get_albums_for_table(table_name)

@app.route('/get_tracks/<table_name>/<album>', methods=['GET'])
def get_tracks(table_name, album):
    return OV.get_tracks_for_album(table_name, album)

@app.route('/update_resume/<table_name>/<int:item_id>', methods=['POST'])
def update_resume(table_name, item_id):
    position = request.form.get('position')
    duration = request.form.get('duration')
    return OV.update_resume_position(table_name, item_id, position, duration)

@app.route('/clear_resume/<table_name>/<int:item_id>', methods=['POST'])
def clear_resume(table_name, item_id):
    return OV.clear_resume_position(table_name, item_id)

@app.route('/player/<table_name>/<int:item_id>')
def player(table_name, item_id):
    return OV.render_player_page(table_name, item_id)

@app.route('/stream/<table_name>/<int:item_id>')
def stream(table_name, item_id):
    return OV.stream_with_range_support(table_name, item_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
