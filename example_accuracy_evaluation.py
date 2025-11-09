#!/usr/bin/env python
"""
Example script showing how to use the fixed accuracy metric

This script demonstrates how to evaluate model predictions using the EvalEngine
with the corrected accuracy calculation.
"""

import pandas as pd
import sys

# Ensure histocc is in path
sys.path.insert(0, '/home/runner/work/OCCC-PST2/OCCC-PST2')

from histocc import OccCANINE, EvalEngine
from histocc.formatter import construct_general_purpose_formatter

def example_evaluation():
    """
    Example of evaluating predictions with the fixed accuracy metric
    """
    
    print("=" * 80)
    print("EXAMPLE: Evaluating PST/HISCO Predictions with Fixed Accuracy Metric")
    print("=" * 80)
    
    # Create a mock model for demonstration
    # In practice, you would load your actual finetuned model
    model = OccCANINE(skip_load=True, model_type='mix', system='pst')
    model.formatter = construct_general_purpose_formatter(
        block_size=5,
        target_cols=['pst_1', 'pst_2', 'pst_3'],
    )
    
    # Example ground truth data
    # This represents the true occupational codes
    ground_truth = pd.DataFrame({
        'pst_1': ['12345', '67890', '11111'],  # First code for each observation
        # Note: pst_2, pst_3 could be NaN if there's only one code per observation
    })
    
    # Example predictions
    # This represents what your model predicted (e.g., top-3 predictions)
    predictions = pd.DataFrame({
        'pst_1': ['12345', '67890', '99999'],  # First prediction
        'pst_2': ['54321', '11111', '88888'],  # Second prediction
        'pst_3': ['11111', '22222', '11111'],  # Third prediction
    })
    
    print("\nGround Truth:")
    print(ground_truth)
    print("\nPredictions:")
    print(predictions)
    
    # Create evaluation engine
    eval_engine = EvalEngine(
        model=model,
        ground_truth=ground_truth,
        predicitons=predictions,
        pred_col='pst_'
    )
    
    # Calculate metrics
    print("\n" + "=" * 80)
    print("EVALUATION METRICS")
    print("=" * 80)
    
    accuracy = eval_engine.accuracy()
    precision = eval_engine.precision()
    recall = eval_engine.recall()
    f1 = eval_engine.f1()
    
    print(f"\nOverall Metrics:")
    print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"  Precision: {precision:.4f} ({precision*100:.2f}%)")
    print(f"  Recall:    {recall:.4f} ({recall*100:.2f}%)")
    print(f"  F1 Score:  {f1:.4f} ({f1*100:.2f}%)")
    
    # Per-observation metrics
    print("\n" + "=" * 80)
    print("PER-OBSERVATION METRICS")
    print("=" * 80)
    
    accuracy_per_obs = eval_engine.accuracy(return_per_obs=True)
    precision_per_obs = eval_engine.precision(return_per_obs=True)
    recall_per_obs = eval_engine.recall(return_per_obs=True)
    f1_per_obs = eval_engine.f1(return_per_obs=True)
    
    results_df = pd.DataFrame({
        'observation': range(1, len(accuracy_per_obs) + 1),
        'accuracy': accuracy_per_obs,
        'precision': precision_per_obs,
        'recall': recall_per_obs,
        'f1': f1_per_obs,
    })
    
    print("\n", results_df)
    
    # Explanation for each observation
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80)
    
    for i in range(len(ground_truth)):
        print(f"\nObservation {i+1}:")
        truth_codes = [ground_truth.iloc[i][col] for col in ground_truth.columns 
                      if str(ground_truth.iloc[i][col]) != 'nan']
        pred_codes = [predictions.iloc[i][col] for col in predictions.columns 
                     if str(predictions.iloc[i][col]) != 'nan']
        
        print(f"  Ground Truth: {truth_codes}")
        print(f"  Predictions:  {pred_codes}")
        print(f"  Accuracy:     {accuracy_per_obs[i]:.4f}")
        print(f"  Precision:    {precision_per_obs[i]:.4f}")
        print(f"  Recall:       {recall_per_obs[i]:.4f}")
        
        # Explain the accuracy
        correct_preds = sum([p in truth_codes for p in pred_codes])
        print(f"  → {correct_preds} out of {len(pred_codes)} predictions are correct")
        print(f"  → Found {correct_preds} out of {len(truth_codes)} ground truth codes")
    
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print("""
The fixed accuracy metric now properly balances:
1. How many of your predictions are correct (precision-like)
2. How many of the ground truth codes you found (recall-like)

This gives a fairer assessment when your model provides multiple predictions
(e.g., top-5) but ground truth only has one code. The correct code being in
your predictions is now properly rewarded!
""")

if __name__ == '__main__':
    example_evaluation()
