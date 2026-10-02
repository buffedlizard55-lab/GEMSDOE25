"""
Download and prepare competition data for the GEMS Prize Challenge.

Competition data is available from:
  - https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (requires login)
  - Dropbox links (see README.md)

Files needed:
  - training_features.tif  (multi-band GeoTIFF with all numeric features)
  - labels.tif             (binary fault labels from USGS/INGENIOUS)
  - sample_submission.tif  (template GeoTIFF with correct CRS/shape/transform)
  - 1m_DEM_links.csv       (URLs for 1m resolution DEMs from USGS 3DEP)
"""

import os
import sys
import json
import numpy as np
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"

# Feature band descriptions from the competition
FEATURE_BANDS = [
    {"name": "surface_conductivity", "category": "conductivity", 
     "description": "Surface conductivity and depth to conductive base surface"},
    {"name": "depth_to_conductive_base", "category": "conductivity",
     "description": "Depth to conductive base surface"},
    {"name": "detrended_elevation", "category": "topography",
     "description": "Detrended elevation"},
    {"name": "slope_of_detrended_elevation", "category": "topography",
     "description": "Slope of detrended elevation"},
    {"name": "dilatation_rate", "category": "strain",
     "description": "Dilatation rate"},
    {"name": "shear_strain_rate", "category": "strain",
     "description": "Shear strain rate"},
    {"name": "second_invariant_strain_rate", "category": "strain",
     "description": "Second invariant of the strain rate tensor"},
    {"name": "isostatic_gravity_anomaly_hg", "category": "gravity",
     "description": "Isostatic gravity anomaly"},
    {"name": "slope_of_isostatic_gravity_anomaly", "category": "gravity",
     "description": "Slope of the isostatic gravity anomaly"},
    {"name": "reduced_to_pole_magnetic_anomaly", "category": "magnetics",
     "description": "Reduced-to-pole magnetic anomaly"},
    {"name": "tmi_hg", "category": "magnetics",
     "description": "Total magnetic intensity"},
    {"name": "vertical_slope_of_tmi", "category": "magnetics",
     "description": "Vertical slope of total magnetic intensity"},
    {"name": "horizontal_slope_of_tmi", "category": "magnetics",
     "description": "Horizontal slope of total magnetic intensity"},
    {"name": "depth_to_magnetic_source", "category": "magnetics",
     "description": "Top-of-crustal magnetic source depth estimate"},
    {"name": "earthquake_density", "category": "seismicity",
     "description": "Density of earthquakes"},
]


def check_data_available():
    """Check which data files are available."""
    files = {
        'training_features': DATA_DIR / 'training_features.tif',
        'labels': DATA_DIR / 'labels.tif',
        'sample_submission': DATA_DIR / 'sample_submission.tif',
        'dem_links': DATA_DIR / '1m_DEM_links.csv',
    }
    
    status = {}
    for name, path in files.items():
        status[name] = {
            'path': str(path),
            'exists': path.exists(),
            'size_mb': round(path.stat().st_size / 1e6, 1) if path.exists() else 0,
        }
    
    return status


def load_features():
    """Load and normalize competition features."""
    try:
        import rasterio
    except ImportError:
        print("ERROR: rasterio not installed. Run: pip install rasterio")
        sys.exit(1)
    
    features_path = DATA_DIR / 'training_features.tif'
    if not features_path.exists():
        print(f"ERROR: {features_path} not found.")
        print("Download from: https://www.drivendata.org/competitions/306/competition-doe-gems/data/")
        sys.exit(1)
    
    with rasterio.open(features_path) as src:
        data = src.read()  # (bands, height, width)
        meta = src.meta
        transform = src.transform
        crs = src.crs
        
        # Read band descriptions
        bands = []
        for i in range(1, src.count + 1):
            tags = src.tags(i)
            bands.append(tags)
    
    # Replace nodata with NaN
    data = data.astype(np.float32)
    nodata = meta.get('nodata', -9999)
    data[data < -1e38] = np.nan
    
    # Normalize to [0, 1] per band
    for i in range(data.shape[0]):
        band = data[i]
        valid = ~np.isnan(band)
        if valid.any():
            bmin = np.nanmin(band)
            bmax = np.nanmax(band)
            if bmax > bmin:
                data[i][valid] = (band[valid] - bmin) / (bmax - bmin)
    
    # Reshape to (height, width, bands)
    features = np.moveaxis(data, 0, -1)
    
    return features, bands, transform, crs


