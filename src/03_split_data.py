import os
import csv
import random
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATURES_CSV = os.path.join(REPO_ROOT, "data", "processed", "features.csv")
TRAIN_CSV = os.path.join(REPO_ROOT, "data", "processed", "train.csv")
VAL_CSV = os.path.join(REPO_ROOT, "data", "processed", "val.csv")
TEST_CSV = os.path.join(REPO_ROOT, "data", "processed", "test.csv")

SEED = 42
TRAIN_FRAC = 0.8
VAL_FRAC = 0.1
# remaining ~0.1 goes to test

def main():
    with open(FEATURES_CSV, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Group rows by their result label (sat/unsat/unknown/timeout) for stratification
    by_label = defaultdict(list)
    for row in rows:
        by_label[row["result"]].append(row)

    random.seed(SEED)
    train_rows, val_rows, test_rows = [], [], []

    for label, group in by_label.items():
        random.shuffle(group)
        n = len(group)
        n_train = int(n * TRAIN_FRAC)
        n_val = int(n * VAL_FRAC)
        # whatever's left after train+val goes to test, avoids rounding gaps
        train_rows.extend(group[:n_train])
        val_rows.extend(group[n_train:n_train + n_val])
        test_rows.extend(group[n_train + n_val:])
        print(f"  {label}: {n} total -> {n_train} train / {n_val} val / {n - n_train - n_val} test")

    # Shuffle each split once more so rows aren't grouped by label within the file
    random.shuffle(train_rows)
    random.shuffle(val_rows)
    random.shuffle(test_rows)

    def write_csv(path, data):
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    write_csv(TRAIN_CSV, train_rows)
    write_csv(VAL_CSV, val_rows)
    write_csv(TEST_CSV, test_rows)

    print(f"\nTotal: {len(rows)} -> {len(train_rows)} train / {len(val_rows)} val / {len(test_rows)} test")
    print(f"Written to:\n  {TRAIN_CSV}\n  {VAL_CSV}\n  {TEST_CSV}")

if __name__ == "__main__":
    main()