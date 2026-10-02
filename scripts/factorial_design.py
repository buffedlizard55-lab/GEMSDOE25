"""
Fractional Factorial Experiment Design for GEMS Feature Families.

Replaces one-factor-at-a-time (OFAT) testing with a structured 2^(5-1) 
half-fraction factorial design across 5 feature families.

Reference: Box, Hunter, and Hunter, "Statistics for Experimenters"
- Sparsity-of-effects principle: real systems are dominated by main effects 
  and low-order interactions, not high-order ones
- A 2^(5-1) design (16 runs) estimates all 5 main effects and all 10 
  pairwise interactions — far fewer than the 32 runs of a full factorial

Feature Families:
    A: Potential-field gradients (gravity slope, magnetic slope, TMI gradients)
    B: DEM curvature/scarp (curvature, openness, local relief, scarp detection)
    C: Strain/seismicity (dilatation, shear strain, earthquake density)
    D: Thermal/geochemical (GDR 1391 springs, wells, geothermometers)
    E: Catalogue-geometry (distance to faults, map-scale corridors)

Design: Resolution V (2^(5-1), generator E = ABCD)
    - All main effects are clear of two-factor interactions
    - All two-factor interactions are aliased with three-factor interactions
    - Under sparsity-of-effects, this is sufficient

Each "run" = train a gradient-boosted classifier using ONLY the specified
feature families, evaluate on the hide-and-recover holdout.
"""

import numpy as np
import json
import os
from itertools import combinations
from datetime import datetime


# ============================================================
# DESIGN MATRIX: 2^(5-1) half-fraction, Resolution V
# Generator: E = ABCD (so that E's column = A×B×C×D element-wise)
# ============================================================

def generate_design_matrix():
    """
    Generate the 2^(5-1) fractional factorial design matrix.
    
    Returns a dict with:
        - 'runs': list of 16 dicts, each mapping factor names to +1/-1
        - 'generators': the defining relation
        - 'alias_structure': what's aliased with what
    """
    factors = ['A', 'B', 'C', 'D', 'E']
    
    # Full 2^4 for A, B, C, D
    base_design = []
    for a in [-1, 1]:
        for b in [-1, 1]:
            for c in [-1, 1]:
                for d in [-1, 1]:
                    # E = A×B×C×D (resolution V generator)
                    e = a * b * c * d
                    run = {'A': a, 'B': b, 'C': c, 'D': d, 'E': e}
                    base_design.append(run)
    
    # Define alias structure for Resolution V
    # Defining relation: I = ABCDE
    # Main effects aliased with 4-factor interactions (negligible under sparsity)
    # 2-factor interactions aliased with 3-factor interactions (negligible under sparsity)
    alias_structure = {
        'defining_relation': 'I = ABCDE',
        'main_effects_clear': 'All main effects are clear of 2-factor interactions',
        'two_factor_aliases': 'Each 2-factor interaction is aliased with a 3-factor interaction',
        'resolution': 'V (5-1)',
    }
    
    return {
        'runs': base_design,
        'n_runs': len(base_design),
        'factors': factors,
        'alias_structure': alias_structure,
        'generator': 'E = ABCD',
    }


# ============================================================
# FEATURE FAMILY DEFINITIONS
# ============================================================

