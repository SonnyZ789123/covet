#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# CONFIG
# ============================================================

# Docker Compose services
PATHCOV_SERVICE="pathcov"
JDART_SERVICE="jdart"

# Scripts / configs inside containers
PATHCOV_SCRIPT="/scripts/test_icfg_coverage.sh"
SUT_CONFIG="/configs/sut.config"
JDART_JPF_CONFIG="/configs/jdart/sut.jpf"

# Optional arguments
DATA_DIR="/data"

# ============================================================
# LOGGING
# ============================================================

log() {
  echo "[INFO] $*"
}

# ============================================================
# MAIN
# ============================================================

main() {
  log "⚙️ Starting containers"
  docker compose up -d

  log "⚙️ Running pathcov stage"
  docker compose exec "$PATHCOV_SERVICE" "$PATHCOV_SCRIPT" "$SUT_CONFIG" "$DATA_DIR"

  log "⚙️ Running JDart / JPF stage"
  docker compose exec "$JDART_SERVICE" /jdart-project/jpf-core/bin/jpf "$JDART_JPF_CONFIG"

  log "✅ Pipeline completed successfully"
}

main "$@"
