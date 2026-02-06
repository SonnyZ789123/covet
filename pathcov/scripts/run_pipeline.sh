#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# CHECK ENV VARIABLES FOR MOUNTED DIRECTORIES
# ============================================================
: "${SUT_DIR:?SUT_DIR not set}"
: "${DATA_DIR:?DATA_DIR not set}"
: "${CONFIGS_DIR:?CONFIGS_DIR not set}"
: "${SCRIPTS_DIR:?SCRIPTS_DIR not set}"


ENV="${ENV:-prod}"

case "$ENV" in
  dev)
    exec "$SCRIPTS_DIR/dev/run_pipeline_dev.sh" "$@"
    ;;
  prod)
    exec "$SCRIPTS_DIR/prod/run_pipeline_prod.sh" "$@"
    ;;
  *)
    echo "[ERROR] Unknown ENV: $ENV" >&2
    echo "Expected one of: dev, prod" >&2
    exit 1
    ;;
esac

