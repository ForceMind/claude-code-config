#!/usr/bin/env python3
"""Claude Code custom status line.

Reads the status-line JSON payload from stdin (see
https://code.claude.com/docs/en/statusline.md) and renders a single
plain-text line: branch, model, context %, tokens, cost, 5h/7d quota.
Uses only the stdlib so it works on any machine with python3
preinstalled, no extra deps to restore.
"""
import json
import os
import subprocess
import sys
import time

try:
    data = json.load(sys.stdin)
except Exception:
    print("statusline: bad payload")
    sys.exit(0)

RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"


def color_for_pct(pct):
    if pct is None:
        return ""
    if pct >= 90:
        return RED
    if pct >= 70:
        return YELLOW
    return GREEN


def fmt_tokens(n):
    if n is None:
        return "-"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}m"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def fmt_duration(seconds):
    if seconds is None:
        return "-"
    seconds = int(seconds)
    if seconds <= 0:
        return "now"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}d{hours}h"
    if hours > 0:
        return f"{hours}h{minutes}m"
    return f"{minutes}m"


def get(d, path, default=None):
    cur = d
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


# ---- branch ----
cwd = data.get("cwd") or get(data, "workspace.current_dir")
branch = None
if cwd and os.path.isdir(cwd):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True, timeout=1,
        )
        branch = out.stdout.strip() or None
    except Exception:
        branch = None

# ---- model ----
model = get(data, "model.display_name") or get(data, "model.id") or "?"

# ---- context window ----
ctx_pct = get(data, "context_window.used_percentage")
usage = get(data, "context_window.current_usage") or {}
token_total = None
if usage:
    token_total = sum(
        usage.get(k) or 0
        for k in (
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
        )
    )
elif get(data, "context_window.total_input_tokens") is not None:
    token_total = (get(data, "context_window.total_input_tokens") or 0) + (
        get(data, "context_window.total_output_tokens") or 0
    )

# ---- cost (client-side estimate, resets on /clear) ----
cost = get(data, "cost.total_cost_usd")

# ---- rate limits: only present for Claude.ai Pro/Max login sessions ----
five_h_pct = get(data, "rate_limits.five_hour.used_percentage")
five_h_reset = get(data, "rate_limits.five_hour.resets_at")
seven_d_pct = get(data, "rate_limits.seven_day.used_percentage")
seven_d_reset = get(data, "rate_limits.seven_day.resets_at")

now = time.time()

# ---- single line: branch | model | context | tokens | cost | 5h | 7d ----
parts = []
if branch:
    parts.append(branch)
parts.append(model)
if ctx_pct is not None:
    c = color_for_pct(ctx_pct)
    parts.append(f"ctx {c}{ctx_pct:.0f}%{RESET}")
if token_total is not None:
    parts.append(f"tok {fmt_tokens(token_total)}")
if cost is not None:
    parts.append(f"cost ${cost:.2f}{DIM}(est){RESET}")
if five_h_pct is not None:
    c = color_for_pct(five_h_pct)
    remain = fmt_duration(five_h_reset - now) if five_h_reset else "-"
    parts.append(f"5h {c}{five_h_pct:.0f}%{RESET} reset {remain}")
if seven_d_pct is not None:
    c = color_for_pct(seven_d_pct)
    remain = fmt_duration(seven_d_reset - now) if seven_d_reset else "-"
    parts.append(f"7d {c}{seven_d_pct:.0f}%{RESET} reset {remain}")

print(" | ".join(parts))
