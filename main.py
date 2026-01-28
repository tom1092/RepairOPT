#!/usr/bin/env python3
"""
Main script for the Repair Optimization MIP Model.

This script:
1. Loads and preprocesses repair data from CSV files
2. Builds DOM objects and data structures
3. Instantiates the MIP model with the preprocessed data
4. Optimizes the MIP model
5. Generates scheduling CSV and visualizations
"""

import sys
import os
from utils.preproc import parse_repair_data
from mip_model import RepairMIP
from generate_results import generate_scheduling_csv, create_gif_animation
from create_interactive_dashboard import create_interactive_dashboard


def main():
    """
    Main function to load data and instantiate the MIP model.
    """
    print("=" * 60)
    print("REPAIR OPTIMIZATION - MIP MODEL SETUP")
    print("=" * 60)
    print()
    
    # Step 1: Load and preprocess data
    print("Step 1: Loading and preprocessing data...")
    print("-" * 60)
    
    preprocessor, model_params = parse_repair_data(data_dir="data")
    
    print()
    print("-------Data loaded-------")
    print(f"  - Products: {len(model_params['P'])}")
    print(f"  - Defects: {len(model_params['D'])}")
    print(f"  - Repairers: {len(model_params['R'])}")
    print(f"  - Time periods: {len(model_params['T'])}")
    print()
    
    # Step 2: Display some statistics
    print("Step 2: Data statistics...")
    print("-" * 60)
    
    # Count defects per product
    defects_per_product = {p: len(d_set) for p, d_set in model_params['D_p'].items()}
    avg_defects = sum(defects_per_product.values()) / len(defects_per_product) if defects_per_product else 0
    
    print(f"  - Average defects per product: {avg_defects:.2f}")
    print(f"  - Products with defects: {sum(1 for d in defects_per_product.values() if d > 0)}")
    print(f"  - Max defects on single product: {max(defects_per_product.values()) if defects_per_product else 0}")
    print()
    
    # Step 3: Instantiate MIP model
    print("Step 3: Instantiating MIP model...")
    print("-" * 60)
    
    mip_model = RepairMIP(
        R=model_params['R'],
        D=model_params['D'],
        P=model_params['P'],
        T=model_params['T'],
        D_p=model_params['D_p'],
        chi_r_s=model_params['chi_r_s'],
        tau=model_params['tau'],
        tau_p=model_params['tau_p'],
        beta_r=model_params['beta_r'],
        lambda_r=model_params['lambda_r'],
        sigma_dpr=model_params['sigma_dpr'],
        chi_dpr_r=model_params['chi_dpr_r'],
        pi_r=model_params['pi_r'],
        alpha1=model_params['alpha1'],
        alpha2=model_params['alpha2'],
        alpha3=model_params['alpha3'],
        alpha4=model_params['alpha4'],
        alpha5=model_params['alpha5']
    )
    
    print("MIP model instantiated")
    print()
    print("Model parameters:")
    print(f"  - Objective weights:")
    print(f"    * alpha1 (lead time): {model_params['alpha1']}")
    print(f"    * alpha2 (shipping cost): {model_params['alpha2']}")
    print(f"    * alpha3 (quality degradation): {model_params['alpha3']}")
    print(f"    * alpha4 (repair cost): {model_params['alpha4']}")
    print(f"    * alpha5 (carbon emissions): {model_params['alpha5']}")
    print(f"  - Maximum lead time (tau): {model_params['tau']}")
    print(f"  - Batch capacity per repairer: {model_params['beta_r'][0] if model_params['R'] else 'N/A'}")
    print()
    
    # Step 4: Optimize the model
    print("=" * 60)
    print("OPTIMIZING MODEL")
    print("=" * 60)
    print()
    print("Running Gurobi optimization...")
    print("This may take a few moments...")
    print()
    
    solution = mip_model.optimize()
    
    print()
    print("=" * 60)
    print("OPTIMIZATION COMPLETE")
    print("=" * 60)
    print()
    print(f"Solution found with {len(solution)} variables")
    print()
    generate_scheduling_csv(mip_model, preprocessor)
    #create_gif_animation(mip_model, preprocessor, duration_seconds=10)
    create_interactive_dashboard(mip_model, preprocessor)
    
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print("\nFiles created:")
    print("  - scheduling_results.csv")
    print("  - scheduling_dashboard.html")
    print()
    
    return mip_model, preprocessor, model_params


if __name__ == "__main__":
    model, preprocessor, params = main()
