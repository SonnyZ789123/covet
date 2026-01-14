#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# CONFIG
# ============================================================
readonly HOME_DIR="$HOME"

# Specific to the SUT
readonly JDART_EXAMPLES_DIR="$HOME_DIR/dev/jdart-examples"
readonly CLASS_PATH="$JDART_EXAMPLES_DIR/out/production/jdart-examples"
readonly TEST_CLASS_PATH="$JDART_EXAMPLES_DIR/out/test/jdart-examples"

readonly FULLY_QUALIFIED_METHOD_SIGNATURE="<test.testsuites.Test: int bar(int)>"
readonly PROJECT_PREFIXES="test.testsuites" # Comma-separated list of project prefixes

# Tools inside image
readonly PATHCOV_PROJECT_DIR="${PATHCOV_DIR:?PATHCOV_DIR is not set}"  # This variable is injected at container runtime via ENV
readonly PATHCOV_DIR="$PATHCOV_PROJECT_DIR/pathcov"

readonly AGENT_JAR="${COVERAGE_AGENT_JAR:?COVERAGE_AGENT_JAR is not set}"  # This variable is injected at container runtime via ENV

readonly JUNIT_CONSOLE_JAR="${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR is not set}"  # This variable is injected at container runtime via ENV

# Outputs
readonly BLOCK_MAP_PATH="$DATA_DIR/blockmaps/icfg_block_map.json"
readonly COVERAGE_PATHS_OUTPUT_PATH="$DATA_DIR/coverage/coverage_paths.json"
readonly JDART_INSTRUCTION_PATHS_OUTPUT_PATH="$DATA_DIR/coverage/jdart_instruction_paths.json"

readonly VISUALIZATION_DIR="$PATHCOV_DIR/out/visualization/icfg/coverage"

readonly DOT_FILE_NAME="coverage_graph.dot" # See application.properties in pathcov
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
    -Dexec.args="$CLASS_PATH \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" $COVERAGE_PATHS_OUTPUT_PATH $BLOCK_MAP_PATH"

  popd > /dev/null
}

generate_svg() {
  log "⚙️ Generating SVG visualization"

  dot -Tsvg \
    "$VISUALIZATION_DIR/$DOT_FILE_NAME" \
    -o "$VISUALIZATION_DIR/$SVG_FILE_NAME"

  open "$VISUALIZATION_DIR/$SVG_FILE_NAME"
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
