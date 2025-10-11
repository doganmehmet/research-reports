#!/usr/bin/env python3
"""
Post-Render Script for Quarto Market Research Reports
======================================================

This script runs automatically after Quarto renders report.qmd.
It handles report archiving, versioning, and archive index updates.

Purpose:
--------
1. Rename rendered report.html with timestamp (report_YYYY-MM-DD.html)
2. Create stable "report-latest.html" copy for consistent URLs
3. Archive dated reports to persistent storage (archived_reports/)
4. Copy supporting assets (charts, site_libs, resources)
5. Update archive/index.qmd with list of all archived reports
6. Deploy archived content to docs/archive/ for GitHub Pages

Trigger:
--------
Quarto calls this script via the `post-render` hook in _quarto.yml:
    project:
      post-render: scripts/post_rename.py

Environment Variables:
----------------------
- QUARTO_PROJECT_OUTPUT_FILES: Newline-separated list of rendered files
  (automatically set by Quarto)

Author: Market Research Automation System
"""

import os
import time
import shutil
import subprocess


def git_short_hash():
    """
    Get the short git commit hash (7 characters) if available.

    This function was originally used for commit-based versioning but is
    currently not used. Kept for potential future use.

    Returns:
        str or None: Short commit hash (e.g., "a1b2c3d") or None if git unavailable

    Example:
        >>> hash = git_short_hash()
        >>> print(hash)  # Output: "a1b2c3d" or None
    """
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None