FEATURE_FAMILIES = {
    'A': {
        'name': 'potential_field_gradients',
        'description': 'Potential-field gradients: gravity, magnetics, their slopes',
        'layers': [
            'isostatic_gravity_anomaly_hg',
            'slope_of_isostatic_gravity_anomaly',
            'tmi_hg',
            'vertical_slope_of_tmi',
            'horizontal_slope_of_tmi',
            'reduced_to_pole_magnetic_anomaly',
            'depth_to_magnetic_source',
        ],
        'layer_indices': None,  # Filled by prepare_data.py based on actual band indices
    },
    'B': {
        'name': 'dem_curvature_scarp',
        'description': 'DEM curvature/scarp: curvature, openness, local relief',
        'layers': [
            'detrended_elevation',
            'slope_of_detrended_elevation',
            'dem_curvature',           # Derived: Laplacian of DEM
            'dem_openness',            # Derived: sky-view factor
            'local_relief_model',      # Derived: max-min in neighborhood
            'topographic_scarp',       # Derived: ridge-normal gradient anomaly
        ],
        'layer_indices': None,
        'derived_layers': ['dem_curvature', 'dem_openness', 'local_relief_model', 'topographic_scarp'],
    },
    'C': {
        'name': 'strain_seismicity',
        'description': 'Strain and seismicity rates',
        'layers': [
            'dilatation_rate',
            'shear_strain_rate',
            'second_invariant_strain_rate',
            'earthquake_density',
        ],
        'layer_indices': None,
    },
    'D': {
        'name': 'thermal_geochemical',
        'description': 'Thermal and geochemical proxies from GDR 1391',
        'layers': [
            'spring_density',
            'well_density',
            'geothermometer_proximity',
            'backward_conduit_inversion',
            'thermal_anomaly_proxy',
        ],
        'layer_indices': None,
        'external_source': 'https://gdr.openei.org/submissions/1391',
    },
    'E': {
        'name': 'catalogue_geometry',
        'description': 'Catalogue-geometry: distance to known faults, map-scale corridors',
        'layers': [
            'distance_to_existing_faults',
            'fault_strike_compatibility',
            'map_scale_correction_corridor',
            'catalogue_density',
        ],
        'layer_indices': None,
        'external_source': 'USGS Quaternary Fault Database / INGENIOUS MAPSCALE field',
    },
}


# ============================================================
# HIDE-AND-RECOVER HOLDOUT
# ============================================================

def create_spatial_holdout(labels, n_quadrants=4, seed=42):
    """
    Create a spatially-blocked hide-and-recover holdout.
    
    Divides the image into n_quadrants spatial blocks, 
    holds out one block at a time for evaluation.
    
    This is the "hide-and-recover" protocol from GEMSDOE10/24:
    - Mask all catalogue faults in the held-out quadrant
    - Train on remaining quadrants
    - Predict on held-out quadrant
    - Measure DTI on the hidden faults
    
    Parameters
    ----------
    labels : np.ndarray
        2D binary fault labels
    n_quadrants : int
        Number of spatial blocks (4 = quadrants)
    seed : int
        Random seed
        
    Returns
    -------
    list of (train_mask, test_mask) pairs
    """
    h, w = labels.shape
    mid_h, mid_w = h // 2, w // 2
    
    # Define quadrant masks
    quadrants = [
        np.zeros_like(labels, dtype=bool),  # top-left
        np.zeros_like(labels, dtype=bool),  # top-right
        np.zeros_like(labels, dtype=bool),  # bottom-left
        np.zeros_like(labels, dtype=bool),  # bottom-right
    ]
    quadrants[0][:mid_h, :mid_w] = True
    quadrants[1][:mid_h, mid_w:] = True
    quadrants[2][mid_h:, :mid_w] = True
    quadrants[3][mid_h:, mid_w:] = True
    
    # Create train/test splits
    splits = []
    for i in range(n_quadrants):
        test_mask = quadrants[i]
        train_mask = ~test_mask
        splits.append((train_mask, test_mask))
    
    return splits


# ============================================================
# RUN THE FACTORIAL EXPERIMENT
# ============================================================

