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

# ------------------------------------------------------------
# Args
# ------------------------------------------------------------

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <coverage_report_path> <cg_classes_output_path> <output_config_args_path>" >&2
  exit 1
fi

INTELLIJ_COVERAGE_REPORT_PATH="$1"
CG_CLASSES_OUTPUT_PATH="$2"
INTELLIJ_COVERAGE_AGENT_CONFIG_PATH="$3"

# ------------------------------------------------------------
# Ensure output directory exists
# ------------------------------------------------------------

mkdir -p "$(dirname "$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH")"

# ------------------------------------------------------------
# Generate config.args
# ------------------------------------------------------------

cat > "$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH" <<EOF
${INTELLIJ_COVERAGE_REPORT_PATH}
false
false
false
false
$(cat "$CG_CLASSES_OUTPUT_PATH")
-exclude
EOF

echo "[OK] Generated IntelliJ coverage agent args:"
echo "  $INTELLIJ_COVERAGE_AGENT_CONFIG_PATH"
