# ============================================================
# CHECK ENV VARIABLES
# ============================================================
: "${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR not set}"
: "${TEST_CLASS_PATH:?TEST_CLASS_PATH not set}"
: "${BLOCK_DIFF_OUTPUT_PATH:?BLOCK_DIFF_OUTPUT_PATH not set}"

INCLUDE_TAGS=$(python3 generate_include_tags.py "${BLOCK_DIFF_OUTPUT_PATH}")

run_junit_with_agent() {
  echo "⚙️ Running test suite"

  # Split INCLUDE_TAGS into words (expects: --include-tag tag1 --include-tag tag2 ...)
  read -r -a TAG_ARGS <<< "$INCLUDE_TAGS"

  java \
    -cp "$JUNIT_CONSOLE_JAR:$TEST_CLASS_PATH" \
    org.junit.platform.console.ConsoleLauncher \
    --scan-classpath \
    "${TAG_ARGS[@]}"
}

run_junit_with_agent
echo "✅ Running test suite completed"
