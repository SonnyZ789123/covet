#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# CHECK ENV VARIABLES
# ============================================================
: "${PATHCOV_JAR:?PATHCOV_JAR not set}"
: "${CLASS_PATH:?CLASS_PATH not set}"
: "${FULLY_QUALIFIED_METHOD_SIGNATURE:?FULLY_QUALIFIED_METHOD_SIGNATURE not set}"
: "${BLOCK_MAP_PATH:?BLOCK_MAP_PATH not set}"

# TODO: We should just generate the block map of the "whole" project, not just 
# the CFG of one single target method.

generate_block_map() {
  echo "⚙️ Generating block map (PROD)"

  java -cp "$PATHCOV_JAR" \
    com.kuleuven.icfg.GenerateBlockMap \
    $CLASS_PATH \
    "$FULLY_QUALIFIED_METHOD_SIGNATURE" \
    "null" \
    $BLOCK_MAP_PATH \
    $PROJECT_PREFIXES
}

generate_block_map

echo "✅ Generating block map completed"