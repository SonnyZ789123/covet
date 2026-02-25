#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# CHECK ENV VARIABLES
# ============================================================
: "${PATHCOV_JAR:?PATHCOV_JAR not set}"
: "${PREVIOUS_BLOCK_MAP_PATH:?PREVIOUS_BLOCK_MAP_PATH not set}"
: "${MODIFIED_BLOCK_MAP_PATH:?MODIFIED_BLOCK_MAP_PATH not set}"
: "${BLOCK_DIFF_OUTPUT_PATH:?BLOCK_DIFF_OUTPUT_PATH not set}"

generate_block_diff() {
  echo "⚙️ Generating block diff (PROD)"

  java -cp "$PATHCOV_JAR" \
    com.kuleuven.blockmap.diff.GenerateBlockHashTreeDiff \
    $PREVIOUS_BLOCK_MAP_PATH \
    $MODIFIED_BLOCK_MAP_PATH \
    $BLOCK_DIFF_OUTPUT_PATH 
}

generate_block_diff

echo "✅ Generating block diff completed"