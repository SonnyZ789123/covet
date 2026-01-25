#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# CHECK ENV VARIABLES FOR MOUNTED DIRECTORIES
# ============================================================
: "${SUT_DIR:?SUT_DIR not set}"
: "${DATA_DIR:?DATA_DIR not set}"
: "${CONFIGS_DIR:?CONFIGS_DIR not set}"
: "${SCRIPTS_DIR:?SCRIPTS_DIR not set}"

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

: "${CLASS_PATH:?CLASS_PATH not set}"
: "${TEST_CLASS_PATH:?TEST_CLASS_PATH not set}"
: "${SOURCE_PATH:?SOURCE_PATH not set}"
: "${TARGET_CLASS:?TARGET_CLASS not set}"
: "${FULLY_QUALIFIED_METHOD_SIGNATURE:?FULLY_QUALIFIED_METHOD_SIGNATURE not set}"

# ============================================================
# FIXED CONFIG
# ============================================================
readonly CLASS_PATH="${SUT_DIR}/${CLASS_PATH}"
readonly TEST_CLASS_PATH="${SUT_DIR}/${TEST_CLASS_PATH}"

# Shared data volume with the JDart container
readonly DATA_DIR="${2:-$DATA_DIR}"

# Tools inside image
readonly PATHCOV_PROJECT_DIR="${PATHCOV_PROJECT_DIR:?PATHCOV_PROJECT_DIR is not set}"  # This variable is injected at container runtime via ENV
readonly PATHCOV_DIR="$PATHCOV_PROJECT_DIR/pathcov"

readonly AGENT_JAR="${INTELLIJ_COVERAGE_AGENT_JAR:?INTELLIJ_COVERAGE_AGENT_JAR is not set}"  # This variable is injected at container runtime via ENV

readonly JUNIT_CONSOLE_JAR="${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR is not set}"  # This variable is injected at container runtime via ENV

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
# STEPS
# ============================================================
generate_block_map() {
  log "⚙️ Generating CFG block map for $FULLY_QUALIFIED_METHOD_SIGNATURE"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.icfg.GenerateBlockMap" \
    -Dexec.args="$CLASS_PATH \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" $BLOCK_MAP_PATH $PROJECT_PREFIXES"

  popd > /dev/null
}

run_junit_with_agent() {
  log "⚙️ Running JUnit tests with coverage agent"

  
  "$SCRIPTS_DIR/make_coverage_agent_args.sh" \
    "$INTELLIJ_COVERAGE_REPORT_PATH" \
    "$TARGET_CLASS" \
    "$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH"

  set +e
  java \
    -javaagent:"$AGENT_JAR=$INTELLIJ_COVERAGE_AGENT_CONFIG_PATH" \
    -cp "$JUNIT_CONSOLE_JAR:$TEST_CLASS_PATH:$CLASS_PATH" \
    org.junit.platform.console.ConsoleLauncher \
    --scan-classpath \
    > /dev/null

  local exit_code=$?
  set -e

  if [[ $exit_code -ne 0 ]]; then
    warn "========================================================="
    warn "    ⚠️ Some JUnit tests FAILED, continuing anyway ⚠️"
    warn "========================================================="
  fi

  log "✅ Running JUnit tests completed"
}

generate_coverage_data() {
  log "⚙️ Generating line coverage JSON export"

  pushd "$PATHCOV_DIR" > /dev/null

  "$SCRIPTS_DIR/make_intellij_coverage_exporter_config.sh" \
    "$INTELLIJ_COVERAGE_REPORT_PATH" \
    "$CLASS_PATH" \
    "$SOURCE_PATH" \
    "$TARGET_CLASS" \
    "$COVERAGE_EXPORT_OUTPUT_PATH" \
    "$EXPORTER_CONFIG_PATH"


  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.coverage.intellij.export.CoverageExportMain" \
    -Dexec.args="$EXPORTER_CONFIG_PATH"

  popd > /dev/null
}

generate_coverage_graph() {
  log "⚙️ Generating coverage graph"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.icfg.coverage.GenerateCoverageGraph" \
    -Dexec.args="$CLASS_PATH \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" $COVERAGE_EXPORT_OUTPUT_PATH $BLOCK_MAP_PATH $VISUALIZATION_DIR/$DOT_FILE_NAME"

  popd > /dev/null
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
main() {
  generate_block_map
  run_junit_with_agent
  generate_coverage_data
  generate_coverage_graph
  generate_svg
  log "✅ Pipeline completed successfully"
}

main "$@"
