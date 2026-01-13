#!/bin/bash

set -e

# ---------- CONFIG ----------
JDART_EXAMPLES_DIR="$HOME/dev/jdart-examples"
CLASS_PATH="$JDART_EXAMPLES_DIR/out/production/jdart-examples"
TEST_CLASSES_PATH="$JDART_EXAMPLES_DIR/out/test/jdart-examples"

FULLY_QUALIFIED_METHOD_SIGNATURE="<test.SimpleExample.Test: int foo(int)>"

JUNIT_CONSOLE_JAR="$HOME/.m2/repository/org/junit/platform/junit-platform-console-standalone/1.12.2/junit-platform-console-standalone-1.12.2.jar"

AGENT_JAR="$HOME/dev/master-thesis/coverage-agent/target/coverage-agent-1.0.jar"

AGENT_ARG_projectPrefix="test/SimpleExample" # see fully qualified method signature
AGENT_OUTPUT_PATH="$HOME/dev/master-thesis/data/coverage_paths.json"
BLOCK_MAP_PATH="$HOME/dev/master-thesis/pathcov/out/cfg_block_map.json"
AGENT_ARGS="projectPrefix=$AGENT_ARG_projectPrefix,outputPath=$AGENT_OUTPUT_PATH,blockMapPath=$BLOCK_MAP_PATH"

JDART_INSTRUCTION_PATHS_OUTPUT_PATH="$HOME/dev/jdart-examples/data/jdart_instruction_paths.json"

# ----------------------------


echo "====== Generating CFG block map for method $FULLY_QUALIFIED_METHOD_SIGNATURE ======"

cd $HOME/dev/master-thesis/pathcov

mvn -q -DskipTests=true package
mvn exec:java \
  -Dexec.mainClass="com.kuleuven.icfg.GenerateBlockMap" \
  -Dexec.args="$CLASS_PATH \"$FULLY_QUALIFIED_METHOD_SIGNATURE\" $BLOCK_MAP_PATH"

cd $HOME/dev/master-thesis

echo "====== Running JUnit tests with coverage agent ======"

# 3️⃣ Execute test suite under javaagent (dynamic execution phase)
set +e # continue even if tests fail

java \
  -javaagent:$AGENT_JAR=$AGENT_ARGS \
  -cp \
  "$JUNIT_CONSOLE_JAR:$TEST_CLASSES_PATH:$CLASS_PATH" \
  org.junit.platform.console.ConsoleLauncher \
  --scan-classpath

JUNIT_EXIT_CODE=$?
set -e

if [ $JUNIT_EXIT_CODE -ne 0 ]; then
  echo "⚠️  Some JUnit tests failed, continuing anyway"
fi


echo "====== Generating JDart Instruction Coverage ======"

cd $HOME/dev/master-thesis/pathcov

mvn exec:java \
  -Dexec.mainClass="com.kuleuven.jdart.GenerateJDartInstructionCoverage" \
  -Dexec.args="$AGENT_OUTPUT_PATH $JDART_INSTRUCTION_PATHS_OUTPUT_PATH"

echo "✅ Done!"


echo "====== Generating Coverage Graph ======"

# See application.properties in pathcov repository for output dir
COVERAGE_DIR="$HOME/dev/master-thesis/pathcov/out/visualization/cfg/coverage"
DOT_DIR="$COVERAGE_DIR/dot"

rm -f "$DOT_DIR"/*.dot

mvn exec:java \
  -Dexec.mainClass="com.kuleuven.cfg.coverage.GenerateCoverageGraph" \
  -Dexec.args="$CLASS_PATH $AGENT_OUTPUT_PATH $BLOCK_MAP_PATH"

echo "✅ Done!"

echo "====== Generating SVGs from DOT files ======"

SVG_DIR="$COVERAGE_DIR/svg"
mkdir -p "$SVG_DIR"

for dot_file in "$DOT_DIR"/*.dot; do
  base=$(basename "$dot_file" .dot)
  dot -Tsvg "$dot_file" -o "$SVG_DIR/$base.svg"
  echo "✅ Generated $SVG_DIR/$base.svg"
done

