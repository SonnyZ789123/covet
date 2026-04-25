# How to bump pathcov or covet-engine versions

## Bumping pathcov

1. **Update the version in the Dockerfile** (`pathcov/Dockerfile`): set `PATHCOV_VERSION` to the new version (e.g., `2.7.0`)

2. **Build the prod image** (from inside the `pathcov/` folder):
   ```bash
   docker build -t pathcov-image:<version> .
   ```

3. **Tag for Docker Hub**:
   ```bash
   docker tag pathcov-image:<version> sonnyz789123/pathcov-image:<version>
   docker tag pathcov-image:<version> sonnyz789123/pathcov-image:latest
   ```

4. **Push both tags**:
   ```bash
   docker push sonnyz789123/pathcov-image:<version>
   docker push sonnyz789123/pathcov-image:latest
   ```

5. **Build the dev image** (from inside the `pathcov/` folder — depends on `sonnyz789123/pathcov-image:latest` being up to date):
   ```bash
   docker build -f ./dev/Dockerfile.dev -t pathcov-image-dev .
   ```

6. **Update `docker-compose.yml`**: set the pathcov service image to `sonnyz789123/pathcov-image:<version>` (use the explicit version, not `:latest`)

## Bumping covet-engine (forked JDart)

1. **Update the version in the Dockerfile** (`covet-engine/Dockerfile`): set `COVET_VERSION` to the new version

2. **Build the image** (from inside the `covet-engine/` folder — must use `--platform linux/amd64` because the engine requires Java 8 on x86):
   ```bash
   docker build --platform linux/amd64 -t covet-engine-image:<version> .
   ```

3. **Tag for Docker Hub**:
   ```bash
   docker tag covet-engine-image:<version> sonnyz789123/covet-engine-image:<version>
   docker tag covet-engine-image:<version> sonnyz789123/covet-engine-image:latest
   ```

4. **Push both tags**:
   ```bash
   docker push sonnyz789123/covet-engine-image:<version>
   docker push sonnyz789123/covet-engine-image:latest
   ```

5. **Update `docker-compose.yml`**: set the covet-engine service image to `sonnyz789123/covet-engine-image:<version>` (use the explicit version, not `:latest`)

## Conventions

- Image version always matches the project version (e.g., pathcov v2.7.0 → `pathcov-image:2.7.0`)
- `docker-compose.yml` always pins an explicit version, never `:latest`
- The pathcov dev image (`Dockerfile.dev`) uses `sonnyz789123/pathcov-image:latest` as its base, so always build and push the prod image first
