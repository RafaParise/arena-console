# Política de segurança

## Versões com suporte

Só a versão mais recente recebe correções de segurança. Hoje:

| Versão | Suporte |
|---|---|
| 2026.10.11 | Sim |
| Anteriores | Não — atualize pelo pacote de atualização (guia 6) |

## Como relatar uma falha de segurança

**Não abra uma issue pública** para falha de segurança. Use o relato
particular do GitHub: na aba **Security** do repositório, clique em
**Report a vulnerability** ("Relatar uma vulnerabilidade"). A mensagem chega
só ao responsável pelo projeto.

Conte, se possível:

- a versão do ARENA e do Windows;
- o que um atacante consegue fazer e de onde (o mesmo computador, outro
  computador da rede, uma página da internet);
- o passo a passo para reproduzir, com o menor exemplo possível.

O projeto é mantido por um professor só: a primeira resposta pode levar
alguns dias. Falha confirmada é corrigida na versão seguinte, e quem
relatou recebe o crédito no relatório, se quiser.

## Como o ARENA se protege (para quem vai testar)

- O servidor do ARENA escuta só neste computador, em `127.0.0.1:8777`.
- Com a opção **"Aceitar conexões da rede"** ligada (para jogar com os
  colegas), só as 8 rotas que a partida a dois e a sincronização dos
  recordes precisam aceitam pedidos de outro computador (a lista
  `ROTAS_REDE_EXTERNA`, em `servidor/arena.py`). Todo o resto recusa.
- Pedido que muda alguma coisa precisa vir como JSON (`Content-Type:
  application/json`): uma página aberta no navegador não consegue mandar
  esse pedido escondido (proteção contra CSRF).
- O servidor confere o cabeçalho `Host` e recusa nome que não seja deste
  computador (proteção contra DNS rebinding).
- Caminhos de arquivo que chegam pela rede são conferidos: nada fora das
  pastas permitidas (proteção contra travessia de pasta).
- O ARENA não pede senha de administrador, não instala nada, não manda
  dados para fora e não grava vídeo nem transmite.

## Fora do escopo

- Falhas dos emuladores incluídos (RetroArch, PCSX2, Dolphin, RPCS3, Xenia):
  relate ao projeto de cada um (os links estão em [TERCEIROS.md](TERCEIROS.md)).
- Jogos, BIOS e firmware: o projeto não distribui esses arquivos.
