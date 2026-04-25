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

readonly PATHCOV_PROJECT_DIR="${PATHCOV_PROJECT_DIR:?PATHCOV_PROJECT_DIR not set}"
readonly PATHCOV_DIR="$PATHCOV_PROJECT_DIR/pathcov"

source "$SCRIPTS_DIR/common/pipeline_common.sh"

write_cg_classes() {
  log "⚙️ Writing CG classes (DEV, Maven)"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.cg.WriteCallGraphClasses" \
    -Dexec.args=" \
      $CLASS_PATH \
      \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" \
      $CG_CLASSES_OUTPUT_PATH \
      $PROJECT_PREFIXES"

  popd > /dev/null
}

generate_coverage_data() {
  log "⚙️ Exporting coverage data (DEV, Maven)"

  pushd "$PATHCOV_DIR" > /dev/null

  "$SCRIPTS_DIR/common/make_intellij_coverage_exporter_config.sh" \
    "$INTELLIJ_COVERAGE_REPORT_PATH" \
    "$COMPILED_ROOT" \
    "$SOURCE_PATH" \
    "$CG_CLASSES_OUTPUT_PATH" \
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

calculate_branch_coverage() {
  log "⚙️ Calculating branch coverage (DEV, Maven)"

  pushd "$PATHCOV_DIR" > /dev/null

  mvn exec:java \
    -Dexec.mainClass="com.kuleuven.coverage.GenerateBranchCoverage" \
    -Dexec.args="$BLOCK_MAP_PATH"

  popd > /dev/null
}

main_common "$@"
