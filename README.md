# SMT Feature Classifier

This project predicts whether Z3 will report sat, unsat, or unknown on QF_UFLIA SMT-LIB formulas, based on structural features of the formula rather than running the solver.

Data: 659 QF_UFLIA benchmarks from the SMT-LIB library (Zenodo release 2025), labeled by actually running Z3 with a timeout and recording the result and solve time.

Features extracted per formula: number of variables, number of assertions, number of uninterpreted functions, number of function applications, max function nesting depth, AST node count, max AST depth, number of arithmetic operators, and file size in bytes.

Data was split 80/10/10 into train/val/test, stratified by result label.

A decision tree was chosen as the first model for interpretability. A depth sweep on a single validation split initially suggested depth 5 was optimal, but 5-fold cross-validation on the combined train+val data showed deeper trees (depth 8, unlimited) generalized better on average. On the actual held-out test set, depth 5 and unlimited depth tied at 85.5% accuracy, with depth 5 doing slightly better on the minority "unknown" class. Depth 5 was kept as the final model for its interpretability and equal test performance.

Baseline (always predict the majority class, "sat") is 64.1% accuracy. The final depth-5 tree reaches 85.5% on the test set.

Error analysis showed misclassified formulas tend to be smaller across every size-related feature (file size, AST node count, max depth, arithmetic op count) than correctly classified ones, while non-size features (variable count, assertion count, function nesting depth) were unchanged. This suggests the model relies heavily on formula size as a proxy for difficulty, and struggles more on small-to-mid-sized formulas where size alone is less discriminating.
