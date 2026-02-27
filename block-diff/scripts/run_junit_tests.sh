#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# CHECK ENV VARIABLES
# ============================================================
: "${JUNIT_CONSOLE_JAR:?JUNIT_CONSOLE_JAR not set}"
: "${TEST_CLASS_PATH:?TEST_CLASS_PATH not set}"
: "${BLOCK_DIFF_OUTPUT_PATH:?BLOCK_DIFF_OUTPUT_PATH not set}"

INCLUDE_TAGS="$(python3 generate_include_tags.py "${BLOCK_DIFF_OUTPUT_PATH}")"

# If no tags, there are no added/removed blocks -> skip tests
if [[ -z "${INCLUDE_TAGS// }" ]]; then
  echo "ℹ️ No added/removed blocks found. Skipping test execution."
  exit 0
fi

echo "⚙️ Running test suite with tags: $INCLUDE_TAGS"

# Split INCLUDE_TAGS into words (expects: --include-tag tag1 --include-tag tag2 ...)
read -r -a TAG_ARGS <<< "$INCLUDE_TAGS"

java \
  -cp "$JUNIT_CONSOLE_JAR:$TEST_CLASS_PATH" \
  org.junit.platform.console.ConsoleLauncher \
  --scan-classpath \
  "${TAG_ARGS[@]}"

echo "✅ Running test suite completed"
