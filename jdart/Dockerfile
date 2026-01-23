FROM ubuntu:14.04

LABEL maintainer="yoranmertens0@gmail.com"

###############################################################################
# Base system & Java 8
###############################################################################
RUN apt-get update -y && \
    apt-get install -y software-properties-common python-software-properties && \
    add-apt-repository ppa:openjdk-r/ppa -y && \
    apt-get update -y && \
    apt-get install -y \
        openjdk-8-jdk \
        ant \
        maven \
        git \
        junit \
        build-essential \
        python \
        antlr3 \
        wget && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java && \
    update-alternatives --set javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV JUNIT_HOME=/usr/share/java

###############################################################################
# Project directory
###############################################################################
RUN mkdir /jdart-project
ENV JDART_DIR=/jdart-project

WORKDIR ${JDART_DIR}

###############################################################################
# Install jpf-core
###############################################################################
RUN git clone https://github.com/javapathfinder/jpf-core.git
WORKDIR ${JDART_DIR}/jpf-core
RUN git checkout JPF-8.0 && ant

###############################################################################
# Install jConstraints
###############################################################################
WORKDIR ${JDART_DIR}
RUN git clone https://github.com/samsbp/jconstraints.git
WORKDIR ${JDART_DIR}/jconstraints
RUN mvn install

###############################################################################
# Install Z3 4.4.1 (Linux binary)
###############################################################################
WORKDIR ${JDART_DIR}
RUN wget https://github.com/Z3Prover/z3/releases/download/z3-4.4.1/z3-4.4.1-x64-ubuntu-14.04.zip && \
    unzip z3-4.4.1-x64-ubuntu-14.04.zip && \
    rm z3-4.4.1-x64-ubuntu-14.04.zip && \
    ln -s z3-4.4.1-x64-ubuntu-14.04 z3

WORKDIR ${JDART_DIR}/z3/bin
RUN mvn install:install-file \
    -Dfile=com.microsoft.z3.jar \
    -DgroupId=com.microsoft \
    -DartifactId=z3 \
    -Dversion=4.4.1 \
    -Dpackaging=jar

ENV LD_LIBRARY_PATH=${JDART_DIR}/z3/bin

###############################################################################
# Install jconstraints-z3
###############################################################################
WORKDIR ${JDART_DIR}
RUN git clone https://github.com/samsbp/jconstraints-z3.git
WORKDIR ${JDART_DIR}/jconstraints-z3
RUN mvn install

###############################################################################
# Configure JPF
###############################################################################
RUN mkdir -p /root/.jpf && \
    echo "jpf-core = ${JDART_DIR}/jpf-core"     >> /root/.jpf/site.properties && \
    echo "jpf-jdart = ${JDART_DIR}/jdart"       >> /root/.jpf/site.properties && \
    echo "extensions=\${jpf-core},\${jpf-jdart}" >> /root/.jpf/site.properties

###############################################################################
# Configure jConstraints extensions
###############################################################################
RUN mkdir -p /root/.jconstraints/extensions && \
    cp ${JDART_DIR}/jconstraints-z3/target/jconstraints-z3-0.9.1-SNAPSHOT.jar /root/.jconstraints/extensions && \
    cp /root/.m2/repository/com/microsoft/z3/4.4.1/z3-4.4.1.jar \
         /root/.jconstraints/extensions/com.microsoft.z3.jar

###############################################################################
# Install JDart
###############################################################################
WORKDIR ${JDART_DIR}
RUN git clone --branch v2.0.0 https://github.com/SonnyZ789123/jdart.git
WORKDIR ${JDART_DIR}/jdart
RUN git checkout v2.0.0
RUN ant

WORKDIR ${JDART_DIR}

###############################################################################
# Default command (drop into shell)
###############################################################################
CMD ["/bin/bash"]
