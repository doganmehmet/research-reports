import subprocess
from datetime import datetime
import os

# --- Configuration ---
TEMPLATE_FILE = "_report-template.qmd"
REPORTS_DIR = "reports"
OUTPUT_DIR = "docs"

# --- Automation Logic ---
today_str = datetime.now().strftime('%Y-%m-%d')
report_qmd_path = f"{REPORTS_DIR}/{today_str}-market-report.qmd"

os.makedirs(REPORTS_DIR, exist_ok=True)

# 1. CREATE THE CORRECT .QMD STUB FILE
# This version has the correct double curly braces {{{{...}}}} which
# Python's f-string will turn into {{...}} in the output file.
report_content = f"""---
title: "Market Research: {today_str}"
date: "{today_str}"
params:
  report_date: "{today_str}"
---

{{{{< include ../{TEMPLATE_FILE} >}}}}
"""
with open(report_qmd_path, "w") as f:
    f.write(report_content)

print(f"✓ Created report stub: {report_qmd_path}")

# 2. RENDER THE ENTIRE WEBSITE
print("▶️  Rendering the full website...")
try:
    subprocess.run(["quarto", "render"], check=True)
    print("✅ Success! Website rendered.")
except Exception as e:
    print(f"❌ An error occurred: {e}")