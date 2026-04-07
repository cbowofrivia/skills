#!/usr/bin/env python3
"""Analyze a Clockwork request JSON file for N+1 queries and performance issues.

Usage:
    python3 analyze.py <path-to-clockwork-json>
    python3 analyze.py --trace <path-to-clockwork-json>

Options:
    --trace   Show full non-vendor stack trace for each N+1 and slow query
"""

import json
import os
import re
import sys
from collections import Counter


def normalize_query(sql: str) -> str:
    """Normalize a SQL query by replacing literal values with placeholders."""
    normalized = re.sub(r"= \d+", "= ?", sql)
    normalized = re.sub(r"= '[^']*'", "= '?'", normalized)
    normalized = re.sub(r"in \([^)]+\)", "in (?)", normalized)
    return normalized


def app_frames(trace: list[dict]) -> list[dict]:
    """Return all non-vendor trace frames."""
    return [f for f in trace if not f.get("isVendor", True)]


def first_app_frame(trace: list[dict]) -> str:
    """Return the first non-vendor trace frame as file:line."""
    frames = app_frames(trace)
    return f"{frames[0]['file']}:{frames[0]['line']}" if frames else "unknown"


def format_trace(trace: list[dict], project_root: str) -> str:
    """Format non-vendor trace frames as a readable stack trace."""
    frames = app_frames(trace)
    if not frames:
        return "         (no app frames)"
    lines = []
    for f in frames:
        path = f["file"].replace(project_root + "/", "")
        lines.append(f"         {path}:{f['line']}  {f.get('call', '')}")
    return "\n".join(lines)


def print_summary(data: dict) -> None:
    print("=== Request Summary ===")
    print(f"URL: {data['method']} {data['uri']}")
    print(f"Controller: {data['controller']}")
    print(f"Status: {data['responseStatus']}")
    print(f"Response time: {data['responseDuration']:.1f}ms")
    print(f"DB time: {data['databaseDuration']:.1f}ms")
    print(f"DB as % of response: {data['databaseDuration'] / max(data['responseDuration'], 0.1) * 100:.0f}%")
    print(f"Memory: {data['memoryUsage'] / 1024 / 1024:.1f}MB")
    print(f"Total queries: {data['databaseQueriesCount']}")
    print(f"Slow queries: {data['databaseSlowQueries']}")
    print()


def print_models(data: dict) -> None:
    retrieved = data.get("modelsRetrieved", {})
    if not retrieved:
        return
    total = sum(retrieved.values())
    print(f"=== Models Retrieved ({total} total) ===")
    for model, count in sorted(retrieved.items(), key=lambda x: -x[1]):
        print(f"  {model}: {count}")
    print()


def print_n_plus_one(queries: list[dict], show_trace: bool, project_root: str) -> None:
    patterns = []
    for q in queries:
        patterns.append((normalize_query(q["query"]), q))

    counts = Counter(p[0] for p in patterns)
    candidates = [(p, c) for p, c in counts.most_common(20) if c > 1]

    if not candidates:
        print("=== N+1 Query Candidates ===")
        print("  None detected.")
        print()
        return

    print("=== N+1 Query Candidates (repeated patterns) ===")
    for pattern, count in candidates:
        sample = next(q for norm, q in patterns if norm == pattern)
        origin = first_app_frame(sample.get("trace", []))
        total_est = sample["duration"] * count
        print(f"  [{count}x] {pattern[:150]}")
        print(f"         Model: {sample.get('model', '?')}  |  Origin: {origin}")
        print(f"         Avg duration: {sample['duration']:.2f}ms  |  Total est: {total_est:.1f}ms")
        if show_trace:
            print(f"         --- Stack trace ---")
            print(format_trace(sample.get("trace", []), project_root))
        print()


def print_slow_queries(queries: list[dict], show_trace: bool, project_root: str, top_n: int = 10) -> None:
    sorted_queries = sorted(queries, key=lambda q: -q["duration"])
    print(f"=== Slowest Individual Queries (top {top_n}) ===")
    for q in sorted_queries[:top_n]:
        origin = first_app_frame(q.get("trace", []))
        print(f"  [{q['duration']:.2f}ms] {q['query'][:150]}")
        print(f"         Origin: {origin}")
        if show_trace:
            print(f"         --- Stack trace ---")
            print(format_trace(q.get("trace", []), project_root))
        print()


def print_cache(data: dict) -> None:
    cache = data.get("cacheQueries", [])
    if not cache:
        return
    by_type = Counter(c["type"] for c in cache)
    summary = ", ".join(f"{count} {t}{'s' if count != 1 else ''}" for t, count in by_type.items())
    print(f"=== Cache: {summary} ===")
    for c in cache:
        print(f"  [{c['type']}] {c['key']}")
    print()


def main() -> None:
    show_trace = "--trace" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--trace"]

    if len(args) != 1:
        print(f"Usage: {sys.argv[0]} [--trace] <clockwork-json-file>", file=sys.stderr)
        sys.exit(1)

    filepath = args[0]
    if not os.path.isfile(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath) as f:
        data = json.load(f)

    # Derive project root from trace paths (first non-vendor frame in any query)
    project_root = ""
    for q in data.get("databaseQueries", []):
        for frame in q.get("trace", []):
            if not frame.get("isVendor", True) and "/app/" in frame.get("file", ""):
                project_root = frame["file"].split("/app/")[0]
                break
        if project_root:
            break

    queries = data.get("databaseQueries", [])

    print_summary(data)
    print_models(data)
    print_n_plus_one(queries, show_trace, project_root)
    print_slow_queries(queries, show_trace, project_root)
    print_cache(data)


if __name__ == "__main__":
    main()
