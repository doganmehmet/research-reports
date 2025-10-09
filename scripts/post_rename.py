#!/usr/bin/env python3
# scripts/post_rename.py

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


def update_archive_qmd(qmd_file_path):
    """
    Updates the archive/index.qmd file with a static Markdown list
    of all archived reports (for static GitHub Pages display).
    """
    print("\n--- Updating archive index.qmd ---")

    # Read from the persistent archive folder
    persistent_archive = "archived_reports"
    
    try:
        files = [f for f in os.listdir(persistent_archive) if f.endswith(".html")]
    except FileNotFoundError:
        print(f"Archive directory not found: {persistent_archive}")
        files = []

    if os.path.exists(persistent_archive):
        existing = [f for f in os.listdir(persistent_archive) if f.endswith('.html')]
        print(f"📂 Existing archived reports: {existing}")

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

for f in files:
    if not os.path.exists(f):
        continue

    base, ext = os.path.splitext(os.path.basename(f))
    if base != "report" or ext != ".html":
        continue

    dirn = os.path.dirname(f) or "."
    new_base = f"{base}_{suffix}"
    new_name = os.path.join(dirn, new_base + ext)

    # Check for resources folder BEFORE renaming
    res_dir = os.path.join(dirn, base + "_files")
    has_resources = os.path.isdir(res_dir)
    
    print(f"Processing report: {f}")
    print(f"Resources directory exists: {has_resources}")
    if has_resources:
        print(f"Resources location: {res_dir}")

    # Rename the main report
    shutil.move(f, new_name)
    print("Renamed:", f, "->", new_name)

    # Rename resources folder if exists
    new_res_dir = None
    if has_resources:
        new_res = os.path.join(dirn, new_base + "_files")
        shutil.move(res_dir, new_res)
        new_res_dir = new_res
        print("Renamed resources:", res_dir, "->", new_res)

    # Copy a stable 'latest' copy
    stable = os.path.join(dirn, f"{base}-latest{ext}")
    shutil.copyfile(new_name, stable)
    print("Copied latest:", new_name, "->", stable)

    # Store dated report in PERSISTENT archive folder (not in docs/)
    persistent_archive = "archived_reports"
    os.makedirs(persistent_archive, exist_ok=True)
    archive_dest = os.path.join(persistent_archive, os.path.basename(new_name))
    shutil.copy(new_name, archive_dest)
    print("Copied to persistent archive:", new_name, "->", archive_dest)

    # Copy charts for this archived report
    charts_dir = "docs/charts"
    if os.path.isdir(charts_dir):
        report_charts_dir = os.path.join(persistent_archive, "charts")
        if os.path.exists(report_charts_dir):
            shutil.rmtree(report_charts_dir)
        shutil.copytree(charts_dir, report_charts_dir)
        print("✅ Copied charts for archive:", charts_dir, "->", report_charts_dir)

    # Copy resources folder to persistent archive if it exists
    if new_res_dir and os.path.isdir(new_res_dir):
        archive_res_dest = os.path.join(persistent_archive, os.path.basename(new_res_dir))
        print(f"Attempting to copy resources to: {archive_res_dest}")
        
        if os.path.exists(archive_res_dest):
            print(f"Removing existing archive resources: {archive_res_dest}")
            shutil.rmtree(archive_res_dest)
        
        shutil.copytree(new_res_dir, archive_res_dest)
        print("✅ Copied resources to archive:", new_res_dir, "->", archive_res_dest)
    else:
        print("⚠️  No resources folder found to copy to archive")

    # Archive the source QMD
    source_qmd = "report.qmd"
    archive_qmd_dir = "archive_qmd"
    os.makedirs(archive_qmd_dir, exist_ok=True)
    archive_qmd_name = f"report_{suffix}.qmd"
    dest_qmd_path = os.path.join(archive_qmd_dir, archive_qmd_name)
    shutil.copyfile(source_qmd, dest_qmd_path)
    print("Archived source:", source_qmd, "->", dest_qmd_path)

    # Update archive/index.qmd with all reports from persistent archive
    qmd_file_path = "archive/index.qmd"
    update_archive_qmd(qmd_file_path)

    # CRITICAL: Copy all archived reports from persistent storage to docs/archive for deployment
    print("\n--- Copying archived reports to docs/archive for deployment ---")
    docs_archive = "docs/archive"
    os.makedirs(docs_archive, exist_ok=True)

    if os.path.exists(persistent_archive):
        for item in os.listdir(persistent_archive):
            src = os.path.join(persistent_archive, item)
            dst = os.path.join(docs_archive, item)
            
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"📄 Copied to docs/archive: {item}")
            elif os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"📁 Copied folder to docs/archive: {item}")
    
    print("✅ All archived content ready for deployment")




