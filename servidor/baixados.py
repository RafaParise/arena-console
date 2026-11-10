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

Ampliado em 10/11/2026 (pedido do Rafael: "identificar os jogos (roms) .iso e qualquer rom ou bios de qualquer
jogo em qualquer lugar ... e poder mover para a pasta correta"):
  - alem dos downloads, as pastas que a pessoa escolher (ate 5; no celular, pode ser o armazenamento inteiro), com
    ate 3 niveis de subpasta, sem olhar a pasta do proprio ARENA nem as do sistema;
  - as BIOS: o arquivo com a marca (md5) ou o nome de uma BIOS conhecida (servidor\bios.py) aparece a parte, e
    "Levar para o ARENA" o poe na pasta BIOS, que o ARENA ja arruma sozinho (cada uma no lugar do console dela).

So biblioteca padrao.
"""
import os
import shutil
import subprocess
import zipfile

import bios
import identificador
import plataforma as plataforma_do_sistema

LIMITE_DE_ARQUIVOS = 300          # pasta Download enorme nao trava a tela
MENOR_ARQUIVO = 256               # bytes: arquivo menor que isso nao e' jogo
NIVEIS_DOS_DOWNLOADS = 1          # a pasta de downloads e uma subpasta
NIVEIS_DAS_ESCOLHIDAS = 3         # a pasta que a pessoa escolheu e tres niveis abaixo
MAXIMO_DE_PASTAS_ESCOLHIDAS = 5
# Nunca se olha dentro destas (ao procurar numa pasta grande, como o celular inteiro): as do sistema e as dos apps.
PASTAS_PULADAS = {"android", "$recycle.bin", "system volume information", "windows", "program files",
                  "program files (x86)", "programdata", "appdata", "node_modules", "lost+found"}


def pastas_escolhidas(lista):
    """As pastas que a pessoa escolheu (config "pastas_de_procura"), so as que existem, sem repetir."""
    vistas, pastas = set(), []
    for pasta in lista or []:
        if not isinstance(pasta, str) or not pasta.strip():
            continue
        real = os.path.realpath(os.path.expanduser(pasta.strip()))
        if os.path.isdir(real) and real not in vistas:
            vistas.add(real)
            pastas.append(real)
    return pastas[:MAXIMO_DE_PASTAS_ESCOLHIDAS]


def conferir_pasta_escolhida(pasta, pasta_do_arena):
    """A pasta que a pessoa quer acrescentar: devolve o caminho real ou levanta NaoPode com o porque."""
    texto = str(pasta or "").strip().strip('"')
    if not texto:
        raise NaoPode("Escreva o caminho da pasta (por exemplo, D:\\Jogos).")
    real = os.path.realpath(os.path.expanduser(texto))
    if not os.path.isabs(real) or not os.path.isdir(real):
        raise NaoPode("Não achei essa pasta. Confira o caminho (copie da barra de endereço do Explorador).")
    arena = os.path.realpath(pasta_do_arena)
    if _dentro(real, arena):
        raise NaoPode("Essa pasta é do próprio ARENA: os jogos dela já estão na lista.")
    return real


def _dentro(caminho, pasta):
    try:
        return os.path.commonpath([caminho, pasta]) == pasta
    except ValueError:                      # discos diferentes no Windows
        return False


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


def _caminhar(pasta, niveis, ignorar):
    """(atual, arquivos) de 'pasta' e de ate 'niveis' de subpasta, sem as escondidas, as do sistema e as de 'ignorar'
    (a pasta do ARENA: os jogos dela ja estao na lista)."""
    for atual, subpastas, arquivos in os.walk(pasta):
        nivel = 0 if atual == pasta else os.path.relpath(atual, pasta).count(os.sep) + 1
        if nivel >= niveis:
            subpastas[:] = []
        subpastas[:] = [s for s in subpastas if not s.startswith(".") and s.lower() not in PASTAS_PULADAS
                        and not any(_dentro(os.path.realpath(os.path.join(atual, s)), i) for i in ignorar)]
        yield atual, arquivos


def procurar(plataformas, pastas=None, escolhidas=(), ignorar=(), bios_achadas=None):
    """Os jogos nas pastas de download (e nas 'escolhidas' pela pessoa): [{arquivo, nome, tamanho, sugestao,
    opcoes:[{id, nome}]}], do mais novo para o mais antigo. Com 'bios_achadas' (uma lista), as BIOS reconhecidas vao
    para ela ([{arquivo, nome, tamanho, bios, certeza}]) e saem da lista de jogos."""
    por_extensao = _consoles_da_extensao(plataformas)
    ignorar = [os.path.realpath(i) for i in ignorar]
    achados, bios_vistas = [], []
    roteiro = [(p, NIVEIS_DOS_DOWNLOADS) for p in (pastas if pastas is not None else pastas_de_baixados())]
    roteiro += [(p, NIVEIS_DAS_ESCOLHIDAS) for p in escolhidas]
    vistos = set()
    for pasta, niveis in roteiro:
        for atual, arquivos in _caminhar(pasta, niveis, ignorar):
            for nome in arquivos:
                if nome.startswith(".") or len(achados) >= LIMITE_DE_ARQUIVOS:
                    continue
                caminho = os.path.join(atual, nome)
                if caminho in vistos:
                    continue                # a pasta escolhida pode conter a de downloads
                vistos.add(caminho)
                extensao = os.path.splitext(nome)[1].lower()
                try:
                    estado = os.stat(caminho)
                except OSError:
                    continue
                if estado.st_size < MENOR_ARQUIVO:
                    continue
                if bios_achadas is not None:
                    reconhecida = bios.reconhecer_arquivo_solto(caminho)
                    if reconhecida:
                        bios_vistas.append(dict(reconhecida, arquivo=caminho, nome=nome,
                                                tamanho=tamanho_legivel(estado.st_size)))
                        continue
                candidatos = por_extensao.get(extensao)
                if not candidatos:
                    continue
                achados.append((estado.st_mtime, caminho, nome, estado.st_size, extensao, candidatos))
    if bios_achadas is not None:
        bios_achadas.extend(bios_vistas)
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


def levar(caminho, plataforma_id, plataformas, pasta_jogos, pastas=None, prateleira=None):
    """Move o arquivo baixado para jogos\\pessoais\\<console> (ou para 'prateleira'\\<console>: a pasta ARENA-jogos
    do cartao SD, no celular). Devolve o destino. So aceita arquivo de dentro das pastas de download e com a
    extensao do console escolhido."""
    real = _conferir_origem(caminho, pastas)
    plataforma = next((p for p in plataformas if p["id"] == plataforma_id), None)
    if not plataforma:
        raise NaoPode("Escolha de qual console é o jogo.")
    extensao = os.path.splitext(real)[1].lower()
    if extensao not in [e.lower() for e in plataforma.get("extensoes", [])]:
        raise NaoPode("O %s não abre arquivo %s. Escolha outro console." % (plataforma["nome"], extensao))
    prateleira = os.path.join(prateleira or os.path.join(pasta_jogos, "pessoais"), plataforma["pasta"])
    destino = os.path.join(prateleira, os.path.basename(real))
    if os.path.exists(destino):
        raise NaoPode("Já existe um jogo com esse nome no %s." % plataforma["nome"])
    os.makedirs(prateleira, exist_ok=True)
    return _mover(real, destino)


def _conferir_origem(caminho, pastas):
    """O arquivo tem de estar numa das pastas onde o ARENA procurou (downloads e escolhidas): a tela nunca move um
    arquivo de outro lugar. Devolve o caminho real."""
    real = os.path.realpath(str(caminho or ""))
    permitidas = pastas if pastas is not None else pastas_de_baixados()
    if not any(_dentro(real, p) for p in permitidas):
        raise NaoPode("Esse arquivo não está nas pastas onde o ARENA procurou. Procure de novo.")
    if not os.path.isfile(real):
        raise NaoPode("O arquivo não está mais lá. Procure de novo.")
    return real


def levar_bios(caminho, pasta_bios, pastas=None):
    """Move a BIOS achada para a pasta BIOS do ARENA (quem a poe no lugar do console e' o bios.organizar, logo
    depois). Devolve o destino. Se ja houver um arquivo com esse nome la, o novo ganha um numero no nome: nenhuma
    BIOS e' apagada nem trocada."""
    real = _conferir_origem(caminho, pastas)
    if not bios.reconhecer_arquivo_solto(real):
        raise NaoPode("Esse arquivo não parece uma BIOS que o ARENA conhece.")
    os.makedirs(pasta_bios, exist_ok=True)
    base, extensao = os.path.splitext(os.path.basename(real))
    destino = os.path.join(pasta_bios, base + extensao)
    numero = 2
    while os.path.exists(destino):
        destino = os.path.join(pasta_bios, "%s (%d)%s" % (base, numero, extensao))
        numero += 1
    return _mover(real, destino)


def _mover(real, destino):
    """Troca o arquivo de lugar sem nunca deixar um pedaco com o nome certo."""
    try:
        os.rename(real, destino)                  # mesmo disco: so troca de lugar, na hora
        return destino
    except OSError:
        pass
    # Outro disco (no celular: Download na memoria -> ARENA-jogos no cartao SD). Antes, o shutil.move copiava direto no
    # nome final: com o cartao cheio ou retirado no meio, sobrava um jogo cortado com o nome certo, que nao abria e
    # impedia a nova tentativa (auditoria 6, DAD6-05). Agora: copia com outro nome, confere o tamanho e so entao troca
    # o nome e apaga o original.
    parcial = destino + ".arena-parcial"
    try:
        shutil.copyfile(real, parcial)
        with open(parcial, "rb+") as arquivo:
            os.fsync(arquivo.fileno())
        if os.path.getsize(parcial) != os.path.getsize(real):
            raise NaoPode("A cópia não chegou inteira (o cartão está cheio ou saiu?). O arquivo ficou nos downloads.")
        os.replace(parcial, destino)
    except OSError as falha:
        raise NaoPode("Não consegui levar o arquivo (%s). Ele ficou nos downloads."
                      % (getattr(falha, "strerror", None) or falha))
    finally:
        if os.path.exists(parcial):
            try:
                os.remove(parcial)
            except OSError:
                pass
    try:
        os.remove(real)
    except OSError:
        pass                                      # o jogo ja esta no ARENA; o download sobra para o aluno apagar
    return destino
