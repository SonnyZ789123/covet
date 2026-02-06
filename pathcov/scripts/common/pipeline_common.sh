#!/usr/bin/env bash
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
# Shared data volume with the JDart container
readonly DATA_DIR="${2:-$DATA_DIR}"

# Tools inside image
readonly AGENT_JAR="${INTELLIJ_COVERAGE_AGENT_JAR:?INTELLIJ_COVERAGE_AGENT_JAR is not set}"  # This variable is injected at container runtime via ENV

readonly JUNIT_CONSOLE_JAR="${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR is not set}"  # This variable is injected at container runtime via ENV
readonly JUNIT_OPTIONS="${JUNIT_OPTIONS:-"--scan-classpath"}"  # This variable is injected at container runtime via ENV

# Outputs
readonly BLOCK_MAP_PATH="$DATA_DIR/blockmaps/icfg_block_map.json"

readonly INTELLIJ_COVERAGE_AGENT_CONFIG_PATH="$DATA_DIR/intellij-coverage/intellij_coverage_agent.args"
readonly INTELLIJ_COVERAGE_REPORT_PATH="$DATA_DIR/intellij-coverage/intellij_coverage_report.ic"

readonly EXPORTER_CONFIG_PATH="$DATA_DIR/intellij-coverage/intellij_coverage_exporter_config.json"
readonly COVERAGE_EXPORT_OUTPUT_PATH="$DATA_DIR/coverage/coverage_data.json"

readonly VISUALIZATION_DIR="$DATA_DIR/visualization/icfg/coverage"

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
    "$TARGET_CLASS" \
    "$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH"

  set +e

java \
  -javaagent:"$AGENT_JAR=$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH" \
  -cp "$JUNIT_CONSOLE_JAR:$TEST_CLASS_PATH" \
  org.junit.platform.console.ConsoleLauncher \
  $JUNIT_OPTIONS

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

  dot -Tsvg \
    "$VISUALIZATION_DIR/$DOT_FILE_NAME" \
    -o "$VISUALIZATION_DIR/$SVG_FILE_NAME"
}

# ============================================================
# MAIN
# ============================================================
main_common() {
  run_junit_with_agent
  generate_coverage_data
  generate_block_map
  generate_coverage_graph
  generate_svg
  log "✅ Pipeline completed successfully"
}