def update_archive_qmd(qmd_file_path):
    """
    Update archive/index.qmd with a markdown list of all archived reports.

    This function scans the persistent archive folder (archived_reports/)
    and generates a static markdown file listing all available reports.
    The list is sorted in reverse chronological order (newest first).

    Args:
        qmd_file_path (str): Path to archive/index.qmd file to update

    Generates:
        A .qmd file with structure:
        ---
        title: Archive
        ---

        # Past Reports

        - [report_2025-01-15](report_2025-01-15.html)
        - [report_2025-01-14](report_2025-01-14.html)
        ...

    Example:
        >>> update_archive_qmd("archive/index.qmd")
        --- Updating archive index.qmd ---
        ✅ Successfully updated archive/index.qmd
        🗂  Reports listed: 15
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


# ============================================================================
# MAIN SCRIPT EXECUTION
# ============================================================================
"""
Main logic flow:
1. Read list of rendered files from Quarto environment variable
2. Find report.html in the list
3. Rename report.html and its resources folder with timestamp
4. Create stable "report-latest.html" copy
5. Archive dated report to persistent storage
6. Copy supporting assets (charts, site_libs, resources)
7. Archive source .qmd file
8. Update archive index
9. Deploy all archived content to docs/archive/ for GitHub Pages
"""

# Read the list of files Quarto just rendered
# Format: "path/to/file1.html\npath/to/file2.html\n..."
out_files = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").strip()

# If no files were rendered, exit early (nothing to do)
if not out_files:
    exit(0)

# Split into individual file paths and remove empty lines
files = [f for f in out_files.splitlines() if f.strip()]

# Generate timestamp suffix for this render (format: YYYY-MM-DD)
ts = time.strftime("%Y-%m-%d")
suffix = ts

# Process each rendered file
for f in files:
    # Skip if file doesn't exist (shouldn't happen, but be safe)
    if not os.path.exists(f):
        continue

    # Extract filename and extension
    base, ext = os.path.splitext(os.path.basename(f))

    # We only process report.html (skip index.html, about.html, etc.)
    if base != "report" or ext != ".html":
        continue

    # Get directory containing the report (usually "docs/")
    dirn = os.path.dirname(f) or "."

    # New filename: report_2025-01-15.html
    new_base = f"{base}_{suffix}"
    new_name = os.path.join(dirn, new_base + ext)

    # ========================================================================
    # STEP 1: Check for Quarto resources folder BEFORE renaming
    # ========================================================================
    # Quarto may create a "report_files/" folder with embedded images, plots, etc.
    # We need to check for this BEFORE renaming the main HTML file
    res_dir = os.path.join(dirn, base + "_files")
    has_resources = os.path.isdir(res_dir)

    print(f"Processing report: {f}")
    print(f"Resources directory exists: {has_resources}")
    if has_resources:
        print(f"Resources location: {res_dir}")

    # ========================================================================
    # STEP 2: Rename the main report HTML file
    # ========================================================================
    shutil.move(f, new_name)
    print("Renamed:", f, "->", new_name)

    # ========================================================================
    # STEP 3: Rename resources folder if it exists
    # ========================================================================
    # Must rename from "report_files/" to "report_2025-01-15_files/"
    # so HTML links remain functional
    new_res_dir = None
    if has_resources:
        new_res = os.path.join(dirn, new_base + "_files")
        shutil.move(res_dir, new_res)
        new_res_dir = new_res
        print("Renamed resources:", res_dir, "->", new_res)

    # ========================================================================
    # STEP 4: Create stable "latest" copy for consistent URLs
    # ========================================================================
    # This creates "report-latest.html" which always points to the most recent report
    # Useful for bookmarks and external links that should always show current report
    stable = os.path.join(dirn, f"{base}-latest{ext}")
    shutil.copyfile(new_name, stable)
    print("Copied latest:", new_name, "->", stable)

    # ========================================================================
    # STEP 5: Archive dated report to persistent storage
    # ========================================================================
    # Store in "archived_reports/" (outside of docs/) for persistent storage
    # This folder persists across renders and is source of truth for all archives
    persistent_archive = "archived_reports"
    os.makedirs(persistent_archive, exist_ok=True)
    archive_dest = os.path.join(persistent_archive, os.path.basename(new_name))
    shutil.copy(new_name, archive_dest)
    print("Copied to persistent archive:", new_name, "->", archive_dest)

    # ========================================================================
    # STEP 6: Copy charts directory for archived reports
    # ========================================================================
    # All archived reports share the same charts folder (charts are overwritten each render)
    # This ensures archived reports can display their charts correctly
    charts_dir = "docs/charts"
    if os.path.isdir(charts_dir):
        report_charts_dir = os.path.join(persistent_archive, "charts")
        if os.path.exists(report_charts_dir):
            shutil.rmtree(report_charts_dir)  # Remove old charts
        shutil.copytree(charts_dir, report_charts_dir)  # Copy new charts
        print("✅ Copied charts for archive:", charts_dir, "->", report_charts_dir)

    # ========================================================================
    # STEP 7: Copy site_libs for consistent styling
    # ========================================================================
    # Quarto's site_libs contains CSS, JavaScript, and fonts for the website
    # Archived reports need these files to maintain proper styling
    site_libs_dir = "docs/site_libs"
    if os.path.isdir(site_libs_dir):
        archive_site_libs = os.path.join(persistent_archive, "site_libs")
        if os.path.exists(archive_site_libs):
            shutil.rmtree(archive_site_libs)  # Remove old site_libs
        shutil.copytree(site_libs_dir, archive_site_libs)  # Copy new site_libs
        print("✅ Copied site_libs for archive:", site_libs_dir, "->", archive_site_libs)

    # ========================================================================
    # STEP 8: Copy Quarto resources folder (if exists)
    # ========================================================================
    # If the report has embedded content (images, plots), copy to persistent archive
    # This is the renamed "report_2025-01-15_files/" folder
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

    # ========================================================================
    # STEP 9: Archive the source .qmd file
    # ========================================================================
    # Keep a copy of the report.qmd source file for reference
    # Useful for debugging or understanding what data/prompts were used
    source_qmd = "report.qmd"
    archive_qmd_dir = "archive_qmd"
    os.makedirs(archive_qmd_dir, exist_ok=True)
    archive_qmd_name = f"report_{suffix}.qmd"
    dest_qmd_path = os.path.join(archive_qmd_dir, archive_qmd_name)
    shutil.copyfile(source_qmd, dest_qmd_path)
    print("Archived source:", source_qmd, "->", dest_qmd_path)

    # ========================================================================
    # STEP 10: Update archive index page
    # ========================================================================
    # Generate/update archive/index.qmd with list of all archived reports
    # This creates the archive landing page users will see
    qmd_file_path = "archive/index.qmd"
    update_archive_qmd(qmd_file_path)

    # ========================================================================
    # STEP 11: Deploy archives to docs/archive/ for GitHub Pages
    # ========================================================================
    # CRITICAL: Copy everything from persistent archive to docs/archive/
    # GitHub Pages serves from docs/, so archived content must be there
    # This is the final step that makes archives accessible online
    print("\n--- Copying archived reports to docs/archive for deployment ---")
    docs_archive = "docs/archive"
    os.makedirs(docs_archive, exist_ok=True)

    if os.path.exists(persistent_archive):
        for item in os.listdir(persistent_archive):
            src = os.path.join(persistent_archive, item)
            dst = os.path.join(docs_archive, item)

            if os.path.isfile(src):
                # Copy individual files (HTML reports)
                shutil.copy2(src, dst)
                print(f"📄 Copied to docs/archive: {item}")
            elif os.path.isdir(src):
                # Copy folders (charts/, site_libs/, report_*_files/)
                if os.path.exists(dst):
                    shutil.rmtree(dst)  # Remove old version
                shutil.copytree(src, dst)
                print(f"📁 Copied folder to docs/archive: {item}")

    print("✅ All archived content ready for deployment")
