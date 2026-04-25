#!/usr/bin/env bash
# build-programs.sh — сборка Anchor-программ в Docker
# Путь: /opt/docker/chain-prod/bin/build-programs.sh
set -eu

ROOT_DIR="/opt/docker/chain-prod"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
BUILDER_IMAGE="gdm-solana-builder:latest"
BUILDER_DOCKERFILE="${ROOT_DIR}/Dockerfile.builder"

if [ -f "${ROOT_DIR}/gdm_solana_programs/Cargo.toml" ]; then
  SRC_DIR="${ROOT_DIR}/gdm_solana_programs"
else
  FOUND=$(find /opt/docker -name "Cargo.toml" -path "*/gdm_solana_programs/*" 2>/dev/null | head -1)
  if [ -n "${FOUND}" ]; then
    SRC_DIR="$(dirname "${FOUND}")"
  else
    echo "[error] gdm_solana_programs not found"
    exit 1
  fi
fi

echo "=== GDM Solana — BUILD PROGRAMS ==="
echo "[*] source:    ${SRC_DIR}"
echo "[*] artifacts: ${ARTIFACTS_DIR}"

echo "[*] ensuring artifacts dir..."
mkdir -p "${ARTIFACTS_DIR}"

echo "[*] building Docker builder image..."
docker build -f "${BUILDER_DOCKERFILE}" -t "${BUILDER_IMAGE}" "${ROOT_DIR}"

echo "[*] running SBF build inside builder container..."
docker run --rm \
  -v "${SRC_DIR}:/workspace" \
  -v "${ARTIFACTS_DIR}:/artifacts" \
  -w /workspace \
  "${BUILDER_IMAGE}" \
  bash -lc '
    set -e
    export PATH=/opt/cargo/bin:/opt/solana/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    export CARGO=/opt/cargo/bin/cargo

    PT_HOME=/root/.cache/solana/v1.41/platform-tools/rust
    OUR_SRC=/opt/cargo/registry/src/index.crates.io-1949cf8c6b5b557f
    PT_REG=index.crates.io-6f17d22bba15001f
    SBF=/opt/solana/bin/cargo-build-sbf

    echo "[builder] cargo:           $(cargo --version)"
    echo "[builder] rustc:           $(rustc --version)"
    echo "[builder] cargo-build-sbf: $(${SBF} --version | head -1)"
    echo ""

    mkdir -p ${PT_HOME}/registry/src/${PT_REG}
    mkdir -p ${PT_HOME}/registry/cache/${PT_REG}
    mkdir -p ${PT_HOME}/registry/index/${PT_REG}

    rm -rf ${PT_HOME}/registry/src/${PT_REG}/*
    cp -r ${OUR_SRC}/. ${PT_HOME}/registry/src/${PT_REG}/
    cp -r /opt/cargo/registry/cache/index.crates.io-1949cf8c6b5b557f/. ${PT_HOME}/registry/cache/${PT_REG}/ 2>/dev/null || true
    cp -r /opt/cargo/registry/index/index.crates.io-1949cf8c6b5b557f/. ${PT_HOME}/registry/index/${PT_REG}/

    find ${PT_HOME}/registry -name "toml_datetime-1*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "toml_parser*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "blake3-1.[6789]*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "blake3-2.*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "block-buffer-0.1[1-9]*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "block-buffer-0.12*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "crypto-common-0.2*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "cpufeatures-0.3*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "borsh-1.[3456789]*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "borsh-derive-1.[3456789]*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "proc-macro-crate-3*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "toml_edit-0.2[1-9]*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "winnow-1*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "wasip2-1*" -exec rm -rf {} \; 2>/dev/null || true
    find ${PT_HOME}/registry -name "wit-bindgen-0.5[1-9]*" -exec rm -rf {} \; 2>/dev/null || true

    cd /workspace
    find . -name "Cargo.lock" -delete

    /opt/cargo/bin/cargo fetch >/dev/null 2>&1
    /opt/cargo/bin/cargo update -p borsh@1.6.1 --precise 1.2.1 >/dev/null 2>&1 || true
    /opt/cargo/bin/cargo update -p blake3 --precise 1.5.0 >/dev/null 2>&1 || true
    /opt/cargo/bin/cargo update -p block-buffer@0.12.0 --precise 0.10.4 >/dev/null 2>&1 || true
    /opt/cargo/bin/cargo update -p crypto-common --precise 0.1.6 >/dev/null 2>&1 || true
    /opt/cargo/bin/cargo update -p unicode-segmentation@1.13.2 --precise 1.12.0 >/dev/null 2>&1 || true
    /opt/cargo/bin/cargo update -p indexmap@2.13.1 --precise 2.2.6 >/dev/null 2>&1 || true
    /opt/cargo/bin/cargo update -p hashbrown@0.14.5 --precise 0.14.3 >/dev/null 2>&1 || true

    sed -i "s/^version = 4$/version = 3/" Cargo.lock

    CARGO_HOME=${PT_HOME} CARGO=/opt/cargo/bin/cargo ${SBF} \
      --manifest-path programs/contract_state_program/Cargo.toml \
      -- --offline --frozen

    CARGO_HOME=${PT_HOME} CARGO=/opt/cargo/bin/cargo ${SBF} \
      --manifest-path programs/document_verification_program/Cargo.toml \
      -- --offline --frozen

    cp target/deploy/contract_state_program.so /artifacts/contract_state.so
    cp target/deploy/document_verification_program.so /artifacts/document_verification.so

    echo "[builder] artifacts:"
    ls -l /artifacts
  '

echo ""
echo "[*] verifying artifacts on host..."
OK=0
for SO in contract_state.so document_verification.so; do
  if [ -f "${ARTIFACTS_DIR}/${SO}" ]; then
    SIZE=$(du -h "${ARTIFACTS_DIR}/${SO}" | cut -f1)
    echo "  [ok] ${SO}  (${SIZE})"
    OK=$((OK + 1))
  else
    echo "  [missing] ${SO}"
  fi
done

if [ "${OK}" -eq 2 ]; then
  echo ""
  echo "=== BUILD SUCCESS ==="
  echo "Next: docker exec -it gdm-solana-tools sh -lc '\''sh /solana/bin/deploy-programs.sh'\''"
else
  echo "[error] build incomplete — ${OK}/2 artifacts"
  exit 1
fi
