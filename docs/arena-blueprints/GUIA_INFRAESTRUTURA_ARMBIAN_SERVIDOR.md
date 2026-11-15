# Guia Técnico — Linux Armbian via MicroSD e Servidor Headless ARENA

## 1. Dual-Boot Linux ARM64 (Armbian) via Cartão MicroSD em TV Box (S905X4 / RK3588)

Permite executar Linux ARM64 (`aarch64`) completo com Docker, Tailscale e `arena-web` nativo mantendo o Android intacto na memória interna (`eMMC`).

### Gravação da Imagem Server (`ophub/amlogic-s9xxx-armbian`)
```bash
lsblk
zcat Armbian_*_server_*.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

### Ajuste do DTB na Partição `BOOT`
- **Amlogic S905X4:** Edite `uEnv.txt` apontando `FDT=` para o `.dtb` correspondente em `/dtb/amlogic/`.
- **Rockchip RK3588:** Edite `extlinux/extlinux.conf` apontando `FDT` para `/dtb/rockchip/rk3588-rock-5b.dtb` (ou placa equivalente).

### Ativação do Multi-Boot (Sem Apagar o Android)
- **Amlogic S905X4:** Com o cartão inserido e a caixa desligada, segure o botão interno de **Reset** (dentro da porta AV) por 5 segundos ao ligar a energia (ou rode `adb reboot update` com o Android ligado).
- **Rockchip RK3588:** Prioriza o slot MicroSD automaticamente no boot.
- **Regra:** Nunca execute `armbian-install` se desejar manter o Android na `eMMC`.

### Setup Inicial Pós-Login (`root` / `1234`)
```bash
apt update && apt upgrade -y
armbian-swap 1

curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

curl -fsSL https://raw.githubusercontent.com/RafaParise/arena-console/main/install.sh | bash

uname -m
ethtool eth0 | grep Speed
systemctl status arena-web
```