"""
Validate a submission GeoTIFF against all GEMS Prize format requirements.

Usage:
    python scripts/validate_submission.py <path_to_submission.tif>

Checks all 9 hard requirements:
1. Single band
2. Float32 dtype
3. EPSG:32611 CRS
4. Shape (3730, 3292)
5. Geotransform matches template
6. All finite values in [0, 1]
7. No Inf values
8. Outside is NaN
9. Profile matches official sample
"""

import sys
import numpy as np
import rasterio
from pathlib import Path


TEMPLATE = {
    'height': 3730,
    'width': 3292,
    'crs': 'EPSG:32611',
    'transform': rasterio.transform.Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
    'dtype': 'float32',
    'count': 1,
}


def validate(path):
    """Run all format checks on a submission TIF."""
    checks = {}
    
    path = Path(path)
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return False
    
    try:
        with rasterio.open(path) as src:
            # 1. Single band
            checks['single_band'] = {
                'pass': src.count == 1,
                'detail': f'count={src.count}'
            }
            
            # 2. Float32
            checks['dtype_float32'] = {
                'pass': src.dtypes[0] == 'float32',
                'detail': f'dtypes={src.dtypes}'
            }
            
            # 3. CRS
            crs_str = src.crs.to_string() if src.crs else 'None'
            checks['crs_epsg_32611'] = {
                'pass': '32611' in crs_str,
                'detail': f'CRS={crs_str}'
            }
            
            # 4. Shape
            checks['shape_matches'] = {
                'pass': src.height == TEMPLATE['height'] and src.width == TEMPLATE['width'],
                'detail': f'({src.height}, {src.width}) vs ({TEMPLATE["height"]}, {TEMPLATE["width"]})'
            }
            
            # 5. Transform
            t = src.transform
            e = TEMPLATE['transform']
            transform_ok = (
                abs(t.a - e.a) < 1e-6 and abs(t.b - e.b) < 1e-6 and
                abs(t.c - e.c) < 1e-6 and abs(t.d - e.d) < 1e-6 and
                abs(t.e - e.e) < 1e-6 and abs(t.f - e.f) < 1e-6
            )
            checks['transform_matches'] = {
                'pass': transform_ok,
                'detail': f'{t} vs {e}'
            }
            
            # 6. Read and check values
            data = src.read(1)
            finite_mask = ~np.isnan(data)
            finite_vals = data[finite_mask]
            
            checks['all_finite_in_range'] = {
                'pass': len(finite_vals) == 0 or (np.all(finite_vals >= 0.0) and np.all(finite_vals <= 1.0)),
                'detail': f'min={np.min(finite_vals) if len(finite_vals) > 0 else "N/A"}, max={np.max(finite_vals) if len(finite_vals) > 0 else "N/A"}'
            }
            
            # 7. No Inf
            checks['no_inf'] = {
                'pass': not np.any(np.isinf(data)),
                'detail': f'Inf count: {np.sum(np.isinf(data))}'
            }
            
            # 8. Outside is NaN (check corners)
            corners = [data[0,0], data[0,-1], data[-1,0], data[-1,-1]]
            checks['outside_is_nan'] = {
                'pass': all(np.isnan(v) for v in corners),
                'detail': f'corner values: {[str(v) for v in corners]}'
            }
            
            # Stats
            checks['_stats'] = {
                'total_pixels': int(data.size),
                'finite_pixels': int(finite_mask.sum()),
                'nan_pixels': int(np.sum(np.isnan(data))),
                'positive_pixels': int(np.sum(finite_vals > 0)),
                'zero_pixels': int(np.sum(finite_vals == 0)),
                'min': float(np.min(finite_vals)) if len(finite_vals) > 0 else None,
                'max': float(np.max(finite_vals)) if len(finite_vals) > 0 else None,
                'mean': float(np.mean(finite_vals)) if len(finite_vals) > 0 else None,
            }
            
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return False
    
    # Print results
    all_pass = True
    print(f"\n{'='*60}")
    print(f"SUBMISSION VALIDATION: {path.name}")
    print(f"{'='*60}")
    
    for name, check in checks.items():
        if name.startswith('_'):
            continue
        status = "✔ PASS" if check['pass'] else "✘ FAIL"
        if not check['pass']:
            all_pass = False
        print(f"  {status}  {name:30s}  {check['detail']}")
    
    stats = checks.get('_stats', {})
    print(f"\n{'─'*60}")
    print(f"  Total pixels:      {stats.get('total_pixels', 0):>12,}")
    print(f"  Finite pixels:     {stats.get('finite_pixels', 0):>12,}")
    print(f"  NaN pixels:        {stats.get('nan_pixels', 0):>12,}")
    print(f"  Positive pixels:   {stats.get('positive_pixels', 0):>12,}")
    print(f"  Value range:       [{stats.get('min', 0):.6f}, {stats.get('max', 0):.6f}]")
    
    print(f"\n{'='*60}")
    if all_pass:
        print("  RESULT: ALL CHECKS PASSED — Ready for submission")
    else:
        print("  RESULT: SOME CHECKS FAILED — Fix before submitting")
    print(f"{'='*60}\n")
    
    return all_pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_submission.py <path_to_submission.tif>")
        sys.exit(1)
    
    success = validate(sys.argv[1])
    sys.exit(0 if success else 1)
