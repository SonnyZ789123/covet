#!/usr/bin/env bash
set -Eeuo pipefail

readonly PATHCOV_JAR="${PATHCOV_JAR:?PATHCOV_JAR not set}"

source "$SCRIPTS_DIR/common/pipeline_common.sh"

generate_coverage_data() {
  log "⚙️ Exporting coverage data (PROD)"

  "$SCRIPTS_DIR/common/make_intellij_coverage_exporter_config.sh" \
    "$INTELLIJ_COVERAGE_REPORT_PATH" \
    "$COMPILED_ROOT" \
    "$SOURCE_PATH" \
    "$TARGET_CLASS" \
    "$COVERAGE_EXPORT_OUTPUT_PATH" \
    "$EXPORTER_CONFIG_PATH"

  java -cp "$PATHCOV_JAR" \
    com.kuleuven.coverage.intellij.export.CoverageExportMain \
    "$EXPORTER_CONFIG_PATH"
}

generate_block_map() {
  log "⚙️ Generating block map (PROD)"

  java -cp "$PATHCOV_JAR" \
    com.kuleuven.icfg.GenerateBlockMap \
    $CLASS_PATH \
    "$FULLY_QUALIFIED_METHOD_SIGNATURE" \
    $COVERAGE_EXPORT_OUTPUT_PATH \
    $BLOCK_MAP_PATH \
    $PROJECT_PREFIXES
}

generate_coverage_graph() {
  log "⚙️ Generating coverage graph (PROD)"

  java -cp "$PATHCOV_JAR" \
    com.kuleuven.icfg.coverage.GenerateCoverageGraph \
    $CLASS_PATH \
    "$FULLY_QUALIFIED_METHOD_SIGNATURE" \
    $BLOCK_MAP_PATH \
    "$VISUALIZATION_DIR/$DOT_FILE_NAME" \
    $PROJECT_PREFIXES
}

main_common "$@"
