FROM maven:3.9.9-eclipse-temurin-17

LABEL maintainer="yoranmertens0@gmail.com"

###############################################################################
# Install system dependencies
###############################################################################
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        graphviz \
        ca-certificates \
        bash && \
    rm -rf /var/lib/apt/lists/*

###############################################################################
# Project directory
###############################################################################
ENV PATHCOV_DIR=/pathcov-project
RUN mkdir -p ${PATHCOV_DIR}

###############################################################################
# Install SootUp
###############################################################################
WORKDIR ${PATHCOV_DIR}
RUN git clone --branch v2.0.1 https://github.com/SonnyZ789123/SootUp.git
WORKDIR ${PATHCOV_DIR}/SootUp
RUN git checkout v2.0.1
RUN mvn -B clean install -DskipTests

###############################################################################
# Install pathcov
###############################################################################
WORKDIR ${PATHCOV_DIR}
RUN git clone --branch v1.0.0 https://github.com/SonnyZ789123/pathcov.git
WORKDIR ${PATHCOV_DIR}/pathcov
RUN git checkout v1.0.0
RUN mvn -B clean install -DskipTests

###############################################################################
# Install coverage-agent
###############################################################################
WORKDIR ${PATHCOV_DIR}
RUN git clone --branch v1.0.0 https://github.com/SonnyZ789123/coverage-agent.git
WORKDIR ${PATHCOV_DIR}/coverage-agent
RUN git checkout v1.0.0
RUN mvn -B clean install -DskipTests

###############################################################################
# Convenience env vars (VERY useful in scripts)
###############################################################################
ENV PATHCOV_JAR=${PATHCOV_DIR}/pathcov/target/pathcov-1.0.0.jar
ENV COVERAGE_AGENT_JAR=${PATHCOV_DIR}/coverage-agent/target/coverage-agent-1.0.0.jar

###############################################################################
# Default
###############################################################################
WORKDIR ${PATHCOV_DIR}
CMD ["/bin/bash"]
