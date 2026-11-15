#!/usr/bin/env bash
set -e

echo "[ARENA-BUILD] Iniciando compilação do backend Rust para Android (aarch64)..."

rustup target add aarch64-linux-android

cd "$(dirname "$0")/../arena-web"

cargo build --target aarch64-linux-android --release

TARGET_JNI_DIR="../android/app/src/main/jniLibs/arm64-v8a"
mkdir -p "$TARGET_JNI_DIR"

cp target/aarch64-linux-android/release/libarena_web.so "$TARGET_JNI_DIR/libarena_web.so"

echo "[ARENA-BUILD] Sucesso! Binário libarena_web.so posicionado em: $TARGET_JNI_DIR"