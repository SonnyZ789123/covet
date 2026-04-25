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