def load_labels():
    """Load fault labels."""
    import rasterio
    
    labels_path = DATA_DIR / 'labels.tif'
    if not labels_path.exists():
        print(f"ERROR: {labels_path} not found.")
        sys.exit(1)
    
    with rasterio.open(labels_path) as src:
        labels = src.read(1).astype(np.float32)
        meta = src.meta
        transform = src.transform
        crs = src.crs
    
    # Binarize: any positive value = fault
    labels[labels < 1] = 0
    labels[labels >= 1] = 1
    
    return labels, transform, crs


def compute_derived_features(features, bands, transform):
    """
    Compute derived features not in the original training_features.tif:
    - DEM curvature (Laplacian)
    - Local relief model
    - Topographic openness (approximate)
    - Distance to existing faults
    """
    from scipy import ndimage
    
    h, w, n_bands = features.shape
    derived = {}
    
    # Find detrended elevation band
    elev_idx = None
    for i, b in enumerate(bands):
        if 'detrended_elevation' in str(b.get('description', '')).lower():
            elev_idx = i
            break
    
    if elev_idx is not None:
        elev = features[:, :, elev_idx]
        
        # Curvature (Laplacian)
        kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        curvature = ndimage.convolve(np.nan_to_num(elev, 0), kernel)
        derived['dem_curvature'] = curvature
        
        # Local relief (max - min in 5x5 window)
        elev_filled = np.nan_to_num(elev, 0)
        max_filter = ndimage.maximum_filter(elev_filled, size=5)
        min_filter = ndimage.minimum_filter(elev_filled, size=5)
        derived['local_relief_model'] = max_filter - min_filter
        
        # Approximate openness (difference from mean in neighborhood)
        mean_filter = ndimage.uniform_filter(elev_filled, size=11)
        derived['topographic_openness'] = elev_filled - mean_filter
    
    return derived


def print_data_summary(features, labels, bands):
    """Print a summary of the loaded data."""
    print("\n" + "=" * 60)
    print("COMPETITION DATA SUMMARY")
    print("=" * 60)
    print(f"  Features shape: {features.shape}")
    print(f"  Labels shape:   {labels.shape}")
    print(f"  Number of bands: {features.shape[2] if features.ndim == 3 else 'N/A'}")
    print(f"  Fault pixels:   {int(np.sum(labels > 0)):,} ({100*np.mean(labels > 0):.4f}%)")
    print(f"  NaN fraction:   {np.mean(np.isnan(features)):.4f}")
    
    print(f"\n  Feature bands ({len(bands)}):")
    for i, b in enumerate(bands):
        desc = b.get('description', 'unknown')
        cat = b.get('data_category', 'unknown')
        print(f"    Band {i+1:2d}: {desc[:50]:50s} [{cat}]")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("GEMS Competition Data Preparation")
    print("=" * 60)
    
    # Check what's available
    status = check_data_available()
    print("\nData file status:")
    all_present = True
    for name, info in status.items():
        exists = "✓" if info['exists'] else "✗"
        size = f"({info['size_mb']:.1f} MB)" if info['exists'] else "(missing)"
        print(f"  {exists} {name:25s} {info['path']} {size}")
        if not info['exists']:
            all_present = False
    
    if not all_present:
        print("\n" + "=" * 60)
        print("MISSING DATA FILES")
        print("=" * 60)
        print("\nTo download competition data:")
        print("1. Sign in at https://www.drivendata.org/competitions/306/competition-doe-gems/data/")
        print("2. Download all files to the data/ directory:")
        print("   - training_features.tif")
        print("   - labels.tif")
        print("   - sample_submission.tif")
        print("   - 1m_DEM_links.csv")
        print("\nOr use the provided download script:")
        print("   bash scripts/download_competition_data.sh")
        sys.exit(1)
    
    # Load and summarize
    features, bands, transform, crs = load_features()
    labels, l_transform, l_crs = load_labels()
    print_data_summary(features, labels, bands)
    
    # Compute derived features
    print("Computing derived features...")
    derived = compute_derived_features(features, bands, transform)
    print(f"  Derived features: {list(derived.keys())}")
    
    print("\nData preparation complete.")
    print("Run 'python scripts/factorial_design.py' to execute the experiment.")
