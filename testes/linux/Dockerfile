# O Linux dos testes do ARENA (item 13 do plano de 15/10/2026).
#
# Um Debian "limpo", como o de um aluno que acabou de instalar o Linux: so
# o que um computador comum ja tem (a tela, o som, o OpenGL e o Vulkan do
# Mesa). O Python e o RetroArch NAO vem daqui: vem do proprio ARENA (a pasta
# montada em /arena), como no pen drive. A tela e' virtual (Xvfb), para o
# RetroArch desenhar sem monitor e o teste tirar a foto.
#
# Montar (no Windows, pelo WSL):
#   "C:\Program Files\WSL\container.exe" build -t arena-linux testes\linux
# Usar: testes\teste_linux.py
FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8
# O que NAO vem aqui de proposito: a libjack (o Ubuntu 24.04 de desktop nao
# traz; o ARENA leva a vazia) e a libgomp (o ARENA leva a de reserva). A
# libgpg-error vem: todo Linux com o systemd tem (o Debian "slim" nao).
# x11-apps: o xwd, que fotografa a tela virtual; git: os testes das
# ferramentas de publicar. O libOpenGL, o harfbuzz e o fribidi vem em todo
# Linux com tela (o GTK e o Qt dependem deles), mas nao no "slim": sem eles,
# o PCSX2 (libOpenGL.so.0, libharfbuzz.so.0) e o Xenia (libfribidi.so.0) nem
# abriam no conteiner (testes\teste_linux.py, 20/10/2026).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates procps xvfb xauth x11-utils x11-apps \
        libgl1 libgl1-mesa-dri libegl1 libgles2 libvulkan1 mesa-vulkan-drivers libopengl0 \
        libasound2t64 libpulse0 libglib2.0-0t64 libfontconfig1 libfreetype6 libxkbcommon0 \
        libharfbuzz0b libfribidi0 \
        libudev1 libusb-1.0-0 libsdl2-2.0-0 libgpg-error0 zstd xz-utils file git \
    && rm -rf /var/lib/apt/lists/*

# Um usuario comum, sem senha de administrador (o ARENA nunca pede).
RUN useradd -m -s /bin/bash aluno
USER aluno
WORKDIR /arena
