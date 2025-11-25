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
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   filename: sync_media.py
#
"""
Standalone CLI script to sync media folders with MySQL database.
Scans folders from table_list in config.py, inserts new files, deletes stale entries,
and displays results using the rich library.

Usage:
    python3 sync_media.py
    or
    ./sync_media.py (if executable)
"""

import pymysql
import os
import re
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from config import mysql_config, table_list

# Initialize rich console
console = Console()

# Regex pattern for video files (expanded to include more formats)
VIDEO_PATTERN = re.compile(r'.*(\.mp4|\.mkv|\.avi|\.webm|\.mov|\.flv|\.wmv|\.m4v|\.mpg|\.mpeg)$', re.IGNORECASE)


def connect_to_db():
    """
    Connects to the MySQL database using credentials from config.py.

    Returns:
        pymysql.Connection: A connection object to the database, or None if connection fails.
    """
    try:
        connection = pymysql.connect(**mysql_config)
        return connection
    except pymysql.Error as e:
        console.print(f"[bold red]Error:[/bold red] Unable to connect to database: {e}")
        return None


def scan_folder(folder_path, pattern):
    """
    Scans a folder recursively for files matching the specified pattern.

    Args:
        folder_path (str): The path to the folder to scan.
        pattern (re.Pattern): A regular expression pattern to match filenames.

    Returns:
        list: A list of absolute file paths found in the folder.
    """
    files = []
    if os.path.exists(folder_path):
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if pattern.match(filename):
                    files.append(os.path.join(root, filename))
    return files


def get_existing_file_paths(connection, table_name):
    """
    Retrieves existing file paths from the database for a given table.

    Args:
        connection (pymysql.Connection): A connection object to the database.
        table_name (str): The name of the database table.

    Returns:
        set: A set of file paths retrieved from the database.
    """
    cursor = connection.cursor()
    cursor.execute(f"SELECT file_path FROM {table_name}")
    results = cursor.fetchall()
    return {row[0] for row in results}


def insert_new_files(connection, table_name, new_files):
    """
    Inserts new file paths into the database for a given table.

    Args:
        connection (pymysql.Connection): A connection object to the database.
        table_name (str): The name of the database table.
        new_files (list): A list of file paths to insert.

    Returns:
        int: The number of files successfully inserted.
    """
    if not new_files:
        return 0
        
    cursor = connection.cursor()
    inserted_count = 0
    failed_count = 0
    
    for file_path in new_files:
        title = os.path.splitext(os.path.basename(file_path))[0]
        try:
            # Insert without specifying id - let AUTO_INCREMENT handle it
            cursor.execute(
                f"INSERT INTO {table_name} (title, file_path) VALUES (%s, %s)",
                (title, file_path),
            )
            inserted_count += 1
        except pymysql.Error as e:
            failed_count += 1
            if failed_count <= 3:  # Only show first 3 errors to avoid spam
                console.print(f"[yellow]Warning:[/yellow] Error inserting into {table_name}: {e}")
            elif failed_count == 4:
                console.print(f"[yellow]Warning:[/yellow] Suppressing further insertion errors for {table_name}...")
    
    connection.commit()
    
    if failed_count > 0:
        console.print(f"[bold red]Error:[/bold red] {failed_count} files failed to insert in {table_name}.")
    
    return inserted_count


def delete_stale_files(connection, table_name, current_files_set):
    """
    Deletes stale file paths from the database (files that no longer exist on disk).

    Args:
        connection (pymysql.Connection): A connection object to the database.
        table_name (str): The name of the database table.
        current_files_set (set): A set of file paths that currently exist on disk.

    Returns:
        int: The number of files successfully deleted.
    """
    cursor = connection.cursor()
    cursor.execute(f"SELECT file_path FROM {table_name}")
    db_files = {row[0] for row in cursor.fetchall()}
    stale_files = db_files - current_files_set
    deleted_count = 0
    for file_path in stale_files:
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE file_path = %s", (file_path,))
            deleted_count += 1
        except pymysql.Error as e:
            console.print(f"[yellow]Warning:[/yellow] Error deleting {file_path}: {e}")
    connection.commit()
    return deleted_count


