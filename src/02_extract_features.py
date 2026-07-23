import os
import sys
import csv
import z3

sys.setrecursionlimit(20000)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw", "non-incremental", "QF_UFLIA")
LABELS_CSV = os.path.join(REPO_ROOT, "data", "processed", "labels.csv")
OUT_CSV = os.path.join(REPO_ROOT, "data", "processed", "features.csv")

ARITH_OPS = {"+", "-", "*", "<=", "<", ">=", ">", "="}


def is_uf_application(expr):
    """True if expr is an application of a declared (>0 arity) uninterpreted function."""
    return (z3.is_app(expr)
            and expr.decl().kind() == z3.Z3_OP_UNINTERPRETED
            and expr.decl().arity() > 0)


def ast_stats(expr, depth=0, func_depth=0, cache=None):
    """
    Recursively walk expr, returning:
      node_count, max_depth, arith_op_count, func_app_count, max_func_nesting_depth
    Memoized by Z3 AST id (cache shared across a whole file) so repeated
    subterms are only walked once.
    """
    if cache is None:
        cache = {}
    key = expr.get_id()
    if key in cache:
        return cache[key]

    if not z3.is_app(expr):
        result = (1, depth, 0, 0, func_depth)
        cache[key] = result
        return result

    is_uf = is_uf_application(expr)
    this_func_depth = func_depth + 1 if is_uf else func_depth

    node_count = 1
    max_d = depth
    arith_count = 1 if expr.decl().name() in ARITH_OPS else 0
    func_app_count = 1 if is_uf else 0
    max_func_depth = this_func_depth

    for child in expr.children():
        c_nodes, c_depth, c_arith, c_func_apps, c_func_depth = ast_stats(
            child, depth + 1, this_func_depth, cache
        )
        node_count += c_nodes
        max_d = max(max_d, c_depth)
        arith_count += c_arith
        func_app_count += c_func_apps
        max_func_depth = max(max_func_depth, c_func_depth)

    result = (node_count, max_d, arith_count, func_app_count, max_func_depth)
    cache[key] = result
    return result


def extract(filepath_abs):
    try:
        formula = z3.parse_smt2_file(filepath_abs)
    except z3.Z3Exception:
        return None

    seen_vars = set()
    seen_funcs = set()
    decls_cache = set()

    def collect_decls(expr):
        key = expr.get_id()
        if key in decls_cache:
            return
        decls_cache.add(key)
        if z3.is_app(expr):
            decl = expr.decl()
            if decl.kind() == z3.Z3_OP_UNINTERPRETED:
                if decl.arity() == 0:
                    seen_vars.add(decl.name())
                else:
                    seen_funcs.add(decl.name())
            for child in expr.children():
                collect_decls(child)

    total_nodes = 0
    max_depth = 0
    arith_ops = 0
    func_applications = 0
    max_func_nesting = 0
    stats_cache = {}

    for f in formula:
        collect_decls(f)
        n, d, a, fa, fd = ast_stats(f, cache=stats_cache)
        total_nodes += n
        max_depth = max(max_depth, d)
        arith_ops += a
        func_applications += fa
        max_func_nesting = max(max_func_nesting, fd)

    return {
        "num_vars": len(seen_vars),
        "num_assertions": len(formula),
        "num_uninterpreted_funcs": len(seen_funcs),
        "num_func_applications": func_applications,
        "max_func_nesting_depth": max_func_nesting,
        "ast_node_count": total_nodes,
        "max_depth": max_depth,
        "num_arith_ops": arith_ops,
        "file_size_bytes": os.path.getsize(filepath_abs),
    }


def main():
    rows = []
    with open(LABELS_CSV, "r", newline="") as f:
        reader = list(csv.DictReader(f))

    for i, row in enumerate(reader):
        rel_path = row["filepath"]
        abs_path = os.path.join(RAW_DIR, rel_path)
        print(f"[{i+1}/{len(reader)}] {rel_path}", flush=True)

        try:
            feats = extract(abs_path)
        except RecursionError:
            print(f"  SKIPPED (recursion depth exceeded): {rel_path}", flush=True)
            continue

        if feats is None:
            print(f"  SKIPPED (parse error): {rel_path}", flush=True)
            continue

        feats["filepath"] = rel_path
        feats["result"] = row["result"]
        feats["solve_time_seconds"] = row["solve_time_seconds"]
        rows.append(feats)

    if not rows:
        print("No rows extracted -- check paths.")
        return

    fieldnames = ["filepath", "result", "solve_time_seconds",
                  "num_vars", "num_assertions", "num_uninterpreted_funcs",
                  "num_func_applications", "max_func_nesting_depth",
                  "ast_node_count", "max_depth", "num_arith_ops", "file_size_bytes"]

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Extracted features for {len(rows)} formulas -> {OUT_CSV}")


if __name__ == "__main__":
    main()