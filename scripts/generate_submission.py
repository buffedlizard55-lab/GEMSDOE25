"""
Generate a valid GeoTIFF submission for the GEMS Prize Challenge.

Creates a single-band float32 GeoTIFF with:
- EPSG:32611 (UTM Zone 11N)
- 3730 × 3292 pixels at 100m resolution
- Values in [0, 1] inside footprint, NaN outside
- Geotransform: (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)

This matches the official submission format requirements.
Reference: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format
"""

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from pathlib import Path
import hashlib
import json
from datetime import datetime


# ============================================================
# COMPETITION TEMPLATE CONSTANTS
# ============================================================

# From the official sample_submission.tif and example_submission.tif
# EPSG:32611, UTM Zone 11N
TEMPLATE = {
    'height': 3730,
    'width': 3292,
    'crs': 'EPSG:32611',
    'transform': rasterio.transform.Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
    'dtype': 'float32',
    'count': 1,
    'nodata': np.nan,
}

FOOTPRINT_PIXELS = TEMPLATE['height'] * TEMPLATE['width']  # 12,279,160 total
# Approximate in-footprint pixels from GEMSDOE24 analysis: 5,167,373
# The exact footprint depends on the GeoDAWN survey area boundary


def create_template_array(value=np.nan):
    """Create a full-size array with the competition template."""
    arr = np.full((TEMPLATE['height'], TEMPLATE['width']), value, dtype=np.float32)
    return arr


