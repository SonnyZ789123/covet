FROM eclipse-temurin:17-jdk

LABEL maintainer="yoranmertens0@gmail.com"

###############################################################################
# Install runtime system dependencies only
###############################################################################
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        graphviz \
        curl && \
    rm -rf /var/lib/apt/lists/*

###############################################################################
# Install pathcov
###############################################################################
ENV PATHCOV_VERSION=2.4.0
ENV PATHCOV_JAR=/opt/pathcov/pathcov-${PATHCOV_VERSION}.jar

RUN mkdir -p /opt/pathcov && \
    curl -fsSL \
      https://github.com/SonnyZ789123/pathcov/releases/download/v${PATHCOV_VERSION}/pathcov-${PATHCOV_VERSION}.jar \
      -o ${PATHCOV_JAR}

###############################################################################
# Install IntelliJ Coverage Agent
###############################################################################
ENV INTELLIJ_COVERAGE_VERSION=1.0.771
ENV INTELLIJ_COVERAGE_AGENT_JAR=/opt/intellij-coverage/intellij-coverage-agent-${INTELLIJ_COVERAGE_VERSION}.jar

RUN mkdir -p /opt/intellij-coverage && \
    curl -fsSL \
      https://repo1.maven.org/maven2/org/jetbrains/intellij/deps/intellij-coverage-agent/${INTELLIJ_COVERAGE_VERSION}/intellij-coverage-agent-${INTELLIJ_COVERAGE_VERSION}.jar \
      -o ${INTELLIJ_COVERAGE_AGENT_JAR}

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
# Default
###############################################################################
CMD ["/bin/bash"]
