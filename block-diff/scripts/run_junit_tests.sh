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
: "${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR not set}"
: "${TEST_CLASS_PATH:?TEST_CLASS_PATH not set}"
: "${BLOCK_DIFF_OUTPUT_PATH:?BLOCK_DIFF_OUTPUT_PATH not set}"

INCLUDE_TAGS="$(python3 generate_include_tags.py "${BLOCK_DIFF_OUTPUT_PATH}")"

# If no tags, there are no added/removed blocks -> skip tests
if [[ -z "${INCLUDE_TAGS// }" ]]; then
  echo "ℹ️ No added/removed blocks found. Skipping test execution."
  exit 0
fi

echo "⚙️ Running test suite with tags: $INCLUDE_TAGS"

# Split INCLUDE_TAGS into words (expects: --include-tag tag1 --include-tag tag2 ...)
read -r -a TAG_ARGS <<< "$INCLUDE_TAGS"

java \
  -cp "$JUNIT_CONSOLE_JAR:$TEST_CLASS_PATH" \
  org.junit.platform.console.ConsoleLauncher \
  --scan-classpath \
  "${TAG_ARGS[@]}"

echo "✅ Running test suite completed"
