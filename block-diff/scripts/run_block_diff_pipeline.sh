#!/usr/bin/env bash
# Copyright (c) 2025-2026 Yoran Mertens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

set -Eeuo pipefail

###############################################################################
# Arguments
#
# $1 = CURRENT_COMMIT
# $2 = PREVIOUS_COMMIT
# $3 = METHOD_SIGNATURE
# $4 = PROJECT_PREFIXES
# $5 = SUT_HOST_PATH        (path on host to mount as /sut)
# $6 = SUT_CONTAINER_PATH   (path inside container, default: /sut)
###############################################################################

CURRENT_COMMIT="${1:-$(git rev-parse HEAD)}"
PREVIOUS_COMMIT="${2:-$(git rev-parse HEAD^)}"
METHOD_SIGNATURE="${3:-<com.kuleuven.diff.BlockDiffExample: int foo(int)>}"
PROJECT_PREFIXES="${4:-com.kuleuven.diff}"
SUT_HOST_PATH="${5:-$(pwd)}"
SUT_CONTAINER_PATH="${6:-/sut}"

###############################################################################
# Config (can be overridden via environment variables)
###############################################################################

DOCKER_IMAGE="${DOCKER_IMAGE:-sonnyz789123/block-diff-image:latest}"
SHARED_DIR="${SHARED_DIR:-shared}"

echo "▶ CURRENT_COMMIT:       $CURRENT_COMMIT"
echo "▶ PREVIOUS_COMMIT:      $PREVIOUS_COMMIT"
echo "▶ SUT_HOST_PATH:        $SUT_HOST_PATH"
echo "▶ SUT_CONTAINER_PATH:   $SUT_CONTAINER_PATH"

mkdir -p "$SHARED_DIR"

echo "🧹 Clearing shared directory: $SHARED_DIR"

# Safety check: prevent accidental rm -rf /
if [[ -z "$SHARED_DIR" || "$SHARED_DIR" == "/" ]]; then
  echo "❌ Refusing to clear unsafe SHARED_DIR value"
  exit 1
fi

rm -rf "${SHARED_DIR:?}/"*

###############################################################################
# Capture original state so we can restore it
###############################################################################

ORIGINAL_COMMIT="$(git -C "$SUT_HOST_PATH" rev-parse HEAD)"
ORIGINAL_BRANCH="$(git -C "$SUT_HOST_PATH" branch --show-current || true)"

echo "▶ ORIGINAL_COMMIT:      $ORIGINAL_COMMIT"
echo "▶ ORIGINAL_BRANCH:      ${ORIGINAL_BRANCH:-DETACHED}"

restore_original_state() {
  echo "🔄 Restoring original git state..."

  if [[ -n "${ORIGINAL_BRANCH:-}" ]]; then
    git -C "$SUT_HOST_PATH" checkout "$ORIGINAL_BRANCH" >/dev/null 2>&1 || true
  else
    git -C "$SUT_HOST_PATH" checkout "$ORIGINAL_COMMIT" >/dev/null 2>&1 || true
  fi

  echo "✅ Restored to original state."
}

trap restore_original_state EXIT

###############################################################################
# Function: Build project
###############################################################################
build_project() {
  echo "🔨 Building project..."
  (cd "$SUT_HOST_PATH" && mvn -q -DskipTests package)
}

###############################################################################
# Function: Generate blockmap
###############################################################################
generate_blockmap() {
  local OUTPUT_FILE="$1"

  echo "⚙️ Generating blockmap -> $OUTPUT_FILE"

  docker run --rm \
    -v "$SUT_HOST_PATH":"$SUT_CONTAINER_PATH" \
    -v "$(pwd)/$SHARED_DIR":/shared \
    -e CLASS_PATH="$SUT_CONTAINER_PATH/target/classes" \
    -e FULLY_QUALIFIED_METHOD_SIGNATURE="$METHOD_SIGNATURE" \
    -e PROJECT_PREFIXES="$PROJECT_PREFIXES" \
    -e BLOCK_MAP_PATH="/shared/$OUTPUT_FILE" \
    "$DOCKER_IMAGE" \
    bash -c "/block-diff/scripts/generate_block_map.sh"
}

###############################################################################
# Function: Generate diff
###############################################################################
generate_diff() {
  echo "⚙️ Generating block diff"

  docker run --rm \
    -v "$(pwd)/$SHARED_DIR":/shared \
    -e PREVIOUS_BLOCK_MAP_PATH=/shared/blockmap_old.json \
    -e MODIFIED_BLOCK_MAP_PATH=/shared/blockmap_new.json \
    -e BLOCK_DIFF_OUTPUT_PATH=/shared/block_diff.json \
    "$DOCKER_IMAGE" \
    bash -c "/block-diff/scripts/generate_block_diff.sh"
}

###############################################################################
# Function: Run selective tests
###############################################################################
run_tests() {
  echo "🧪 Running selective JUnit tests"

  docker run --rm \
    -v "$SUT_HOST_PATH":"$SUT_CONTAINER_PATH" \
    -v "$(pwd)/$SHARED_DIR":/shared \
    -e TEST_CLASS_PATH="$SUT_CONTAINER_PATH/target/classes:$SUT_CONTAINER_PATH/target/test-classes" \
    -e BLOCK_DIFF_OUTPUT_PATH=/shared/block_diff.json \
    "$DOCKER_IMAGE" \
    bash -c "/block-diff/scripts/run_junit_tests.sh"
}

###############################################################################
# PIPELINE EXECUTION
###############################################################################

echo "=============================="
echo " STEP 1 — NEW COMMIT"
echo "=============================="

git -C "$SUT_HOST_PATH" checkout "$CURRENT_COMMIT"
build_project
generate_blockmap "blockmap_new.json"

echo "=============================="
echo " STEP 2 — OLD COMMIT"
echo "=============================="

git -C "$SUT_HOST_PATH" checkout "$PREVIOUS_COMMIT"
build_project
generate_blockmap "blockmap_old.json"

echo "=============================="
echo " STEP 3 — RESTORE NEW COMMIT"
echo "=============================="

git -C "$SUT_HOST_PATH" checkout "$CURRENT_COMMIT"
build_project

echo "=============================="
echo " STEP 4 — DIFF"
echo "=============================="

generate_diff

echo "=============================="
echo " STEP 5 — SELECTIVE TESTING"
echo "=============================="

run_tests

echo "✅ Differential pipeline completed successfully."

### Example usage:
# ./scripts/run_block_diff_pipeline.sh HEAD HEAD~1 \
#   "<com.kuleuven.diff.BlockDiffExample: int foo(int)>" \
#   "com.kuleuven.diff" \
#   /Users/yoran/dev/master-thesis/suts/test-block-diff \
#   /sut
###