def write_submission_tif(
    prediction: np.ndarray,
    output_path: str,
    nan_outside: bool = True,
    footprint_mask: np.ndarray = None,
) -> dict:
    """
    Write a valid submission GeoTIFF.
    
    Parameters
    ----------
    prediction : np.ndarray
        2D array with values in [0, 1]. Must match template shape.
    output_path : str
        Path to save the GeoTIFF.
    nan_outside : bool
        If True, set pixels outside the footprint to NaN.
        If False, set them to 0.0 (allfinite fallback).
    footprint_mask : np.ndarray, optional
        Boolean mask of the in-footprint region. If None, uses a default
        approximation of the GeoDAWN survey area.
        
    Returns
    -------
    dict with file metadata and SHA-256 hash
    """
    assert prediction.shape == (TEMPLATE['height'], TEMPLATE['width']), \
        f"Shape mismatch: {prediction.shape} vs ({TEMPLATE['height']}, {TEMPLATE['width']})"
    
    # Ensure float32
    prediction = prediction.astype(np.float32)
    
    # Clip to [0, 1]
    prediction = np.clip(prediction, 0.0, 1.0)
    
    # Apply footprint mask
    if footprint_mask is not None:
        if nan_outside:
            prediction[~footprint_mask] = np.nan
        else:
            prediction[~footprint_mask] = 0.0
    
    # Write GeoTIFF
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    profile = {
        'driver': 'GTiff',
        'height': TEMPLATE['height'],
        'width': TEMPLATE['width'],
        'count': 1,
        'dtype': 'float32',
        'crs': TEMPLATE['crs'],
        'transform': TEMPLATE['transform'],
        'nodata': np.nan if nan_outside else None,
        'compress': 'deflate',
    }
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(prediction, 1)
    
    # Compute SHA-256
    sha256 = hashlib.sha256()
    with open(output_path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    file_hash = sha256.hexdigest()
    
    # File stats
    in_footprint = prediction[~np.isnan(prediction)] if nan_outside else prediction.ravel()
    positive_pixels = int(np.sum(in_footprint > 0))
    
    info = {
        'path': output_path,
        'sha256': file_hash,
        'shape': list(prediction.shape),
        'dtype': 'float32',
        'crs': 'EPSG:32611',
        'nan_outside': nan_outside,
        'total_pixels': int(prediction.size),
        'footprint_pixels': int(len(in_footprint)),
        'positive_pixels': positive_pixels,
        'min_value': float(np.nanmin(in_footprint)) if len(in_footprint) > 0 else 0.0,
        'max_value': float(np.nanmax(in_footprint)) if len(in_footprint) > 0 else 0.0,
        'mean_value': float(np.nanmean(in_footprint)) if len(in_footprint) > 0 else 0.0,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }
    
    return info


def generate_ridge_based_prediction(features_path=None, template_only=True):
    """
    Generate a ridge-based fault prediction.
    
    Based on the H19-5 methodology which achieved 0.1922:
    - Topographic openness (sky-view factor from DEM)
    - Local relief model
    - Power-law fault population scaling
    - Backward thermal/geochemical conduit inversion
    - Geopotential strike worms
    
    For template-only mode, creates a sample prediction for testing
    the submission pipeline without actual features.
    """
    if template_only:
        # Create a synthetic prediction for pipeline testing
        pred = create_template_array(0.0)
        
        # Generate synthetic ridge-like patterns
        rng = np.random.RandomState(42)
        
        # Create NW-SE trending ridges (consistent with Great Basin extension)
        y, x = np.mgrid[0:TEMPLATE['height'], 0:TEMPLATE['width']]
        
        # Multiple NW-SE trending lineaments
        for offset in np.linspace(-500, 500, 8):
            # NW-SE direction: y + x = constant
            line = np.abs((y + x + offset * 3) % 200 - 100) < 3
            pred[line] = 0.7 + rng.random(line.sum()) * 0.3
        
        # Add some NE-SW cross structures
        for offset in np.linspace(-300, 300, 5):
            line = np.abs((y - x + offset * 5) % 300 - 150) < 2
            pred[line] = 0.5 + rng.random(line.sum()) * 0.3
        
        # Create approximate footprint (GeoDAWN area is roughly centered)
        center_h, center_w = TEMPLATE['height'] // 2, TEMPLATE['width'] // 2
        fy, fx = np.mgrid[0:TEMPLATE['height'], 0:TEMPLATE['width']]
        # Approximate footprint as an irregular polygon
        footprint = ((fx - center_w)**2 / (1200**2) + (fy - center_h)**2 / (1500**2)) < 1.0
        
        # Set outside to NaN
        pred[~footprint] = np.nan
        pred[footprint] = np.clip(pred[footprint], 0, 1)
        
        return pred, footprint
    
    # Full feature-based prediction would go here
    # Requires competition data
    raise NotImplementedError("Full prediction requires competition data. "
                            "Run scripts/prepare_data.py first.")


def validate_submission(path):
    """
    Validate a submission TIF against all format requirements.
    
    Returns dict of checks with pass/fail status.
    """
    checks = {}
    
    try:
        with rasterio.open(path) as src:
            # 1. Single band
            checks['single_band'] = src.count == 1
            
            # 2. Float32
            checks['dtype_float32'] = src.dtypes[0] == 'float32'
            
            # 3. CRS
            checks['crs_epsg_32611'] = src.crs is not None and 'EPSG:32611' in str(src.crs.to_string())
            
            # 4. Shape
            checks['shape_matches'] = (src.height == TEMPLATE['height'] and 
                                       src.width == TEMPLATE['width'])
            
            # 5. Transform
            expected = TEMPLATE['transform']
            actual = src.transform
            checks['transform_matches'] = (
                abs(actual.a - expected.a) < 1e-6 and
                abs(actual.b - expected.b) < 1e-6 and
                abs(actual.c - expected.c) < 1e-6 and
                abs(actual.d - expected.d) < 1e-6 and
                abs(actual.e - expected.e) < 1e-6 and
                abs(actual.f - expected.f) < 1e-6
            )
            
            # 6. Read data
            data = src.read(1)
            
            # 7. Values in [0, 1] where not NaN
            finite_mask = ~np.isnan(data)
            finite_vals = data[finite_mask]
            checks['all_finite_in_range'] = bool(
                len(finite_vals) == 0 or 
                (np.all(finite_vals >= 0.0) and np.all(finite_vals <= 1.0))
            )
            checks['no_negative'] = bool(len(finite_vals) == 0 or np.all(finite_vals >= 0.0))
            checks['no_above_one'] = bool(len(finite_vals) == 0 or np.all(finite_vals <= 1.0))
            
            # 8. No Inf
            checks['no_inf'] = bool(~np.any(np.isinf(data)))
            
            # 9. Outside is NaN
            # (approximate: check corners which should be outside)
            corner_vals = [data[0, 0], data[0, -1], data[-1, 0], data[-1, -1]]
            checks['outside_is_nan'] = all(np.isnan(v) for v in corner_vals)
            
            # Summary stats
            checks['_stats'] = {
                'total_pixels': int(data.size),
                'finite_pixels': int(finite_mask.sum()),
                'positive_pixels': int(np.sum(finite_vals > 0)),
                'min': float(np.min(finite_vals)) if len(finite_vals) > 0 else None,
                'max': float(np.max(finite_vals)) if len(finite_vals) > 0 else None,
                'mean': float(np.mean(finite_vals)) if len(finite_vals) > 0 else None,
            }
    
    except Exception as e:
        checks['error'] = str(e)
    
    checks['_all_pass'] = all(v for k, v in checks.items() 
                               if not k.startswith('_') and isinstance(v, bool))
    
    return checks


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'validate':
        path = sys.argv[2]
        checks = validate_submission(path)
        print(f"\nSubmission validation: {path}")
        print("=" * 50)
        for k, v in checks.items():
            if k.startswith('_'):
                continue
            status = "✔ PASS" if v else "✘ FAIL"
            print(f"  {k:30s} {status}")
        print(f"\n  Overall: {'ALL CHECKS PASSED' if checks['_all_pass'] else 'SOME CHECKS FAILED'}")
        if '_stats' in checks:
            stats = checks['_stats']
            print(f"\n  Stats:")
            print(f"    Total pixels:    {stats['total_pixels']:,}")
            print(f"    Finite pixels:   {stats['finite_pixels']:,}")
            print(f"    Positive pixels: {stats['positive_pixels']:,}")
            print(f"    Value range:     [{stats['min']:.6f}, {stats['max']:.6f}]")
        sys.exit(0 if checks['_all_pass'] else 1)
    
    else:
        # Generate a template submission
        output = "docs/downloads/gems25-template-v1-nan.tif"
        pred, footprint = generate_ridge_based_prediction(template_only=True)
        info = write_submission_tif(pred, output, nan_outside=True, footprint_mask=footprint)
        
        print("Generated template submission:")
        print(f"  Path: {info['path']}")
        print(f"  SHA-256: {info['sha256']}")
        print(f"  Shape: {info['shape']}")
        print(f"  Footprint pixels: {info['footprint_pixels']:,}")
        print(f"  Positive pixels: {info['positive_pixels']:,}")
        print(f"  Value range: [{info['min_value']:.6f}, {info['max_value']:.6f}]")
        
        # Validate
        checks = validate_submission(output)
        print(f"\n  Validation: {'ALL PASSED' if checks['_all_pass'] else 'SOME FAILED'}")
        
        # Save info
        info_path = output.replace('.tif', '-info.json')
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)
        print(f"  Info saved: {info_path}")
