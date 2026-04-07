FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV RUSTUP_HOME=/opt/rustup
ENV CARGO_HOME=/opt/cargo
ENV PATH=/opt/cargo/bin:/opt/solana/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl bash bzip2 pkg-config libssl-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Rust (новый — только для fetch)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --no-modify-path --profile minimal --default-toolchain 1.85.0

# Solana (внутри — rustc 1.75)
RUN mkdir -p /tmp/solana-dl \
    && curl -fL https://github.com/solana-labs/solana/releases/download/v1.18.26/solana-release-x86_64-unknown-linux-gnu.tar.bz2 \
        -o /tmp/solana-dl/solana.tar.bz2 \
    && tar -xjf /tmp/solana-dl/solana.tar.bz2 -C /tmp/solana-dl \
    && mv /tmp/solana-dl/solana-release /opt/solana \
    && rm -rf /tmp/solana-dl

# Фикс PATH для bash -lc
RUN ln -sf /opt/cargo/bin/cargo /usr/local/bin/cargo \
 && ln -sf /opt/solana/bin/cargo-build-sbf /usr/local/bin/cargo-build-sbf \
 && ln -sf /opt/solana/bin/solana /usr/local/bin/solana

# Прогрев platform-tools
RUN mkdir -p /tmp/w/src \
 && printf '[package]\nname="w"\nversion="0.1.0"\nedition="2021"\n[lib]\ncrate-type=["cdylib"]\n[dependencies]\n' > /tmp/w/Cargo.toml \
 && echo 'pub fn f(){}' > /tmp/w/src/lib.rs \
 && cd /tmp/w \
 && /opt/cargo/bin/cargo generate-lockfile || true \
 && sed -i "s/^version = 4$/version = 3/" Cargo.lock || true \
 && CARGO=/opt/cargo/bin/cargo /opt/solana/bin/cargo-build-sbf || true \
 && rm -rf /tmp/w

# Anchor deps preload
RUN mkdir -p /tmp/ac/programs/d/src \
 && printf '[workspace]\nmembers=["programs/d"]\nresolver="2"\n' > /tmp/ac/Cargo.toml \
 && printf '[package]\nname="d"\nversion="0.1.0"\nedition="2021"\n[lib]\ncrate-type=["cdylib"]\n[dependencies]\nanchor-lang="=0.29.0"\n' > /tmp/ac/programs/d/Cargo.toml \
 && echo 'use anchor_lang::prelude::*; declare_id!("11111111111111111111111111111111"); #[program] pub mod d { use super::*; }' > /tmp/ac/programs/d/src/lib.rs \
 && cd /tmp/ac && /opt/cargo/bin/cargo fetch && rm -rf /tmp/ac

# 🔑 ВСЕ критические pins
RUN mkdir -p /tmp/pins/src \
 && printf '[package]\nname="pins"\nversion="0.1.0"\nedition="2021"\n\n[[bin]]\nname="pins"\npath="src/main.rs"\n\n[dependencies]\n\
borsh="=1.2.1"\n\
borsh-derive="=1.2.1"\n\
blake3="=1.5.0"\n\
block-buffer="=0.10.4"\n\
crypto-common="=0.1.6"\n\
toml_datetime="=0.6.3"\n\
toml_edit="=0.20.2"\n\
winnow="=0.5.40"\n\
proc-macro-crate="=2.0.2"\n\
syn_derive="=0.1.8"\n\
proc-macro-error="=1.0.4"\n\
proc-macro-error-attr="=1.0.4"\n\
unicode-segmentation="=1.12.0"\n\
indexmap="=2.2.6"\n\
hashbrown="=0.14.3"\n\
' > /tmp/pins/Cargo.toml \
 && echo 'fn main(){}' > /tmp/pins/src/main.rs \
 && cd /tmp/pins && /opt/cargo/bin/cargo fetch && rm -rf /tmp/pins

WORKDIR /workspace
CMD ["bash"]
