FROM sonnyz789123/pathcov-image:2.6.1

LABEL maintainer="yoranmertens0@gmail.com"

###############################################################################
# Install system dependencies
###############################################################################
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        bash \
        python3 \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

###############################################################################
# Optional: make python -> python3
###############################################################################
RUN ln -s /usr/bin/python3 /usr/bin/python

###############################################################################
# Copy scripts
###############################################################################
COPY scripts/ /block-diff/scripts/

###############################################################################
# Default
###############################################################################
WORKDIR /block-diff/scripts
CMD ["/bin/bash"]
