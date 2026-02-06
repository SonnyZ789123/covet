#!/usr/bin/env bash
set -Eeuo pipefail

readonly PATHCOV_PROJECT_DIR="${PATHCOV_PROJECT_DIR:?PATHCOV_PROJECT_DIR not set}"
readonly PATHCOV_DIR="$PATHCOV_PROJECT_DIR/pathcov"

source "$SCRIPTS_DIR/common/pipeline_common.sh"

generate_coverage_data() {
  log "⚙️ Exporting coverage data (DEV, Maven)"

  pushd "$PATHCOV_DIR" > /dev/null

  "$SCRIPTS_DIR/common/make_intellij_coverage_exporter_config.sh" \
    "$INTELLIJ_COVERAGE_REPORT_PATH" \
    "$COMPILED_ROOT" \
    "$SOURCE_PATH" \
    "$TARGET_CLASS" \
    "$COVERAGE_EXPORT_OUTPUT_PATH" \
    "$EXPORTER_CONFIG_PATH"

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.coverage.intellij.export.CoverageExportMain" \
    -Dexec.args="$EXPORTER_CONFIG_PATH"

  popd > /dev/null
}

generate_block_map() {
  log "⚙️ Generating block map (DEV, Maven)"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.icfg.GenerateBlockMap" \
    -Dexec.args=" \
      $CLASS_PATH \
      \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" \
      $COVERAGE_EXPORT_OUTPUT_PATH \
      $BLOCK_MAP_PATH \
      $PROJECT_PREFIXES"

  popd > /dev/null
}

generate_coverage_graph() {
  log "⚙️ Generating coverage graph (DEV, Maven)"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.icfg.coverage.GenerateCoverageGraph" \
    -Dexec.args=" \
      $CLASS_PATH \
      \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" \
      $BLOCK_MAP_PATH \
      $VISUALIZATION_DIR/$DOT_FILE_NAME \
      $PROJECT_PREFIXES"

  popd > /dev/null
}

main_common "$@"
