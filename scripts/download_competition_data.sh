#!/bin/bash
# Download competition data for the GEMS Prize Challenge
# Requires: wget or curl
# 
# Option 1: Download from Dropbox links (no login needed)
# Option 2: Download from DrivenData (requires competition login)
#
# Reference: https://www.drivendata.org/competitions/306/competition-doe-gems/data/

set -e

DATA_DIR="$(dirname "$0")/../data"
mkdir -p "$DATA_DIR"

echo "=============================================="
echo "GEMS Competition Data Download"
echo "=============================================="
echo ""

# Check for existing files
check_file() {
    local name="$1"
    local path="$2"
    if [ -f "$path" ] && [ -s "$path" ]; then
        echo "✓ $name already exists ($(du -h "$path" | cut -f1))"
        return 0
    else
        echo "✗ $name not found or empty"
        return 1
    fi
}

all_present=true

check_file "training_features.tif" "$DATA_DIR/training_features.tif" || all_present=false
check_file "labels.tif" "$DATA_DIR/labels.tif" || all_present=false
check_file "sample_submission.tif" "$DATA_DIR/sample_submission.tif" || all_present=false
check_file "1m_DEM_links.csv" "$DATA_DIR/1m_DEM_links.csv" || all_present=false

if $all_present; then
    echo ""
    echo "All data files present. Ready to proceed."
    echo "Run: python scripts/prepare_data.py"
    exit 0
fi

echo ""
echo "=============================================="
echo "DOWNLOAD OPTIONS"
echo "=============================================="
echo ""
echo "Option 1: Dropbox links (no login required)"
echo "  These files may not include all competition data."
echo "  Source: https://www.dropbox.com/sh/... (see README)"
echo ""
echo "Option 2: DrivenData (requires login)"
echo "  1. Sign in at: https://www.drivendata.org/competitions/306/competition-doe-gems/data/"
echo "  2. Download all files to: $DATA_DIR/"
echo "  Required files:"
echo "    - training_features.tif"
echo "    - labels.tif"
echo "    - sample_submission.tif"
echo "    - 1m_DEM_links.csv"
echo ""
echo "Option 3: Automated download with credentials"
echo "  Set DRIVENDATA_USER and DRIVENDATA_PASS environment variables"
echo "  and run: python scripts/download_with_credentials.py"
echo ""

# Try Dropbox downloads
echo "Attempting Dropbox downloads..."
echo ""

# Example submission (template)
if ! check_file "sample_submission.tif" "$DATA_DIR/sample_submission.tif" 2>/dev/null; then
    echo "Downloading example_submission.tif (template)..."
    curl -L -o "$DATA_DIR/sample_submission.tif" \
        "https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=1" 2>/dev/null || \
    wget -q -O "$DATA_DIR/sample_submission.tif" \
        "https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=1" 2>/dev/null || \
    echo "  ✗ Failed to download example_submission.tif"
fi

# Existing faults
if ! check_file "existing_faults.tif" "$DATA_DIR/existing_faults.tif" 2>/dev/null; then
    echo "Downloading existing_faults.tif..."
    curl -L -o "$DATA_DIR/existing_faults.tif" \
        "https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=1" 2>/dev/null || \
    wget -q -O "$DATA_DIR/existing_faults.tif" \
        "https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=1" 2>/dev/null || \
    echo "  ✗ Failed to download existing_faults.tif"
fi

# Numerical features
if ! check_file "gems-geodawn-numerical-features.tif" "$DATA_DIR/gems-geodawn-numerical-features.tif" 2>/dev/null; then
    echo "Downloading gems-geodawn-numerical-features.tif..."
    curl -L -o "$DATA_DIR/gems-geodawn-numerical-features.tif" \
        "https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=1" 2>/dev/null || \
    wget -q -O "$DATA_DIR/gems-geodawn-numerical-features.tif" \
        "https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=1" 2>/dev/null || \
    echo "  ✗ Failed to download gems-geodawn-numerical-features.tif"
fi

echo ""
echo "=============================================="
echo "VERIFICATION"
echo "=============================================="
echo ""
echo "Check downloaded files:"
ls -lh "$DATA_DIR/"*.tif "$DATA_DIR/"*.csv 2>/dev/null || echo "  No files downloaded."
echo ""
echo "If downloads failed, use Option 2 (manual download from DrivenData)."
echo "Then run: python scripts/prepare_data.py"
