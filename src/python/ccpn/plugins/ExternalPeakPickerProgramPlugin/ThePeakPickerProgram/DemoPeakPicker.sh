#!/usr/bin/env sh
set -e

# --- OPTION A: hardcode your Python here (leave empty to disable) ---
HARD_PY=""     # e.g. HARD_PY="/opt/miniconda/envs/nmr/bin/python"
# --- The Python script we want to run ---
PY_FILE="MyDemoPicker.py"

# --- OPTION B: search upward for bin/python up to MAX_UP levels ---
MAX_UP=6
# Optional: require these executables in the same bin/ (leave empty to skip)
REQUIRE_BINS="nef pytest pyeditor"

# ---- resolve script dir (works through symlinks) ----
PRG="$0"
while [ -h "$PRG" ]; do
  lsout=$(ls -ld "$PRG"); link=$(expr "$lsout" : '.*-> \(.*\)$')
  case "$link" in /*) PRG="$link" ;; *) PRG="$(dirname "$PRG")/$link" ;; esac
done
DIR="$(cd "$(dirname "$PRG")" && pwd -P)"

pick_python() {
  # A1: hardcoded path wins if executable
  if [ -n "$HARD_PY" ] && [ -x "$HARD_PY" ]; then
    echo "$HARD_PY"; return 0
  fi
  # B: walk up parents looking for bin/python (+ optional siblings)
  CUR="$DIR"
  i=0
  while [ "$i" -le "$MAX_UP" ] && [ "$CUR" != "/" ]; do
    CAND="$CUR/bin/python"
    if [ -x "$CAND" ]; then
      ok=1
      for b in $REQUIRE_BINS; do
        [ -x "$CUR/bin/$b" ] || ok=0
      done
      [ "$ok" -eq 1 ] && { echo "$CAND"; return 0; }
      [ -z "$REQUIRE_BINS" ] && { echo "$CAND"; return 0; }
    fi
    CUR=$(dirname "$CUR"); i=$((i+1))
  done
  # Fallback
  command -v python3 || true
}

PY="$(pick_python)"
[ -n "$PY" ] && [ -x "$PY" ] || { echo "No suitable Python found." >&2; exit 1; }

# Run the picker
exec "$PY" "$DIR/$PY_FILE" "$@"