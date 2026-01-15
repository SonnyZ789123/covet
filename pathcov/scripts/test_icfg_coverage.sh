#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# LOAD CONFIGURABLE SUT CONFIG
# ============================================================

readonly SUT_CONFIG_FILE="${1:-/configs/sut.config}"

[[ -f "$SUT_CONFIG_FILE" ]] || {
  echo "[ERROR] SUT config not found: $SUT_CONFIG_FILE" >&2
  exit 1
}

# shellcheck source=/dev/null
source "$SUT_CONFIG_FILE"

: "${CLASS_PATH:?CLASS_PATH not set}"
: "${TEST_CLASS_PATH:?TEST_CLASS_PATH not set}"
: "${FULLY_QUALIFIED_METHOD_SIGNATURE:?FULLY_QUALIFIED_METHOD_SIGNATURE not set}"

# ============================================================
# FIXED CONFIG
# ============================================================

readonly SUT_DIR="/sut"

readonly CLASS_PATH="${SUT_DIR}/${CLASS_PATH}"
readonly TEST_CLASS_PATH="${SUT_DIR}/${TEST_CLASS_PATH}"

# Shared data volume with the JDart container
readonly DATA_DIR="${2:-/data}"

# Tools inside image
readonly PATHCOV_PROJECT_DIR="${PATHCOV_PROJECT_DIR:?PATHCOV_PROJECT_DIR is not set}"  # This variable is injected at container runtime via ENV
readonly PATHCOV_DIR="$PATHCOV_PROJECT_DIR/pathcov"

readonly AGENT_JAR="${COVERAGE_AGENT_JAR:?COVERAGE_AGENT_JAR is not set}"  # This variable is injected at container runtime via ENV

readonly JUNIT_CONSOLE_JAR="${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR is not set}"  # This variable is injected at container runtime via ENV

# Outputs
readonly BLOCK_MAP_PATH="$DATA_DIR/blockmaps/icfg_block_map.json"
readonly COVERAGE_PATHS_OUTPUT_PATH="$DATA_DIR/coverage/coverage_paths.json"
readonly JDART_INSTRUCTION_PATHS_OUTPUT_PATH="$DATA_DIR/coverage/jdart_instruction_paths.json"

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

  mvn -q -DskipTests=true package
  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.icfg.GenerateBlockMap" \
    -Dexec.args="$CLASS_PATH \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" $BLOCK_MAP_PATH $PROJECT_PREFIXES"

  popd > /dev/null
}

run_junit_with_agent() {
  log "⚙️ Running JUnit tests with coverage agent"

  set +e
  java \
    -javaagent:"$AGENT_JAR=projectPrefix=$PROJECT_PREFIXES,outputPath=$COVERAGE_PATHS_OUTPUT_PATH,blockMapPath=$BLOCK_MAP_PATH" \
    -cp "$JUNIT_CONSOLE_JAR:$TEST_CLASS_PATH:$CLASS_PATH" \
    org.junit.platform.console.ConsoleLauncher \
    --scan-classpath \
    > /dev/null

  local exit_code=$?
  set -e

  if [[ $exit_code -ne 0 ]]; then
    warn "Some JUnit tests failed, continuing anyway"
  fi

  log "✅ Running JUnit tests completed"
}

generate_jdart_instruction_coverage() {
  log "⚙️ Generating JDart instruction coverage"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.jdart.GenerateJDartInstructionCoverage" \
    -Dexec.args="$COVERAGE_PATHS_OUTPUT_PATH $JDART_INSTRUCTION_PATHS_OUTPUT_PATH"

  popd > /dev/null
}

generate_coverage_graph() {
  log "⚙️ Generating coverage graph"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.icfg.coverage.GenerateCoverageGraph" \
    -Dexec.args="$CLASS_PATH \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" $COVERAGE_PATHS_OUTPUT_PATH $BLOCK_MAP_PATH $VISUALIZATION_DIR/$DOT_FILE_NAME"

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
  generate_jdart_instruction_coverage
  generate_coverage_graph
  generate_svg
  log "✅ Pipeline completed successfully"
}

main "$@"
