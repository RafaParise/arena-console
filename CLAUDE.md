# CLAUDE.md: ARENA

Este arquivo é lido em toda sessão (Claude Code no computador e na nuvem,
Hermes), então **mantenha curto** e guarde aqui só o que vale sempre.
Histórico, medições e relatos de sessão vão para o commit e para `docs\`.
As pendências ficam em `docs\PENDENCIAS.md`, e a versão longa antiga deste
arquivo se recupera com `git show bfc84a0:CLAUDE.md`. O repositório é
público (`github.com/RafaParise/arena-console`): **nada de e-mail, senha,
token ou dado de aluno** (nome, nota, planilha de turma).

## O projeto

O ARENA é um lançador portátil de emuladores para a sala de aula (curso
técnico de Desenvolvimento de Sistemas, com alunos menores de idade). É
feito em **Python puro** sobre o **RetroArch** (núcleos libretro), com
emuladores externos para PS2 (PCSX2), GameCube/Wii (Dolphin), PS3 (RPCS3)
e Xbox 360 (Xenia). Roda **local**, de uma pasta ou de um pen drive, sem
instalar nada. O código também é material de aula: comentários em
português, legíveis por aluno do ensino médio. Autor: Rafael Parise Passos,
professor da rede estadual de SP.

- Caminhos aqui são relativos à raiz do repositório (no computador do
  Rafael, a pasta `arena-console`). A versão dos alunos fica ao lado, em
  `..\ARENA`, e é do Rafael: **nunca remontar.** Conserto chega lá só pelo
  `ferramentas\montar_versao_alunos.py --atualizar`.
- O ARENA distribui a ferramenta, nunca o acervo: **ROM e BIOS
  proprietária (Sony, Sega, SNK) não entram no repositório nem no pacote.**
  A exceção é o que tem licença livre: as BIOS livres
  (`servidor\bios_livres`, como o C-BIOS) e os jogos livres dos testes
  (`testes\jogos_livres`). O conferidor só os aceita pela marca da
  `lista.json` de cada pasta.
- **Gravação de vídeo e transmissão ficam desligadas de propósito, para
  proteger os dados dos alunos. Não reativar nem propor.**

## Restrições (não negociáveis)

| Restrição | O que isso obriga |
|---|---|
| Sem `pip install` | Só a biblioteca padrão; o Windows é alcançado por `ctypes` |
| Sem administrador | Nada de driver, serviço, regra de firewall ou gravação no registro. **Exceção única** (pedido do Rafael, 13/11/2026): o botão opcional **Equipamentos → Instalar o WSL**, que avisa antes e deixa o próprio Windows pedir a permissão |
| Pen drive | Caminho sempre relativo. Caminho absoluto vazando é bug de portabilidade |
| Offline | Internet é bônus, e sem ela tudo degrada com uma mensagem clara |
| Máquina-alvo | Celeron N5100 (4 threads, **sem AVX**), 7,7 GB e Intel UHD integrada (`docs\MAQUINA-ALVO.md`). O desempenho se julga nela, não no Ryzen do Rafael |

## Python

- Python **3.13.15 x64 embutido** em `servidor\python\`. Script e teste
  rodam com `servidor\python\python.exe`.
- O `ARENA.bat` abre o `servidor\arena.py` (servidor HTTP em
  `127.0.0.1:8777` e banco `dados\arena.db`), que abre a tela de
  `launcher\` (`index.html` e `app.js`, sem framework) numa janela do
  Edge/Chrome. O `ARENA.bat` reabre o servidor que cai (até 3 vezes).
- Módulos principais em `servidor\`:
  - `graficos.py`: opções por núcleo e configuração dos emuladores externos.
  - `hardware.py`: processador, placa, disco e motor de vídeo.
  - `processos.py`: prioridade e energia dos processos.
  - Os demais: `controles.py`, `indexador.py`, `bios.py`, `arrumar.py` e
    `motivo_do_erro.py`.
- Dados em `servidor\`:
  - `consoles.json`: plataformas e núcleos.
  - `graficos.json`: ajuste por núcleo e por nota da placa, modo modesto e
    exceções.
  - `recursos.json`: as opções avançadas explicadas.
- Toda gravação é **atômica** (`arena.gravar_texto_atomico`): o ARENA
  grava num temporário com nome único por thread e troca pelo
  `os.replace`. Se a troca falhar porque outra thread está lendo (no
  Windows isso acontece), ele tenta de novo por pouco tempo. É o que
  protege o arquivo quando o pen drive sai no meio da gravação.
- Portas: 8777 (servidor), 55435 (partida a dois, no RetroArch) e 55436
  UDP (descoberta de colegas). Só as rotas de `ROTAS_REDE_EXTERNA` aceitam
  pedido de fora do computador, e todo POST exige
  `Content-Type: application/json`. A 8780 (tela do celular como controle,
  `servidor\controle_remoto.py`) só abre com a chave ligada em Ajustes e só
  atende rede local; o RetroArch escuta o UDP dele (porta sorteada a cada
  jogo) só enquanto o jogo roda.
- Testes:
  - `servidor\tests\run.py` (ou `RODAR_TESTES.bat`) antes de todo commit.
  - O `testes\teste_*.py` da área que você mexeu.
  - `ferramentas\rodada_final.py` antes de versão nova (cerca de 80 min).
  - Teste que abre emulador usa `testes\protege_cfg.rodar(main)`, com
    `emuladores=True` para PCSX2, Dolphin, RPCS3 e Xenia.
  - Pasta temporária se apaga com `testes\limpeza.apagar_pasta`, nunca com
    `rmtree(ignore_errors=True)`.

## Regras técnicas (detalhe em `docs\REGRAS-TECNICAS.md`)

Antes de mexer em threads, processos, vídeo ou RetroArch, **leia a seção
certa de `docs\REGRAS-TECNICAS.md`**. O mínimo que vale sempre:

- Servidor: `ThreadingHTTPServer`, estado compartilhado só com trava (a
  conferência e a gravação na mesma trava), trabalho demorado em thread
  `daemon`, nada de laço de consulta (parado, perto de 0% de CPU).
- Prioridade sem administrador (`processos.py`); classe de prioridade não
  se combina com OU; `SetPriorityClass` sempre com `argtypes`. O modo de
  energia do Windows não se mexe.
- Vídeo: só `automatico`, `vulkan`, `d3d11` e `glcore`; o Vulkan é
  conferido num processo separado; a placa da tela principal vem antes do
  registro do Windows.
- RetroArch: `global_core_options = "true"`, `network_cmd_enable = false`,
  `user_language = 7`; as opções da partida vão pelo `--appendconfig`
  antes do jogo; o tipo de porta vai no `.rmp` da partida; núcleo sem
  netplay usa o `core_netplay`, nunca o `.info` editado.

## Como trabalhar

- **Português do Brasil em tudo**, inclusive na descrição de cada comando.
  Respostas diretas. Quando algo não for possível, diga na hora, com o
  motivo técnico. Diagnóstico por eliminação.
- **Economize tokens:**
  - Não leia arquivo grande inteiro (o `arena.py` tem cerca de 8.200
    linhas): use a busca e leia só o trecho.
  - Não use agentes nem workflows sem pedido.
  - Use comandos curtos. Operação de vários passos vira um script `.py` em
    `ferramentas\`.
- Antes de corrigir, reproduza o problema e ache a causa no código. Faça
  uma mudança por vez, com teste, e um commit ao fim de cada uma. Ao mudar
  uma função, atualize o guia certo (de `1-COMECAR.md` a
  `6-RECURSOS-E-REPARO.md`).
- **Nunca apague** save, jogo, núcleo, BIOS ou `dados\`. Dado do usuário
  só muda com autorização.
- **Git** (detalhe em `AGENTS.md`):
  - Nunca `git add -A` nem `git add .`: só os arquivos que você mudou,
    porque outro assistente (Hermes) trabalha na mesma pasta.
  - Nunca `git init` fora daqui (nem em `..\ARENA`) e nunca
    `push --force`.
  - Publique pelo `SINCRONIZAR.bat`, que confere BIOS, jogo, banco, save,
    e-mail, senha e token antes de enviar.
  - No começo da sessão, rode `git pull --ff-only` e confira se o Hermes
    (`hermes.exe`) está rodando.
