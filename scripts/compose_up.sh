FILES="-f docker-compose.yml"

[[ -f docker-compose.override.yml ]] && FILES="$FILES -f docker-compose.override.yml"
[[ -f docker-compose.sut.yml ]] && FILES="$FILES -f docker-compose.sut.yml"
[[ -f docker-compose.deps.yml ]] && FILES="$FILES -f docker-compose.deps.yml"

docker compose --env-file container.env $FILES up -d