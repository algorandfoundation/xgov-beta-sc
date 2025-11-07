# syntax=docker/dockerfile:1

FROM rust:1.82-slim-bullseye

ARG MDBOOK_VERSION=0.4.52

# Create an unprivileged user that will own the working tree.
RUN useradd --create-home --shell /bin/bash mdbookuser

WORKDIR /book

# Install basic tooling required for building mdBook and running health checks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# Install mdBook and the Mermaid preprocessor with matching versions.
RUN cargo install --locked --force --root /usr/local mdbook --version ${MDBOOK_VERSION} \
    && cargo install --locked --force --root /usr/local mdbook-mermaid

# Copy book sources and theme (include root-level includes referenced from docs).
COPY docs docs
COPY book.toml .
COPY theme ./theme
COPY SECURITY.md .
COPY LICENSE .

# Ensure the non-root user can access /book.
RUN chown -R mdbookuser:mdbookuser /book

USER mdbookuser

RUN mdbook-mermaid install

ENTRYPOINT ["mdbook"]

HEALTHCHECK CMD curl --fail http://localhost:3000 || exit 1
