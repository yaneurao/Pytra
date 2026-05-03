# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ARG DEBIAN_FRONTEND=noninteractive
ARG DART_VERSION=3.11.5
ARG POWERSHELL_VERSION=7.6.1
ARG ZIG_VERSION=0.16.0

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN set -eux; \
    rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn*.list; \
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
        xz-utils \
        zip; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
        amd64) dart_arch="x64"; zig_arch="x86_64-linux" ;; \
        arm64) dart_arch="arm64"; zig_arch="aarch64-linux" ;; \
        *) echo "unsupported Dart/Zig devcontainer architecture: $arch" >&2; exit 1 ;; \
    esac; \
    install -d -m 0755 /opt/pytra-setup /opt/dart /opt/zig; \
    curl -fsSL "https://storage.googleapis.com/dart-archive/channels/stable/release/${DART_VERSION}/sdk/dartsdk-linux-${dart_arch}-release.zip" \
        -o /opt/pytra-setup/dart-sdk.zip; \
    unzip -q /opt/pytra-setup/dart-sdk.zip -d /opt/dart; \
    ln -sf /opt/dart/dart-sdk/bin/dart /usr/local/bin/dart; \
    curl -fsSL "https://ziglang.org/download/${ZIG_VERSION}/zig-${zig_arch}-${ZIG_VERSION}.tar.xz" \
        -o /opt/pytra-setup/zig.tar.xz; \
    tar -xJf /opt/pytra-setup/zig.tar.xz -C /opt/zig --strip-components=1; \
    ln -sf /opt/zig/zig /usr/local/bin/zig; \
    dart --version; \
    zig version; \
    rm -rf /opt/pytra-setup

RUN set -eux; \
    install -d -m 0755 /opt/pytra-setup; \
    curl -fsSL https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
        -o /opt/pytra-setup/packages-microsoft-prod.deb; \
    dpkg -i /opt/pytra-setup/packages-microsoft-prod.deb; \
    apt-get update; \
    arch="$(dpkg --print-architecture)"; \
    if [[ "$arch" == "amd64" ]]; then \
        apt-get install -y --no-install-recommends dotnet-sdk-8.0 powershell; \
    else \
        curl -fsSL https://dot.net/v1/dotnet-install.sh -o /opt/pytra-setup/dotnet-install.sh; \
        bash /opt/pytra-setup/dotnet-install.sh \
            --channel 8.0 \
            --architecture arm64 \
            --install-dir /usr/share/dotnet; \
        ln -sf /usr/share/dotnet/dotnet /usr/local/bin/dotnet; \
        install -d -m 0755 /opt/microsoft/powershell/7; \
        curl -fsSL "https://github.com/PowerShell/PowerShell/releases/download/v${POWERSHELL_VERSION}/powershell-${POWERSHELL_VERSION}-linux-arm64.tar.gz" \
            -o /opt/pytra-setup/powershell.tar.gz; \
        tar -xzf /opt/pytra-setup/powershell.tar.gz -C /opt/microsoft/powershell/7; \
        chmod 0755 /opt/microsoft/powershell/7/pwsh; \
        ln -sf /opt/microsoft/powershell/7/pwsh /usr/local/bin/pwsh; \
    fi; \
    rm -rf /opt/pytra-setup /var/lib/apt/lists/*

RUN set -eux; \
    npm install -g typescript; \
    python3 -m pip install --no-cache-dir --upgrade pip pytest; \
    apt-get autoremove -y; \
    rm -rf /root/.cache /root/.npm
