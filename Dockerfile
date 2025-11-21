# syntax=docker/dockerfile:1

FROM rust:1.91-slim-bookworm

ARG MDBOOK_VERSION=0.4.52
ARG MERMAID_VERSION=0.16.2

# Create an unprivileged user that will own the working tree.
RUN useradd --create-home --shell /bin/bash mdbookuser

WORKDIR /book

COPY book.toml .
COPY theme ./theme

# Install basic tooling required for building mdBook and running health checks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install mdBook and the Mermaid preprocessor with matching versions.
RUN cargo install --locked --force --root /usr/local mdbook --version ${MDBOOK_VERSION} \
    && cargo install --locked --force --root /usr/local mdbook-mermaid --version ${MERMAID_VERSION}

# Ensure the non-root user can access /book.
RUN chown -R mdbookuser:mdbookuser /book

USER mdbookuser

RUN mdbook-mermaid install

ENTRYPOINT ["mdbook"]

HEALTHCHECK CMD curl --fail http://localhost:3000 || exit 1
