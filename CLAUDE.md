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
| Sem administrador | Nada de driver, serviço, regra de firewall ou gravação no registro |
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
  `Content-Type: application/json`.
- Testes:
  - `servidor\tests\run.py` (ou `RODAR_TESTES.bat`) antes de todo commit.
  - O `testes\teste_*.py` da área que você mexeu.
  - `ferramentas\rodada_final.py` antes de versão nova (cerca de 80 min).
  - Teste que abre emulador usa `testes\protege_cfg.rodar(main)`, com
    `emuladores=True` para PCSX2, Dolphin, RPCS3 e Xenia.
  - Pasta temporária se apaga com `testes\limpeza.apagar_pasta`, nunca com
    `rmtree(ignore_errors=True)`.

## Threads e processos (alocação de CPU)

**No servidor:**
- `class Servidor(ThreadingHTTPServer)`: cada pedido roda na sua própria
  thread.
- Estado compartilhado só se mexe com trava, e a conferência e a gravação
  ficam na **mesma** trava. As travas:
  - `TRAVA_JOGO`: um jogo por vez.
  - `TRAVA_REDE`: troca do servidor sem reabrir o ARENA.
  - As outras: `TRAVA_BANCO`, `TRAVA_ARQUIVO`, `TRAVA_CACHE`,
    `TRAVA_RELEITURA`, `TRAVA_CAPAS`, `TRAVA_BARREIRAS` e `TRAVA_VIZINHOS`.
- Trabalho demorado nunca roda na thread do pedido: vai para uma thread
  `daemon`.
  - Ao abrir o ARENA: `rodar_vigia`, `anunciar_e_escutar` (UDP 55436, a
    cada 5 s; só escuta com a rede liberada ou com o Jogar Junto
    procurando partida), `conferir_vulkan`, `conferir_fliperamas` e
    `organizar_bios`.
  - Sob pedido: capas, `arrumar` (descompactar) e o teste dos amigos, em
    paralelo.
  - A janela preta recebe os recados por fila, numa thread só dela
    (`janela_preta.py`).
- Parado, o servidor fica perto de 0% de CPU, porque não há laço de
  consulta. Os controles são contados só ao abrir o jogo
  (`controles.contar_controles`, por Raw Input + XInput): o `joyGetPosEx`
  chamado a cada pedido vazava alças do Windows.

**No emulador (`processos.py`, sem administrador):**
- Durante o jogo, o ARENA se rebaixa
  (`prioridade_do_arena(ABAIXO_DO_NORMAL)` e
  `memoria_do_arena(MEMORIA_BAIXA)`) e volta ao normal quando o jogo fecha.
- No Ultra, `tirar_da_economia_de_energia(pid)` tira o emulador do EcoQoS
  do Windows (`SetProcessInformation` com `ProcessPowerThrottling`).
- **O modo de energia do Windows não se mexe** (decisão do Rafael).
- Duas armadilhas que já custaram caro:
  - Classe de prioridade não se combina com OU: `0x8000|0x80` vira "acima
    do normal".
  - `SetPriorityClass` sem `argtypes` cortava o handle.
- RetroArch, `video_threaded` (o vídeo numa thread própria: mais quadros em
  processador fraco, com um pouco mais de atraso):
  - `true` nos perfis Desempenho e Equilibrado e na partida a dois.
  - `false` no perfil Qualidade e no Ultra.
  - Onde fica: `arena.PERFIS_GRAFICOS` e `ULTRA_DESEMPENHO`.
- Dolphin: `CPUThread` (Dual Core) sempre ligado e compilação de shader
  híbrida (`ShaderCompilationMode` 2; no nível mínimo, 3, que pula o
  desenho). O padrão do Dolphin é a compilação síncrona, que trava a cada
  efeito novo.
- `ferramentas\modo_alvo.py` abre o ARENA num Job Object com os limites
  da máquina-alvo (2 núcleos, prioridade baixa e teto de memória). Ele não
  imita disco lento, placa fraca nem a falta de AVX.

## Vulkan e motor de vídeo (estabilidade)

**RetroArch:**
- Só oferece `automatico`, `vulkan`, `d3d11` e `glcore`
  (`arena.DRIVERS_VIDEO`).
- O automático (`hardware.driver_video`) testa Vulkan, depois D3D11,
  depois glcore, conferindo qual DLL carrega.
- O `vulkan-1.dll` pode ter sobrado de outra placa, e Vulkan sem placa faz
  o jogo abrir e fechar na hora. Por isso, ao abrir o ARENA,
  `conferir_vulkan` pergunta ao Vulkan, num **processo separado**
  (`hardware.vulkan_tem_placa`), se ele enxerga alguma placa. Se não
  enxergar, troca para D3D11.
