#!/home/al/miniconda3/envs/py/bin/python3
# -*- coding: utf-8 -*-
#
#   Copyright 2025 AL Haines <alfredhaines@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   filename:  read_audio_to_mysql.py

import os
import pymysql
import re
from config import mysql_config, audio_table_list,Media # Import MySQL credentials from config.py
from mutagen import mp3, flac, ogg  # Library for reading audio metadata

# Regex pattern for audio files
audio_pattern = re.compile(r'.*(\.mp3|\.wav|\.flac|\.ogg|\.ape)$', re.IGNORECASE)

# Function to connect to MySQL database
def connect_to_db():
    """Connects to the MySQL database using credentials from config.py."""
    try:
        connection = pymysql.connect(**mysql_config)
        return connection
    except pymysql.Error as e:
        print(f"Error: Unable to connect to the database. {e}")
        return None

# Function to get existing file paths from the database
def get_existing_file_paths(connection, table_name):
    """Retrieves existing file paths from the specified table in the database."""
    cursor = connection.cursor()
    cursor.execute(f"SELECT file_path FROM {table_name}")
    results = cursor.fetchall()
    return {row[0] for row in results}  # Return as a set for faster lookup

# Function to insert new files into the database
def insert_new_files(connection, folder_path, table_name, pattern, existing_paths):
    """
    Scans the specified folder for audio files, extracts metadata,
    and inserts new file information into the database.

    Args:
        connection: MySQL database connection object.
        folder_path: Path to the directory containing audio files.
        table_name: Name of the table in the database to insert data into.
        pattern: Regex pattern to match audio files.
        existing_paths: Set of existing file paths in the database.
    """
    cursor = connection.cursor()
    file_count = 0
    new_files_count = 0

    print(f"Scanning files in: {folder_path} for table: {table_name}")

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if pattern is None or pattern.match(file):
                file_path = os.path.join(root, file)
                if file_path not in existing_paths:
                    title = os.path.splitext(file)[0]  # Extract title from filename (basic)
                    artist = "Unknown Artist"  # Default value
                    album = "Unknown Album"    # Default value
                    category = table_name.replace("audio_", "") # Extract category from table name

                    # Extract metadata using mutagen (if needed)
                    try:
                        audio_file = mutagen.File(file_path)
                        if audio_file:
                            title = audio_file.get("TIT2", [title])[0]
                            artist = audio_file.get("TPE1", [artist])[0]
                            album = audio_file.get("TALB", [album])[0]
                    except Exception as e:
                        print(f"Error reading metadata from {file_path}: {e}")

                    try:
                        cursor.execute(
                            f"INSERT INTO {table_name} (title, file_path, category, artist, album) VALUES (%s, %s, %s, %s, %s)",
                            (title, file_path, category, artist, album),
                        )
                        new_files_count += 1
                    except pymysql.Error as e:
                        print(f"Error inserting {file_path}: {e}")
                file_count += 1  # Increment total files processed
            else:
                pass  # Unmatched files are ignored now
            #print(f"unmatched file {os.path.join(root,file)}")

    connection.commit()
    print(
        f"{table_name.capitalize()} cataloging completed. "
        f"Total files processed: {file_count}, New files inserted: {new_files_count}"
    )

if __name__ == "__main__":
    # Connect to MySQL database
    db_connection = connect_to_db()
    if db_connection is None:
        exit()  # Exit if database connection fails

    # Iterate through the table list
    for folder_path, table_name in audio_table_list:
        if os.path.exists(folder_path):
            # Get existing file paths from the database
            existing_paths = get_existing_file_paths(db_connection, table_name)
            # Insert only the new files
            insert_new_files(
                db_connection, folder_path, table_name, audio_pattern, existing_paths
            )
        else:
            print(f"{folder_path} folder not found.")

    # Close the database connection
    db_connection.close()
