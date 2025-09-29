# See here for image contents: https://github.com/devcontainers/images/tree/main/src/base-ubuntu
FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install apt-get packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends curl jq \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