- Atraso de imagem: em Vulkan e D3D11 se controla pela fila de imagens
  (`video_max_swapchain_images`). O `video_hard_sync` só vale no OpenGL.

**Placa de vídeo:**
- `hardware.placa_da_tela_principal()` (`EnumDisplayDevicesW`) vem antes
  do registro do Windows, que guarda placas que já saíram do computador.
  Uma GeForce antiga fazia a Radeon integrada passar por dedicada e
  quebrava o texto do PS1.
- A nota da placa é separada da nota geral, e placa integrada não passa
  de 3.

**Por console:**
- **N64:** `parallel-rdp` (Vulkan) só com nota da placa a partir de 4
  (`graficos.json → excecoes`); abaixo disso, `gliden64`.
- **PS1:** o SwanStation regrava inteiro o
  `retroarch\system\swanstation\vulkan_pipelines.bin` a cada partida. No
  modo econômico, esse arquivo fica somente leitura (`graficos.CACHE_PS1`).
- **PS2 (PCSX2):** os motores estão em `graficos.MOTORES_PCSX2`. O
  automático do PCSX2 2.8 escolhe D3D12 nas placas Intel; se a imagem
  piscar, use D3D11.
  - O ARENA sempre grava os valores seguros: mipmapping, filtro trilinear
    e pré-carga completa de textura.
  - Em placa integrada, também 1x e mistura Básica.
- **Xbox 360 (Xenia):** sempre Vulkan (`consoles.json →
  xbox360.externo.placa` e `graficos.placa_do_xenia`). O D3D12 dava
  "Graphics device lost" na Radeon integrada. O Xenia exige AVX, por isso
  **não roda na máquina-alvo**.

## RetroArch: o que não se reverte

- `arena.gravar_override` grava a configuração de cada partida, que entra
  pelo `--appendconfig`. As opções vêm **antes** do arquivo do jogo, e o
  `--host` leva a porta explícita (`--port 55435`).
- `global_core_options = "true"`. Sem ela, cada núcleo lê o próprio `.opt`
  e ignora em silêncio o que o ARENA grava.
- A cada abertura, `graficos.VALORES_OBRIGATORIOS` e
  `corrigir_caminhos_retroarch_cfg()` acertam o `retroarch.cfg`:
  - Os caminhos apontam para a pasta atual, inclusive o `cache_directory`.
  - `network_cmd_enable = false`. Ligado, qualquer máquina da rede fecharia
    o jogo.
  - `user_language = 7` (português do Brasil; o 17 é grego).
  - `menu_driver = rgui` e `pause_nonactive = false`.
- O `input_auto_game_focus` fica fora do Ultra, porque prende o Esc.
  Travar as teclas é a chave `travar_teclas`, com escape no F9.
- O tipo de porta (`input_libretro_device_pN`, como o Multitap e o
  analógico do PS1, 517) vai no `.rmp` da partida
  (`remapeamento_da_partida`). O RetroArch ignora esse valor no
  `--appendconfig`.
- Controles:
  - O botão que o aluno não definiu vai como `nul`.
  - O direcional fica com o autoconfig (o chapéu `h0up`), nunca com os
    botões 12 a 15 do navegador.
- Partida a dois:
  - Núcleo sem netplay não se "destrava" editando o `.info`. Usa-se um
    núcleo alternativo (`consoles.json → core_netplay`; no PS1, o
    PCSX ReARMed).
  - O Multitap pede `netplay_max_connections = 4`.
- Dos registros do RetroArch, ficam os 10 mais recentes
  (`limpar_logs_antigos`).
- Java ME (FreeJ2ME-Plus): o núcleo abre o `javaw` do PATH.
  - O Java de `emuladores\Java` vai na frente do PATH (`java_do_arena.py`).
  - Vídeo sem thread (`consoles.json → opcoes_retroarch`): com thread, o
    RetroArch travava ao fechar.
  - Uma caixa do Windows (`processos.caixa_que_fecha_os_filhos`) fecha o
    Java que sobrar quando o RetroArch cai.

## Como trabalhar

- **Português do Brasil em tudo**, inclusive na descrição de cada comando.
  Respostas diretas. Quando algo não for possível, diga na hora, com o
  motivo técnico. Diagnóstico por eliminação.
- **Economize tokens:**
  - Não leia arquivo grande inteiro (o `arena.py` tem cerca de 6.700
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
