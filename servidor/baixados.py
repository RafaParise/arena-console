# -*- coding: utf-8 -*-
r"""Achar os jogos que a pessoa baixou e leva-los para a prateleira certa.

Pedido do Rafael (22/10/2026, auditoria 4): "nao tem jogos na pasta, precisa
ter um passo a passo simples de onde adicionar o jogo ... ou um
identificador que identifica roms no celular baixadas e que pede permissao
para mover o arquivo para pasta correta".

O ARENA olha SO as pastas de download deste aparelho (no Windows e no Linux,
a pasta Downloads; no Android, a Download e as de documentos do WhatsApp e do
Telegram), com no maximo um nivel de subpasta, e SO os arquivos com a
extensao de algum console do consoles.json. Nada sai do lugar sem a pessoa
pedir: a tela mostra o que achou, com o console sugerido, e cada jogo so vai
para jogos\pessoais\<console> quando a pessoa toca em "Levar para o ARENA".

Quando a extensao serve a varios consoles (.iso, .chd, .bin, .zip...), o
console sai do conteudo (servidor\identificador.py, o mesmo do indexador)
ou, no .zip, do arquivo de dentro; se nem assim der, a pessoa escolhe.

So biblioteca padrao.
"""
import os
import shutil
import subprocess
import zipfile

import identificador
import plataforma as plataforma_do_sistema

LIMITE_DE_ARQUIVOS = 300          # pasta Download enorme nao trava a tela
MENOR_ARQUIVO = 256               # bytes: arquivo menor que isso nao e' jogo


def pastas_de_baixados():
    """As pastas de download deste aparelho que existem, sem repetir."""
    candidatas = []
    if plataforma_do_sistema.ANDROID:
        raiz = "/storage/emulated/0"
        candidatas += [os.path.join(raiz, "Download"),
                       os.path.join(raiz, "Android", "media", "com.whatsapp", "WhatsApp", "Media",
                                    "WhatsApp Documents"),
                       os.path.join(raiz, "Telegram", "Telegram Documents")]
    else:
        casa = os.path.expanduser("~")
        if plataforma_do_sistema.LINUX:
            try:
                saida = subprocess.run(["xdg-user-dir", "DOWNLOAD"], capture_output=True, text=True, timeout=5)
                if saida.returncode == 0 and saida.stdout.strip():
                    candidatas.append(saida.stdout.strip())
            except (OSError, subprocess.SubprocessError):
                pass
            candidatas.append(os.path.join(casa, "Transferências"))
        candidatas.append(os.path.join(casa, "Downloads"))
    vistas, pastas = set(), []
    for pasta in candidatas:
        real = os.path.realpath(pasta)
        if os.path.isdir(real) and real not in vistas:
            vistas.add(real)
            pastas.append(real)
    return pastas


def _consoles_da_extensao(plataformas):
    por_extensao = {}
    for p in plataformas:
        for extensao in p.get("extensoes", []):
            por_extensao.setdefault(extensao.lower(), []).append(p)
    return por_extensao


def _de_dentro_do_zip(caminho, por_extensao):
    """O console pelo arquivo de dentro do .zip: um jogo de cartucho zipado
    tem UM arquivo, com a extensao do console. Devolve os consoles, ou []."""
    try:
        with zipfile.ZipFile(caminho) as pacote:
            nomes = [n for n in pacote.namelist() if not n.endswith("/")]
    except (OSError, zipfile.BadZipFile, ValueError):
        return []
    if len(nomes) != 1:
        return []
    extensao = os.path.splitext(nomes[0])[1].lower()
    if extensao == ".zip":
        return []
    return por_extensao.get(extensao, [])


def _sugestao(caminho, extensao, candidatos, por_extensao):
    """(id sugerido ou None, lista de opcoes) para este arquivo."""
    if len(candidatos) == 1:
        return candidatos[0]["id"], candidatos
    if extensao == ".zip":
        de_dentro = _de_dentro_do_zip(caminho, por_extensao)
        if len(de_dentro) == 1:
            return de_dentro[0]["id"], candidatos
    try:
        achado = identificador.identificar(caminho, [c["id"] for c in candidatos])
    except Exception:            # noqa: BLE001 -- ler o arquivo e' ajuda, nunca derruba
        achado = None
    if achado and any(c["id"] == achado for c in candidatos):
        return achado, candidatos
    return None, candidatos


