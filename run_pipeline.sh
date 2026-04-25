#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Load container-side path config (container.env)
# ============================================================

if [[ -f container.env ]]; then
  set -a
  source container.env
  set +a
fi

# ============================================================
# CONFIG
# ============================================================

ENVIRONMENT="${ENV:-prod}"

PATHCOV_SERVICE="pathcov"
COVET_SERVICE="covet-engine"

PATHCOV_SCRIPT="${CONTAINER_SCRIPTS_DIR}/run_pipeline.sh"
SUT_CONFIG="${CONTAINER_CONFIGS_DIR}/sut.config"
COVET_JPF_CONFIG="${CONTAINER_CONFIGS_DIR}/sut.jpf"

DATA_DIR="${CONTAINER_DATA_DIR}"

OUTPUT_DIR="./output"
DEV_DATA_DIR="./development/data"

# ============================================================
# LOGGING
# ============================================================

log() {
  echo "[INFO] $*"
}

# ============================================================
# SAFE DIRECTORY CLEARING
# ============================================================

clear_directory() {
  local dir="$1"

  # Safety checks
  if [[ -z "$dir" || "$dir" == "/" ]]; then
    echo "[ERROR] Refusing to clear unsafe directory: '$dir'" >&2
    exit 1
  fi

  if [[ -d "$dir" ]]; then
    log "🧹 Clearing directory: $dir"
    rm -rf "${dir:?}/"*
  fi
}

# ============================================================
# Compose file stack builder
# ============================================================

compose_up() {
  FILES="-f docker-compose.yml"

  if [[ "$ENVIRONMENT" == "dev" && -f docker-compose.override.yml ]]; then
    FILES="$FILES -f docker-compose.override.yml"
  fi

  [[ -f docker-compose.sut.yml ]] && FILES="$FILES -f docker-compose.sut.yml"
  [[ -f docker-compose.deps.yml ]] && FILES="$FILES -f docker-compose.deps.yml"

  docker compose --env-file container.env $FILES up -d
}

compose_exec() {
  FILES="-f docker-compose.yml"

  if [[ "$ENVIRONMENT" == "dev" && -f docker-compose.override.yml ]]; then
    FILES="$FILES -f docker-compose.override.yml"
  fi

  [[ -f docker-compose.sut.yml ]] && FILES="$FILES -f docker-compose.sut.yml"
  [[ -f docker-compose.deps.yml ]] && FILES="$FILES -f docker-compose.deps.yml"

  docker compose --env-file container.env $FILES exec "$@"
}


# ============================================================
# MAIN
# ============================================================

main() {
  log "⚙️ Environment: $ENVIRONMENT"

  # Ensure directories exist
  mkdir -p "$OUTPUT_DIR"

  if [[ "$ENVIRONMENT" == "dev" ]]; then
    mkdir -p "$DEV_DATA_DIR"
  fi

  # Clear output directory always
  clear_directory "$OUTPUT_DIR"

  # Clear development directory only in dev mode
  if [[ "$ENVIRONMENT" == "dev" ]]; then
    clear_directory "$DEV_DATA_DIR"
  fi

  log "⚙️ Generating tool-specific configs from sut.yml"
  python3 scripts/generate_sut_configs.py

  log "⚙️ Generating docker-compose.sut.yml for SUT"
  python3 scripts/generate_sut_compose.py

  log "⚙️ Starting containers"
  compose_up

  log "⚙️ Running pathcov stage"
  compose_exec "$PATHCOV_SERVICE" "$PATHCOV_SCRIPT" "$SUT_CONFIG" "$DATA_DIR"

  log "⚙️ Running covet-engine / JPF stage"
  compose_exec "$COVET_SERVICE" /covet-engine-project/jpf-core/bin/jpf "$COVET_JPF_CONFIG"

  log "✅ Pipeline completed successfully"
}

main "$@"
