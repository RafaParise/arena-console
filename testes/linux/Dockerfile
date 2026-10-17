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
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates procps xvfb xauth x11-utils \
        libgl1 libgl1-mesa-dri libegl1 libgles2 libvulkan1 mesa-vulkan-drivers \
        libasound2t64 libpulse0 libglib2.0-0t64 libfontconfig1 libfreetype6 libxkbcommon0 \
        libudev1 libusb-1.0-0 libsdl2-2.0-0 zstd xz-utils file \
    && rm -rf /var/lib/apt/lists/*

# Um usuario comum, sem senha de administrador (o ARENA nunca pede).
RUN useradd -m -s /bin/bash aluno
USER aluno
WORKDIR /arena
