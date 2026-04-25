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
# LOAD CONFIGURABLE SUT CONFIG
# ============================================================

readonly SUT_CONFIG_FILE="${1:-$CONFIGS_DIR/sut.config}"

[[ -f "$SUT_CONFIG_FILE" ]] || {
  echo "[ERROR] SUT config not found: $SUT_CONFIG_FILE" >&2
  exit 1
}

# shellcheck source=/dev/null
source "$SUT_CONFIG_FILE"

: "${COMPILED_ROOT:?COMPILED_ROOT not set}"
: "${COMPILED_TEST_ROOT:?COMPILED_TEST_ROOT not set}"
: "${SOURCE_PATH:?SOURCE_PATH not set}"
: "${CLASS_PATH:?CLASS_PATH not set}"
: "${TEST_CLASS_PATH:?TEST_CLASS_PATH not set}"
: "${TARGET_CLASS:?TARGET_CLASS not set}"
: "${FULLY_QUALIFIED_METHOD_SIGNATURE:?FULLY_QUALIFIED_METHOD_SIGNATURE not set}"

# ============================================================
# FIXED CONFIG
# ============================================================
# Shared data volume with the covet-engine container
readonly DATA_DIR="${2:-$DATA_DIR}"

# Tools inside image
readonly AGENT_JAR="${INTELLIJ_COVERAGE_AGENT_JAR:?INTELLIJ_COVERAGE_AGENT_JAR is not set}"  # This variable is injected at container runtime via ENV

readonly JUNIT_CONSOLE_JAR="${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR is not set}"  # This variable is injected at container runtime via ENV
readonly JUNIT_OPTIONS="${JUNIT_OPTIONS:-"--scan-classpath"}"  # This variable is injected at container runtime via ENV

# Outputs
readonly CG_CLASSES_OUTPUT_PATH="$DATA_DIR/intellij-coverage/cg_classes.txt"

readonly BLOCK_MAP_PATH="$DATA_DIR/blockmaps/icfg_block_map.json"

readonly INTELLIJ_COVERAGE_AGENT_CONFIG_PATH="$DATA_DIR/intellij-coverage/intellij_coverage_agent.args"
readonly INTELLIJ_COVERAGE_REPORT_PATH="$DATA_DIR/intellij-coverage/intellij_coverage_report.ic"

readonly EXPORTER_CONFIG_PATH="$DATA_DIR/intellij-coverage/intellij_coverage_exporter_config.json"
readonly COVERAGE_EXPORT_OUTPUT_PATH="$DATA_DIR/coverage/coverage_data.json"

readonly VISUALIZATION_DIR="$OUTPUT_DIR/visualization/icfg/coverage"

readonly DOT_FILE_NAME="coverage_graph.dot"
readonly SVG_FILE_NAME="coverage_graph.svg"

# ============================================================
# LOGGING
# ============================================================
log() {
  echo "[INFO] $*"
}

warn() {
  echo "[WARN] $*" >&2
}

# ============================================================
# COMMON STEPS
# ============================================================
run_junit_with_agent() {
  log "⚙️ Running test suite with coverage agent"

  "$SCRIPTS_DIR/common/make_coverage_agent_args.sh" \
    "$INTELLIJ_COVERAGE_REPORT_PATH" \
    "$CG_CLASSES_OUTPUT_PATH" \
    "$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH"

  set +e

java \
  -javaagent:"$AGENT_JAR=$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH" \
  -cp "$JUNIT_CONSOLE_JAR:$TEST_CLASS_PATH" \
  org.junit.platform.console.ConsoleLauncher \
  $JUNIT_OPTIONS \
  > /dev/null 2>&1

  local exit_code=$?
  set -e

  if [[ $exit_code -ne 0 ]]; then
    warn "========================================================="
    warn "    ⚠️ Some JUnit tests FAILED, continuing anyway ⚠️"
    warn "========================================================="
  fi

  log "✅ Running test suite completed"
}

generate_svg() {
  log "⚙️ Generating SVG visualization"

  if ! timeout 10s dot -Tsvg \
      "$VISUALIZATION_DIR/$DOT_FILE_NAME" \
      -o "$VISUALIZATION_DIR/$SVG_FILE_NAME" \
      > /dev/null 2>&1; then

    if [[ $? -eq 124 ]]; then
      warn "⚠️ SVG generation timed out, dot file may be too large or complex to visualize"
    else
      warn "❌ SVG generation failed"
    fi
  fi
}

# ============================================================
# MAIN
# ============================================================
main_common() {
  write_cg_classes
  run_junit_with_agent
  generate_coverage_data
  generate_block_map
  generate_coverage_graph
  calculate_branch_coverage
  generate_svg
  log "✅ Pipeline completed successfully"
}