# import os
# import time
# import shutil
# import subprocess


# def git_short_hash():
#     """Get short git commit hash if available (optional suffix)."""
#     try:
#         out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
#         return out.decode().strip()
#     except Exception:
#         return None


# def update_archive_qmd(archive_dir, qmd_file_path):
#     """
#     Updates the archive/index.qmd file with a static Markdown list
#     of all archived reports (for static GitHub Pages display).
#     """
#     print("\n--- Updating archive index.qmd ---")

#     try:
#         files = [f for f in os.listdir(archive_dir) if f.endswith(".html") and f != "index.html"]
#     except FileNotFoundError:
#         print(f"Archive directory not found: {archive_dir}")
#         return

#     files.sort(reverse=True)

#     if not files:
#         list_md = "No archived reports yet."
#     else:
#         list_items = [f"- [{f.replace('.html', '')}]({f})" for f in files]
#         list_md = "\n".join(list_items)

#     # Build full .qmd content
#     content = f"""---
# title: Archive
# ---

# # Past Reports

# {list_md}
# """

#     with open(qmd_file_path, "w", encoding="utf-8") as f:
#         f.write(content)

#     print(f"✅ Successfully updated {qmd_file_path}")
#     print(f"🗂  Reports listed: {len(files)}")


# # --- MAIN SCRIPT LOGIC ---

# out_files = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").strip()
# if not out_files:
#     exit(0)

# files = [f for f in out_files.splitlines() if f.strip()]
# ts = time.strftime("%Y-%m-%d")
# suffix = ts
# git_hash = git_short_hash()
# if git_hash:
#     suffix = ts  # Just use timestamp

# for f in files:
#     if not os.path.exists(f):
#         continue

#     base, ext = os.path.splitext(os.path.basename(f))
#     if base != "report" or ext != ".html":
#         continue

#     dirn = os.path.dirname(f) or "."
#     new_base = f"{base}_{suffix}"
#     new_name = os.path.join(dirn, new_base + ext)

#     # Rename the main report
#     shutil.move(f, new_name)
#     print("Renamed:", f, "->", new_name)

#     # Rename resources folder if exists
#     res_dir = os.path.join(dirn, base + "_files")
#     if os.path.isdir(res_dir):
#         new_res = os.path.join(dirn, new_base + "_files")
#         shutil.move(res_dir, new_res)
#         print("Renamed resources:", res_dir, "->", new_res)

#     # Copy a stable 'latest' copy
#     stable = os.path.join(dirn, f"{base}-latest{ext}")
#     shutil.copyfile(new_name, stable)
#     print("Copied latest:", new_name, "->", stable)

#     # Move dated report into archive
#     archive_dir = os.path.join(dirn, "archive")
#     os.makedirs(archive_dir, exist_ok=True)
#     shutil.move(new_name, os.path.join(archive_dir, os.path.basename(new_name)))
#     print("Moved to archive:", new_name)

#     # Archive the source QMD
#     source_qmd = "report.qmd"
#     archive_qmd_dir = "archive_qmd"
#     os.makedirs(archive_qmd_dir, exist_ok=True)
#     archive_qmd_name = f"report_{suffix}.qmd"
#     dest_qmd_path = os.path.join(archive_qmd_dir, archive_qmd_name)
#     shutil.copyfile(source_qmd, dest_qmd_path)
#     print("Archived source:", source_qmd, "->", dest_qmd_path)

#     # Update archive/index.qmd
#     # qmd_file_path = os.path.join(archive_dir, "index.qmd")
#     # update_archive_qmd(archive_dir, qmd_file_path)

#     # Update archive/index.qmd
#     qmd_file_path = "archive/index.qmd" # <-- Corrected path
#     update_archive_qmd(archive_dir, qmd_file_path)
