#!/usr/bin/env python3
# scripts/post_rename.py

import os
import time
import shutil
import subprocess


def git_short_hash():
    """Get short git commit hash if available (optional suffix)."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None


def update_archive_qmd(archive_dir, qmd_file_path):
    """
    Updates the archive/index.qmd file with a static Markdown list
    of all archived reports (for static GitHub Pages display).
    """
    print("\n--- Updating archive index.qmd ---")

    try:
        files = [f for f in os.listdir(archive_dir) if f.endswith(".html") and f != "index.html"]
    except FileNotFoundError:
        print(f"Archive directory not found: {archive_dir}")
        return

    files.sort(reverse=True)

    if not files:
        list_md = "No archived reports yet."
    else:
        list_items = [f"- [{f.replace('.html', '')}]({f})" for f in files]
        list_md = "\n".join(list_items)

    # Build full .qmd content
    content = f"""---
title: Archive
---

# Past Reports

{list_md}
"""

    with open(qmd_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Successfully updated {qmd_file_path}")
    print(f"🗂  Reports listed: {len(files)}")


# --- MAIN SCRIPT LOGIC ---

out_files = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").strip()
if not out_files:
    exit(0)

files = [f for f in out_files.splitlines() if f.strip()]
ts = time.strftime("%Y-%m-%d")
suffix = ts
git_hash = git_short_hash()
if git_hash:
    suffix = f"{suffix}-{git_hash}"

for f in files:
    if not os.path.exists(f):
        continue

    base, ext = os.path.splitext(os.path.basename(f))
    if base != "report" or ext != ".html":
        continue

    dirn = os.path.dirname(f) or "."
    new_base = f"{base}_{suffix}"
    new_name = os.path.join(dirn, new_base + ext)

    # Rename the main report
    shutil.move(f, new_name)
    print("Renamed:", f, "->", new_name)

    # Rename resources folder if exists
    res_dir = os.path.join(dirn, base + "_files")
    if os.path.isdir(res_dir):
        new_res = os.path.join(dirn, new_base + "_files")
        shutil.move(res_dir, new_res)
        print("Renamed resources:", res_dir, "->", new_res)

    # Copy a stable 'latest' copy
    stable = os.path.join(dirn, f"{base}-latest{ext}")
    shutil.copyfile(new_name, stable)
    print("Copied latest:", new_name, "->", stable)

    # Move dated report into archive
    archive_dir = os.path.join(dirn, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    shutil.move(new_name, os.path.join(archive_dir, os.path.basename(new_name)))
    print("Moved to archive:", new_name)

    # Archive the source QMD
    source_qmd = "report.qmd"
    archive_qmd_dir = "archive_qmd"
    os.makedirs(archive_qmd_dir, exist_ok=True)
    archive_qmd_name = f"report_{suffix}.qmd"
    dest_qmd_path = os.path.join(archive_qmd_dir, archive_qmd_name)
    shutil.copyfile(source_qmd, dest_qmd_path)
    print("Archived source:", source_qmd, "->", dest_qmd_path)

    # Update archive/index.qmd
    qmd_file_path = os.path.join(archive_dir, "index.qmd")
    update_archive_qmd(archive_dir, qmd_file_path)
