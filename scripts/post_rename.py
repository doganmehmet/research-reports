#!/usr/bin/env python3
# scripts/post_rename.py

import os
import time
import shutil

# --- NEW FUNCTION TO UPDATE THE ARCHIVE INDEX PAGE ---
def update_archive_index(archive_dir_path, index_file_path):
    """
    Generates a list of reports from the archive directory
    and injects it into the archive's index.html page.
    """
    print("--- Updating archive index page ---")
    
    # 1. Find all HTML files in the archive, excluding the index itself.
    try:
        files = [f for f in os.listdir(archive_dir_path) if f.endswith('.html') and f != 'index.html']
        
        # --- CRITICAL DEBUGGING STEP ---
        print(f"DEBUG: Files found in archive: {files}")
        # --------------------------------

    except FileNotFoundError:
        print(f"Archive directory not found at '{archive_dir_path}', skipping index update.")
        return

    # 2. Sort the files (newest first) and create HTML list items.
    files.sort(reverse=True)
    if not files:
        print("No reports found in archive.")
        list_html = "<p>No archived reports yet.</p>"
    else:
        list_items = [f'<li><a href="{f}">{f.replace(".html", "")}</a></li>' for f in files]
        list_html = "<ul>\n" + "\n".join(list_items) + "\n</ul>"
    
    # 3. Read the template index.html, replace the placeholder, and write it back.
    try:
        with open(index_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('', list_html)
        
        with open(index_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully updated archive index with report list.")
    
    except FileNotFoundError:
        print(f"Could not find archive index file at '{index_file_path}'")
# --------------------------------------------------------

# --- MAIN SCRIPT LOGIC ---
out_files = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").strip()
if not out_files:
    exit(0)

files = [f for f in out_files.splitlines() if f.strip()]
ts = time.strftime("%Y-%m-%d")
suffix = ts
new_name = "" # Initialize new_name

for f in files:
    if not os.path.exists(f):
        continue

    base, ext = os.path.splitext(os.path.basename(f))
    if base != "report" or ext != ".html":
        continue

    dirn = os.path.dirname(f) or "."
    new_base = f"{base}_{suffix}"
    new_name = os.path.join(dirn, new_base + ext)
    
    shutil.move(f, new_name)
    print("Renamed:", f, "->", new_name)
    stable = os.path.join(dirn, f"{base}-latest{ext}")
    shutil.copyfile(new_name, stable)
    print("Copied latest:", new_name, "->", stable)
    
    archive_dir_path = os.path.join(dirn, "archive")
    os.makedirs(archive_dir_path, exist_ok=True)
    final_archive_path = os.path.join(archive_dir_path, os.path.basename(new_name))
    shutil.move(new_name, final_archive_path)
    print("Moved to archive:", new_name)
    
    source_qmd = "report.qmd"
    archive_qmd_dir = "archive_qmd"
    os.makedirs(archive_qmd_dir, exist_ok=True)
    archive_qmd_name = f"report_{suffix}.qmd"
    dest_qmd_path = os.path.join(archive_qmd_dir, archive_qmd_name)
    shutil.copyfile(source_qmd, dest_qmd_path)
    print("Archived source:", source_qmd, "->", dest_qmd_path)
    
    index_file_path = os.path.join(archive_dir_path, "index.html")
    update_archive_index(archive_dir_path, index_file_path)