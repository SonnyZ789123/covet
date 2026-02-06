#!/usr/bin/env bash
set -Eeuo pipefail

# ------------------------------------------------------------
# Args
# ------------------------------------------------------------

if [[ $# -ne 6 ]]; then
  echo "Usage: $0 <coverage_report_path> <compiled_classes_path> <source_path> <target_class> <coverage_export_output_path> <output_config_path>" >&2
  exit 1
fi

COVERAGE_REPORT_PATH="$1"
COMPILED_CLASSES_PATH="$2"
SOURCE_PATH="$3"
TARGET_CLASS="$4"
COVERAGE_EXPORT_OUTPUT_PATH="$5"
OUTPUT_CONFIG_PATH="$6"

# ------------------------------------------------------------
# Ensure output directory exists
# ------------------------------------------------------------

mkdir -p "$(dirname "$OUTPUT_CONFIG_PATH")"

# ------------------------------------------------------------
# Generate exporter config JSON
# ------------------------------------------------------------

cat > "$OUTPUT_CONFIG_PATH" <<EOF
{
  "reportPath": "${COVERAGE_REPORT_PATH}",
  "outputRoots": [
    "${COMPILED_CLASSES_PATH}"
  ],
  "sourceRoots": [
    "${SOURCE_PATH}"
  ],
  "includeClasses": [
    "${TARGET_CLASS}"
  ],
  "outputJson": "${COVERAGE_EXPORT_OUTPUT_PATH}"
}
EOF

echo "[OK] Generated IntelliJ coverage exporter config:"
echo "  $OUTPUT_CONFIG_PATH"
