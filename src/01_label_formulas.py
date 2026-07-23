import os
import time
import csv
import z3

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw", "non-incremental", "QF_UFLIA")
OUT_CSV = os.path.join(REPO_ROOT, "data", "processed", "labels.csv")
TIMEOUT_MS = 10000  # 10 seconds per formula

def find_smt2_files(root):
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(".smt2"):
                yield os.path.join(dirpath, fname)

def label_file(filepath):
    solver = z3.Solver()
    solver.set("timeout", TIMEOUT_MS)
    try:
        formula = z3.parse_smt2_file(filepath)
        solver.add(formula)
    except z3.Z3Exception as e:
        return "parse_error", 0.0

    start = time.time()
    result = solver.check()
    elapsed = time.time() - start

    result_str = str(result)  # "sat", "unsat", or "unknown"
    return result_str, elapsed

def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    files = list(find_smt2_files(RAW_DIR))
    print(f"Found {len(files)} .smt2 files")

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filepath", "result", "solve_time_seconds"])
        for i, path in enumerate(files):
            result, elapsed = label_file(path)
            rel_path = os.path.relpath(path, RAW_DIR).replace("\\", "/")
            writer.writerow([rel_path, result, f"{elapsed:.4f}"])
            if (i + 1) % 50 == 0:
                print(f"Labeled {i+1}/{len(files)}")

    print(f"Done. Labels written to {OUT_CSV}")

if __name__ == "__main__":
    main()