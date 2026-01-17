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
ENV PATHCOV_PROJECT_DIR=/pathcov-project
RUN mkdir -p ${PATHCOV_PROJECT_DIR}

###############################################################################
# Install SootUp
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
RUN git clone --branch v2.0.1 https://github.com/SonnyZ789123/SootUp.git
WORKDIR ${PATHCOV_PROJECT_DIR}/SootUp
RUN git checkout v2.0.1
RUN mvn -B clean install -DskipTests

###############################################################################
# Install pathcov
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
RUN git clone --branch v1.1.0 https://github.com/SonnyZ789123/pathcov.git
WORKDIR ${PATHCOV_PROJECT_DIR}/pathcov
RUN git checkout v1.1.0
RUN mvn -B clean install -DskipTests

###############################################################################
# Install coverage-agent
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
RUN git clone --branch v1.0.2 https://github.com/SonnyZ789123/coverage-agent.git
WORKDIR ${PATHCOV_PROJECT_DIR}/coverage-agent
RUN git checkout v1.0.2
RUN mvn -B clean install -DskipTests

###############################################################################
# Install JUnit Platform Console Standalone
###############################################################################
ENV JUNIT_VERSION=1.12.2
ENV JUNIT_CONSOLE_JAR=/opt/junit/junit-platform-console-standalone-${JUNIT_VERSION}.jar

RUN mkdir -p /opt/junit && \
    curl -fsSL \
      https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/${JUNIT_VERSION}/junit-platform-console-standalone-${JUNIT_VERSION}.jar \
      -o ${JUNIT_CONSOLE_JAR}

###############################################################################
# Convenience env vars (VERY useful in scripts)
###############################################################################
ENV PATHCOV_JAR=${PATHCOV_PROJECT_DIR}/pathcov/target/pathcov-1.1.0.jar
ENV COVERAGE_AGENT_JAR=${PATHCOV_PROJECT_DIR}/coverage-agent/target/coverage-agent-1.0.2.jar

###############################################################################
# Default
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
CMD ["/bin/bash"]
