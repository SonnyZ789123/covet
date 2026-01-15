# Coverage-Guided Concolic Pipeline

An end-to-end, containerized pipeline for **coverage-guided concolic test generation** in Java.
This project integrates **static CFG/ICFG analysis**, **runtime coverage instrumentation**, **coverage graph construction**, and **heuristic-guided concolic execution with JDart** to systematically discover uncovered execution paths.

The pipeline is designed to be **reproducible**, **configurable**, and **tool-agnostic**, with a single canonical SUT specification that drives all analysis stages.

---

## Overview

The pipeline consists of two main stages:

1. **Pathcov stage**

   * Generates block maps (CFG/ICFG)
   * Runs the existing test suite with a custom Java coverage agent
   * Extracts covered instruction paths
   * Builds coverage graphs

2. **JDart stage**

   * Uses coverage information to guide concolic execution
   * Explores uncovered execution paths
   * Optionally generates new JUnit test cases

All stages are fully containerized and orchestrated via Docker Compose.

---

## Repository Structure

```
.
├── configs
│   └── sut.yml                   # Canonical SUT specification (single source of truth)
├── docker-compose.yml            # Orchestrates Pathcov and JDart containers
├── development
│   └── data                      # Developmnet: bind-mount for output 
├── jdart
│   ├── Dockerfile
│   └── configs
│       ├── sut.jpf               # Base JDart config (user-editable)
│       ├── sut_gen.jpf           # AUTO-GENERATED from sut.yml
│       └── coverage_heuristic.config
├── pathcov
│   ├── Dockerfile
│   ├── configs
│   │   └── sut.config            # AUTO-GENERATED from sut.yml
│   └── scripts
│       └── generate_pathcov.sh
├── scripts
│   └── generate_sut_configs.py   # Generates tool-specific configs from sut.yml
├── run_pipeline.sh               # Single entry point for running the pipeline
└── requirements.txt              # Host-side Python dependencies
```

---

## Requirements (Host)

* Docker
* Docker Compose
* Python ≥ 3.8
* PyYAML

Install the Python dependency once:

```bash
python3 -m pip install -r requirements.txt
```

---

## Step 1: Configure the SUT directory (`.env`)

The System Under Test (SUT) must be available on the host and mounted into both containers.

Create a `.env` file in the repository root:

```bash
SUT_DIR=$HOME/dev/jdart-examples
```

Requirements for `SUT_DIR`:

* It must contain **compiled class files**
* The directory will be mounted into containers at `/sut`

Example inside the container:

```
/sut/out/production/jdart-examples
/sut/out/test/jdart-examples
```

> **Note**
> `.env` is automatically read by Docker Compose.
> It is also explicitly loaded by `run_pipeline.sh` so that host-side scripts see the same variables.

---

## Step 2: Define the SUT and target method (`configs/sut.yml`)

`sut.yml` is the **single canonical configuration** that defines:

* where compiled classes live
* which method is analyzed
* where generated tests should be written

Example:

```yaml
sut:
  compiled_root: out/production/jdart-examples
  test_root: out/test/jdart-examples

test_generation:
  generated_tests_dir_out: data/generated-tests

target:
  class: test.testsuites.Test
  method: bar
  return: int
  parameters:
    - name: a
      type: int

analysis:
  project_prefixes:
    - test.testsuites
```

You only edit **this file** to change the SUT or the analyzed method.

All tool-specific configurations are **derived automatically** from this file.

---

## Step 3: (Optional) Configure JDart behavior

You may customize JDart-specific options in:

```
jdart/configs/sut.jpf
```

This file is **not generated** and is intended for manual tuning.

### Examples of useful JDart options

Enable fine-grained logging:

```properties
log.finest=jdart,jdart.testsuites
```

Enable test generation:

```properties
jdart.tests.gen=true
```

Select a custom exploration strategy:

```properties
# Coverage guided
jdart.exploration=gov.nasa.jpf.jdart.exploration.CoverageHeuristicStrategy(/configs/coverage_heuristic.config)

# Depth First
jdart.exploration=gov.nasa.jpf.jdart.exploration.DFSStrategy

# Breadth First
jdart.exploration=gov.nasa.jpf.jdart.exploration.BFSStrategy
```

During execution, this file is **combined** with the auto-generated JDart configuration (`sut_gen.jpf`).

---

## Step 4: Run the pipeline

Once everything is configured, run:

```bash
./run_pipeline.sh
```

This single command will:

1. Generate tool-specific configs from `configs/sut.yml`
2. Start the Docker containers
3. Run the Pathcov stage
4. Run JDart with the generated configuration

No manual Docker commands are required.

---

## Generated Artifacts

All generated data is written to a shared Docker volume mounted at:

```
/data
```

This includes:

* coverage paths
* coverage graphs (`.dot`, `.svg`)
* JDart instruction paths
* generated test cases (if enabled)

The volume persists across container runs.

---

## Development Mode (Optional)

By default, the pipeline runs in **production mode**, using **pre-built Docker images**.

For development (e.g. modifying Pathcov or the coverage agent locally), you can enable **development mode** using a Docker Compose override file.

### docker-compose.override.yml

Create a `docker-compose.override.yml` file and bind-mount your locally cloned tools:

```yaml
services:
  pathcov:
    volumes:
      - ../pathcov:/work/pathcov
    environment:
      PATHCOV_PROJECT_DIR=/work/pathcov
      COVERAGE_AGENT_JAR=/work/pathcov/coverage-agent/target/coverage-agent-1.0.0.jar
      JUNIT_CONSOLE_JAR=/work/pathcov/tools/junit-platform-console-standalone.jar
```

Key points:

* `docker-compose.override.yml` is **automatically applied** by Docker Compose
* Production images remain unchanged
* You can override:

  * tool source directories
  * JAR locations
  * other environment variables as needed

No script changes are required.

---

## Docker Architecture

### Docker Compose

* **pathcov container**

  * Runs coverage instrumentation and graph generation
  * Mounts:

    * `/sut` (SUT)
    * `/configs` (Pathcov configs)
    * `/data` (shared artifacts)
* **jdart container**

  * Runs JDart/JPF
  * Mounts:

    * `/sut` (SUT)
    * `/configs` (JDart configs)
    * `/data` (shared artifacts)

Containers do **not** communicate directly.
The host orchestrates execution via `run_pipeline.sh`.

---

## Design Principles

* **Single source of truth**
  All tool-specific configs are generated from `sut.yml`

* **No configuration drift**
  Pathcov and JDart always analyze the same method

* **Containerized execution**
  No local Java/JPF/JDart installation required

* **Reproducible experiments**
  Identical inputs lead to identical results

---

## Typical Workflow

```bash
git clone <repo>
cd coverage-guided-concolic-pipeline

python3 -m pip install -r requirements.txt

cat <<EOF > .env
ENV=dev
SUT_DIR=$HOME/dev/jdart-examples
EOF

vim configs/sut.yml
vim jdart/configs/sut.jpf   # optional

./run_pipeline.sh

```

---

## Notes for Research / Artifact Evaluation

* The pipeline cleanly separates **experiment specification** from **tool configuration**
* All analysis stages are deterministic given the same inputs
* The architecture is intentionally modular to support future extensions

---

## License

See `LICENSE`.
