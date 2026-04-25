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