def procurar(plataformas, pastas=None):
    """Os jogos nas pastas de download: [{arquivo, nome, tamanho, sugestao,
    opcoes:[{id, nome}]}], do mais novo para o mais antigo."""
    por_extensao = _consoles_da_extensao(plataformas)
    achados = []
    for pasta in (pastas if pastas is not None else pastas_de_baixados()):
        for atual, subpastas, arquivos in os.walk(pasta):
            nivel = 0 if atual == pasta else os.path.relpath(atual, pasta).count(os.sep) + 1
            if nivel >= 1:
                subpastas[:] = []          # so um nivel de subpasta
            subpastas[:] = [s for s in subpastas if not s.startswith(".")]
            for nome in arquivos:
                extensao = os.path.splitext(nome)[1].lower()
                candidatos = por_extensao.get(extensao)
                if not candidatos or nome.startswith("."):
                    continue
                caminho = os.path.join(atual, nome)
                try:
                    estado = os.stat(caminho)
                except OSError:
                    continue
                if estado.st_size < MENOR_ARQUIVO:
                    continue
                achados.append((estado.st_mtime, caminho, nome, estado.st_size, extensao, candidatos))
                if len(achados) >= LIMITE_DE_ARQUIVOS:
                    break
    achados.sort(key=lambda item: item[0], reverse=True)
    lista = []
    for _hora, caminho, nome, tamanho, extensao, candidatos in achados:
        sugestao, opcoes = _sugestao(caminho, extensao, candidatos, por_extensao)
        lista.append({"arquivo": caminho, "nome": nome, "tamanho": tamanho_legivel(tamanho),
                      "sugestao": sugestao,
                      "opcoes": [{"id": c["id"], "nome": c["nome"]} for c in opcoes]})
    return lista


def tamanho_legivel(tamanho):
    """'2 KB', '7,5 MB', '1,4 GB' (jogo de cartucho tem poucos KB)."""
    if tamanho < 1048576:
        return "%d KB" % max(1, round(tamanho / 1024.0))
    if tamanho < 1073741824:
        return ("%.1f MB" % (tamanho / 1048576.0)).replace(".", ",")
    return ("%.1f GB" % (tamanho / 1073741824.0)).replace(".", ",")


class NaoPode(Exception):
    """O pedido nao pode ser feito; a mensagem diz o porque e o que fazer."""


def levar(caminho, plataforma_id, plataformas, pasta_jogos, pastas=None):
    """Move o arquivo baixado para jogos\\pessoais\\<console>. Devolve o
    destino. So aceita arquivo de dentro das pastas de download e com a
    extensao do console escolhido."""
    real = os.path.realpath(str(caminho or ""))
    permitidas = pastas if pastas is not None else pastas_de_baixados()
    if not any(os.path.commonpath([real, p]) == p for p in permitidas if os.path.splitdrive(real)[0].lower()
               == os.path.splitdrive(p)[0].lower()):
        raise NaoPode("Esse arquivo não está na pasta de downloads. Procure os jogos baixados de novo.")
    if not os.path.isfile(real):
        raise NaoPode("O arquivo não está mais lá. Procure os jogos baixados de novo.")
    plataforma = next((p for p in plataformas if p["id"] == plataforma_id), None)
    if not plataforma:
        raise NaoPode("Escolha de qual console é o jogo.")
    extensao = os.path.splitext(real)[1].lower()
    if extensao not in [e.lower() for e in plataforma.get("extensoes", [])]:
        raise NaoPode("O %s não abre arquivo %s. Escolha outro console." % (plataforma["nome"], extensao))
    prateleira = os.path.join(pasta_jogos, "pessoais", plataforma["pasta"])
    destino = os.path.join(prateleira, os.path.basename(real))
    if os.path.exists(destino):
        raise NaoPode("Já existe um jogo com esse nome no %s." % plataforma["nome"])
    os.makedirs(prateleira, exist_ok=True)
    shutil.move(real, destino)
    return destino