def run_factorial_experiment(features, labels, feature_family_map, save_dir='results'):
    """
    Execute the 2^(5-1) fractional factorial experiment.
    
    For each of the 16 runs:
    1. Select features from the active families
    2. Train a gradient-boosted classifier on 3/4 quadrants
    3. Evaluate on the held-out quadrant
    4. Record DTI
    
    Then analyze:
    - Main effects (which families matter alone)
    - Two-factor interactions (which combinations matter)
    - Rank families by effect size
    """
    from sklearn.ensemble import HistGradientBoostingClassifier
    
    design = generate_design_matrix()
    os.makedirs(save_dir, exist_ok=True)
    
    h, w = labels.shape
    splits = create_spatial_holdout(labels)
    
    results = []
    
    for run_idx, run_config in enumerate(design['runs']):
        # Determine which families are active (+1) or inactive (-1)
        active_families = [f for f, level in run_config.items() if level == 1]
        active_family_names = [FEATURE_FAMILIES[f]['name'] for f in active_families]
        
        # Collect features from active families
        active_features = []
        for f in active_families:
            family = FEATURE_FAMILIES[f]
            if family.get('layer_indices') is not None:
                active_features.extend(family['layer_indices'])
        
        if not active_features:
            # No features: baseline prediction
            result = {
                'run': run_idx,
                'config': run_config,
                'active_families': active_family_names,
                'n_features': 0,
                'mean_dti': 0.0,
                'fold_dtis': [0.0, 0.0, 0.0, 0.0],
            }
            results.append(result)
            continue
        
        # Train on 3 folds, evaluate on held-out fold
        fold_dtis = []
        for train_mask, test_mask in splits:
            # Extract training data
            train_labels = labels[train_mask]
            train_features = features[train_mask][:, active_features]
            
            # Remove NaN
            valid = ~(np.isnan(train_features).any(axis=1) | np.isnan(train_labels))
            X_train = train_features[valid]
            y_train = train_labels[valid].astype(int)
            
            if len(np.unique(y_train)) < 2:
                fold_dtis.append(0.0)
                continue
            
            # Train
            model = HistGradientBoostingClassifier(
                max_iter=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
            )
            model.fit(X_train, y_train)
            
            # Predict on held-out fold
            test_features = features[test_mask][:, active_features]
            test_labels = labels[test_mask]
            valid_test = ~np.isnan(test_features).any(axis=1)
            
            if valid_test.sum() == 0:
                fold_dtis.append(0.0)
                continue
            
            X_test = test_features[valid_test]
            y_test = test_labels[valid_test]
            
            pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Reconstruct 2D prediction for DTI computation
            pred_2d = np.zeros_like(test_labels)
            pred_flat = np.zeros(len(test_labels))
            pred_flat[valid_test] = pred_proba
            # Reshape back to 2D based on test_mask shape
            pred_2d = np.zeros((h, w))
            pred_2d[test_mask] = pred_flat.reshape(test_mask.sum())
            
            # Compute DTI
            truth_2d = np.zeros((h, w))
            truth_2d[test_mask] = test_labels.reshape(test_mask.sum())
            
            # Import DTI computation
            from scripts.dti_metric import compute_dti_fast
            dti_result = compute_dti_fast(pred_2d, truth_2d)
            fold_dtis.append(dti_result['dti'])
        
        mean_dti = np.mean(fold_dtis)
        result = {
            'run': run_idx,
            'config': {k: int(v) for k, v in run_config.items()},
            'active_families': active_family_names,
            'n_features': len(active_features),
            'mean_dti': float(mean_dti),
            'fold_dtis': [float(d) for d in fold_dtis],
        }
        results.append(result)
        print(f"Run {run_idx:2d} | {' '.join(f'{k}={v:+d}' for k,v in run_config.items())} | "
              f"DTI = {mean_dti:.4f} | families: {active_family_names}")
    
    # Save results
    with open(os.path.join(save_dir, 'factorial_results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    
    # Analyze effects
    effects = analyze_effects(results, design)
    with open(os.path.join(save_dir, 'factorial_effects.json'), 'w') as f:
        json.dump(effects, f, indent=2)
    
    return results, effects


def analyze_effects(results, design):
    """
    Estimate main effects and two-factor interactions from the fractional factorial.
    
    Main effect of factor A = (mean DTI when A=+1) - (mean DTI when A=-1)
    Interaction AB = (mean DTI when A and B have same sign) - (mean DTI when different signs)
    """
    factors = ['A', 'B', 'C', 'D', 'E']
    dtis = np.array([r['mean_dti'] for r in results])
    configs = np.array([[r['config'][f] for f in factors] for r in results])
    
    # Main effects
    main_effects = {}
    for i, f in enumerate(factors):
        high = dtis[configs[:, i] == 1]
        low = dtis[configs[:, i] == -1]
        effect = np.mean(high) - np.mean(low)
        main_effects[f] = {
            'factor': f,
            'family': FEATURE_FAMILIES[f]['name'],
            'effect': float(effect),
            'mean_high': float(np.mean(high)),
            'mean_low': float(np.mean(low)),
        }
    
    # Two-factor interactions
    interactions = {}
    for i, j in combinations(range(5), 2):
        f1, f2 = factors[i], factors[j]
        # Interaction = same sign - different sign
        same = dtis[configs[:, i] * configs[:, j] == 1]
        diff = dtis[configs[:, i] * configs[:, j] == -1]
        interaction = np.mean(same) - np.mean(diff)
        interactions[f"{f1}*{f2}"] = {
            'factors': f"{f1}*{f2}",
            'families': f"{FEATURE_FAMILIES[f1]['name']} × {FEATURE_FAMILIES[f2]['name']}",
            'interaction_effect': float(interaction),
        }
    
    # Rank by absolute effect
    ranked_main = sorted(main_effects.items(), key=lambda x: abs(x[1]['effect']), reverse=True)
    ranked_interactions = sorted(interactions.items(), key=lambda x: abs(x[1]['interaction_effect']), reverse=True)
    
    return {
        'main_effects': main_effects,
        'interactions': interactions,
        'ranked_main_effects': [(k, v) for k, v in ranked_main],
        'ranked_interactions': [(k, v) for k, v in ranked_interactions],
        'best_run': max(results, key=lambda r: r['mean_dti']),
    }


def print_effects_summary(effects):
    """Pretty-print the factorial analysis results."""
    print("\n" + "="*70)
    print("FACTORIAL EXPERIMENT RESULTS")
    print("="*70)
    
    print("\n--- MAIN EFFECTS (ranked by |effect|) ---")
    for name, info in effects['ranked_main_effects']:
        direction = "↑ helps" if info['effect'] > 0 else "↓ hurts"
        print(f"  {name} ({info['family']:30s}): {info['effect']:+.4f} {direction}")
        print(f"    Mean DTI when included: {info['mean_high']:.4f} | excluded: {info['mean_low']:.4f}")
    
    print("\n--- TWO-FACTOR INTERACTIONS (ranked by |effect|) ---")
    for name, info in effects['ranked_interactions']:
        direction = "synergistic" if info['interaction_effect'] > 0 else "antagonistic"
        print(f"  {name:8s} ({info['families']:60s}): {info['interaction_effect']:+.4f} ({direction})")
    
    best = effects['best_run']
    print(f"\n--- BEST CONFIGURATION ---")
    print(f"  Run {best['run']}: DTI = {best['mean_dti']:.4f}")
    print(f"  Active families: {', '.join(best['active_families'])}")
    print(f"  Features: {best['n_features']}")
    print("\n" + "="*70)


if __name__ == "__main__":
    # Print the design matrix
    design = generate_design_matrix()
    print(f"Design: 2^(5-1) Resolution V")
    print(f"Generator: {design['generator']}")
    print(f"Runs: {design['n_runs']}")
    print(f"Alias: {design['alias_structure']['defining_relation']}")
    print()
    
    print("Run  |  A  B  C  D  E  | Active families")
    print("-" * 60)
    for i, run in enumerate(design['runs']):
        active = [f for f, v in run.items() if v == 1]
        signs = ' '.join(f'{v:+d}' for v in run.values())
        names = ', '.join(FEATURE_FAMILIES[f]['name'] for f in active)
        print(f" {i:2d}  |  {signs}  | {names}")
    
    print(f"\nNote: This script requires competition data in data/")
    print(f"Run 'python scripts/prepare_data.py' first, then:")
    print(f"python scripts/factorial_design.py --run")
