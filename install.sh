#!/usr/bin/env bash
# Restore this Claude Code global config onto a (new) machine.
#   git clone https://github.com/ForceMind/claude-code-config.git
#   cd claude-code-config && ./install.sh
#
# Existing files under ~/.claude are backed up (never silently overwritten).
# settings.json is merged (top-level keys only) so other settings you've
# added on this machine (e.g. permissions) are preserved.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
STAMP="$(date +%Y%m%d%H%M%S)"

mkdir -p "$CLAUDE_DIR"

backup_and_copy() {
  local src="$1" dest="$2"
  if [ -f "$dest" ] && ! cmp -s "$src" "$dest"; then
    cp "$dest" "$dest.bak.$STAMP"
    echo "已备份: $dest -> $dest.bak.$STAMP"
  fi
  cp "$src" "$dest"
  echo "已安装: $dest"
}

backup_and_copy "$REPO_DIR/CLAUDE.global.md" "$CLAUDE_DIR/CLAUDE.md"
backup_and_copy "$REPO_DIR/statusline.py" "$CLAUDE_DIR/statusline.py"
chmod +x "$CLAUDE_DIR/statusline.py"

# settings.json: shallow-merge repo keys into existing file instead of
# overwriting, so unrelated settings (permissions, etc.) already on this
# machine survive.
python3 - "$REPO_DIR/settings.json" "$CLAUDE_DIR/settings.json" "$STAMP" <<'PYEOF'
import json, sys, os, shutil

repo_path, dest_path, stamp = sys.argv[1], sys.argv[2], sys.argv[3]

with open(repo_path) as f:
    repo_settings = json.load(f)

existing = {}
if os.path.exists(dest_path):
    with open(dest_path) as f:
        try:
            existing = json.load(f)
        except Exception:
            existing = {}
    backup_path = f"{dest_path}.bak.{stamp}"
    shutil.copy(dest_path, backup_path)
    print(f"已备份: {dest_path} -> {backup_path}")

merged = {**existing, **repo_settings}
with open(dest_path, "w") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"已合并写入: {dest_path}")
PYEOF

echo
echo "完成。新开一个 Claude Code 会话即可看到状态栏生效。"
