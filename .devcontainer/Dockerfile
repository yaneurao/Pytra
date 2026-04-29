# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ARG DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        apt-transport-https \
        build-essential \
        ca-certificates \
        clang \
        cmake \
        curl \
        file \
        git \
        gnupg \
        golang-go \
        less \
        lua5.4 \
        luarocks \
        make \
        mono-complete \
        ninja-build \
        nodejs \
        npm \
        openjdk-17-jdk-headless \
        php-cli \
        php-mbstring \
        pkg-config \
        ripgrep \
        ruby-full \
        rustc \
        cargo \
        unzip \
        zip; \
    update-alternatives --install /usr/bin/lua lua /usr/bin/lua5.4 54; \
    update-alternatives --install /usr/bin/luac luac /usr/bin/luac5.4 54; \
    install -d -m 0755 /opt/pytra-setup; \
    curl -fsSL https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
        -o /opt/pytra-setup/packages-microsoft-prod.deb; \
    dpkg -i /opt/pytra-setup/packages-microsoft-prod.deb; \
    rm -rf /opt/pytra-setup; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        dotnet-sdk-8.0 \
        powershell; \
    npm install -g typescript; \
    python3 -m pip install --no-cache-dir --upgrade pip pytest; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/* /root/.cache /root/.npm
