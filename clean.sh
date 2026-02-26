#!/usr/bin/env bash
# clean.sh - Remove temporary files, caches, and build artifacts
# Usage: ./clean.sh [--dry-run] [--force]
#   --dry-run  Show what would be removed without deleting
#   --force    Skip confirmation prompt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DRY_RUN=false
FORCE=false

for arg in "$@"; do
  case $arg in
    --dry-run)
      DRY_RUN=true
      ;;
    --force|-f)
      FORCE=true
      ;;
  esac
done

# Collect all paths to remove
PATHS=()

# Python virtual environments (use ./ for consistency with find output)
for d in .venv venv env ENV env.bak venv.bak; do
  [[ -d "$d" ]] && PATHS+=("./$d")
done

# Direct paths that may exist
for p in .npm .parcel-cache .eslintcache .stylelintcache .yarn-integrity \
         .node_repl_history htmlcov coverage .nyc_output site .ropeproject; do
  [[ -e "$p" ]] && PATHS+=("./$p")
done

# Find common cache/build directories recursively (avoid .git)
while IFS= read -r p; do
  PATHS+=("$p")
done < <(find . -type d \( \
  -name "__pycache__" -o \
  -name "node_modules" -o \
  -name ".venv" -o \
  -name "venv" -o \
  -name ".pytest_cache" -o \
  -name ".mypy_cache" -o \
  -name ".cache" -o \
  -name "build" -o \
  -name "dist" -o \
  -name ".next" -o \
  -name ".parcel-cache" -o \
  -name "htmlcov" -o \
  -name "coverage" -o \
  -name ".ipynb_checkpoints" -o \
  -name ".tox" -o \
  -name ".nox" -o \
  -name ".hypothesis" -o \
  -name ".pyre" -o \
  -name ".pytype" -o \
  -name "*.egg-info" -o \
  -name ".eggs" -o \
  -name ".rpt2_cache" -o \
  -name ".rts2_cache_cjs" -o \
  -name ".rts2_cache_es" -o \
  -name ".rts2_cache_umd" \
  \) -not -path "./.git/*" 2>/dev/null)

# Add supply-chain-ui specific paths
for p in supply-chain-ui/build supply-chain-ui/dist; do
  [[ -d "$p" ]] && PATHS+=("./$p")
done

# Deduplicate and filter: keep only top-level paths (avoid listing parent+children)
# Sort by path length so we process shorter paths first
SORTED=()
while IFS= read -r p; do
  [[ -n "$p" ]] && SORTED+=("$p")
done < <(printf '%s\n' "${PATHS[@]}" | sort -u | awk '{ print length, $0 }' | sort -n | cut -d' ' -f2-)

# Keep only paths that are not subpaths of another path in the list
FINAL=()
for p in "${SORTED[@]}"; do
  is_subpath=false
  for other in "${SORTED[@]}"; do
    [[ "$other" == "$p" ]] && continue
    if [[ "$p" == "$other"/* ]]; then
      is_subpath=true
      break
    fi
  done
  [[ "$is_subpath" == "false" ]] && FINAL+=("$p")
done

if [[ ${#FINAL[@]} -eq 0 ]]; then
  echo "Nothing to clean. Project is already tidy."
  exit 0
fi

echo "The following items will be removed:"
echo "-----------------------------------"
printf '%s\n' "${FINAL[@]}"
echo "-----------------------------------"
echo "Total: ${#FINAL[@]} item(s)"
echo

if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run complete. Run without --dry-run to actually remove."
  exit 0
fi

if [[ "$FORCE" != "true" ]]; then
  read -p "Proceed? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

REMOVED=0
for path in "${FINAL[@]}"; do
  if [[ -e "$path" ]]; then
    rm -rf "$path"
    echo "Removed: $path"
    ((REMOVED++)) || true
  fi
done

echo
echo "Cleanup complete. Removed $REMOVED item(s)."