def sync_media_folders():
    """
    Main function to sync media folders with the database.
    Scans all folders in table_list, compares with database, and updates accordingly.
    """
    # Display header
    console.print(Panel.fit(
        "[bold cyan]Media Manager - Database Sync[/bold cyan]\n"
        f"[dim]Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="cyan"
    ))
    
    # Connect to database
    db_connection = connect_to_db()
    if not db_connection:
        console.print("[bold red]Sync aborted due to database connection failure.[/bold red]")
        return
    
    # Create results table
    results_table = Table(
        title="Sync Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    
    results_table.add_column("Table", style="cyan", no_wrap=True)
    results_table.add_column("Folder", style="white")
    results_table.add_column("Scanned", justify="right", style="blue")
    results_table.add_column("Inserted", justify="right", style="green")
    results_table.add_column("Deleted", justify="right", style="red")
    results_table.add_column("Status", justify="center")
    
    # Track totals
    total_scanned = 0
    total_inserted = 0
    total_deleted = 0
    total_errors = 0
    
    # Process each folder/table pair
    with console.status("[bold green]Syncing media folders...") as status:
        for folder_path, table_name in table_list:
            status.update(f"[bold green]Processing: {table_name}...")
            
            if not os.path.exists(folder_path):
                results_table.add_row(
                    table_name,
                    folder_path,
                    "-",
                    "-",
                    "-",
                    "[bold red]✗ Folder Not Found[/bold red]"
                )
                total_errors += 1
                continue
            
            try:
                # Scan folder for video files
                scanned_files = scan_folder(folder_path, VIDEO_PATTERN)
                scanned_count = len(scanned_files)
                
                # Get existing paths from database
                existing_paths = get_existing_file_paths(db_connection, table_name)
                
                # Find new files to insert
                new_files = [f for f in scanned_files if f not in existing_paths]
                
                # Insert new files
                inserted_count = insert_new_files(db_connection, table_name, new_files)
                
                # Delete stale entries
                deleted_count = delete_stale_files(db_connection, table_name, set(scanned_files))
                
                # Add row to results table
                status_text = "[bold green]✓ Success[/bold green]"
                if inserted_count > 0 or deleted_count > 0:
                    status_text = f"[bold yellow]✓ Updated[/bold yellow]"
                
                results_table.add_row(
                    table_name,
                    folder_path,
                    str(scanned_count),
                    str(inserted_count),
                    str(deleted_count),
                    status_text
                )
                
                # Update totals
                total_scanned += scanned_count
                total_inserted += inserted_count
                total_deleted += deleted_count
                
            except Exception as e:
                results_table.add_row(
                    table_name,
                    folder_path,
                    "-",
                    "-",
                    "-",
                    f"[bold red]✗ Error: {str(e)[:30]}[/bold red]"
                )
                total_errors += 1
    
    # Close database connection
    db_connection.close()
    
    # Display results table
    console.print()
    console.print(results_table)
    
    # Display summary
    console.print()
    summary_table = Table(
        title="Summary",
        box=box.SIMPLE,
        show_header=False,
        border_style="dim"
    )
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")
    
    summary_table.add_row("Total Tables Processed", str(len(table_list)))
    summary_table.add_row("Total Files Scanned", f"[blue]{total_scanned}[/blue]")
    summary_table.add_row("Total Files Inserted", f"[green]{total_inserted}[/green]")
    summary_table.add_row("Total Files Deleted", f"[red]{total_deleted}[/red]")
    if total_errors > 0:
        summary_table.add_row("Errors", f"[bold red]{total_errors}[/bold red]")
    
    console.print(summary_table)
    
    # Final status message
    console.print()
    if total_errors == 0:
        console.print(Panel(
            "[bold green]✓ Sync completed successfully![/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]⚠ Sync completed with {total_errors} error(s).[/bold yellow]",
            border_style="yellow"
        ))


if __name__ == "__main__":
    try:
        sync_media_folders()
    except KeyboardInterrupt:
        console.print("\n[bold red]Sync interrupted by user.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
