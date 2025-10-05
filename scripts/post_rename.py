#!/usr/bin/env python3
# scripts/post_rename.py

import os
import time
import shutil
import subprocess

def git_short_hash():
    try:
        out = subprocess.check_output(["git","rev-parse","--short","HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None

out_files = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").strip()
if not out_files:
    exit(0)

files = [f for f in out_files.splitlines() if f.strip()]
ts = time.strftime("%Y-%m-%d")
suffix = ts
# new line
# new_name = "" # Initialize new_name to use it outside the loop

for f in files:
    if not os.path.exists(f):
        continue

    base, ext = os.path.splitext(os.path.basename(f))

    # ✅ Only rename report.html
    if base != "report" or ext != ".html":
        continue

    dirn = os.path.dirname(f) or "."
    new_base = f"{base}_{suffix}"
    new_name = os.path.join(dirn, new_base + ext)

    # move the html file
    shutil.move(f, new_name)
    print("Renamed:", f, "->", new_name)

    # also rename the associated resources dir (e.g. report_files -> report_<ts>_files)
    res_dir = os.path.join(dirn, base + "_files")
    if os.path.isdir(res_dir):
        new_res = os.path.join(dirn, new_base + "_files")
        shutil.move(res_dir, new_res)
        print("Renamed resources:", res_dir, "->", new_res)

    # optionally create a stable "latest" copy (overwrite)
    stable = os.path.join(dirn, f"{base}-latest{ext}")
    shutil.copyfile(new_name, stable)
    print("Copied latest:", new_name, "->", stable)


archive_dir = os.path.join(dirn, "archive")
os.makedirs(archive_dir, exist_ok=True)

# Move the dated report into archive (skip the latest copy)
shutil.move(new_name, os.path.join(archive_dir, os.path.basename(new_name)))
print("Moved to archive:", new_name)

# below is added.
# --- Archiving Section ---

# Only proceed if a report was actually generated
# if new_name and os.path.exists(new_name):
#     # 1. Archive the rendered HTML report
#     archive_dir = os.path.join(dirn, "archive")
#     os.makedirs(archive_dir, exist_ok=True)
#     # Move the dated report into archive (skip the latest copy)
#     shutil.move(new_name, os.path.join(archive_dir, os.path.basename(new_name)))
#     print("Moved to archive:", new_name)

#     # 2. (NEW) Archive the source QMD file for reproducibility
#     source_qmd = "report.qmd"
#     archive_qmd_dir = "archive_qmd" # A new top-level folder for source files
#     os.makedirs(archive_qmd_dir, exist_ok=True)
    
#     # Create the new filename for the archived source file
#     archive_qmd_name = f"report_{suffix}.qmd"
#     dest_qmd_path = os.path.join(archive_qmd_dir, archive_qmd_name)
    
#     # Copy the source file
#     shutil.copyfile(source_qmd, dest_qmd_path)
#     print("Archived source:", source_qmd, "->", dest_qmd_path)