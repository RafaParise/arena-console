# Mapa do multitap — Fase A

> Pesquisa de 25/09/2026, sem mexer no funcionamento do ARENA. O programa lê
> `servidor\multitap.json`; esta página é a mesma coisa para ler. Conferir
> contra os núcleos da pasta a qualquer momento:
> `servidor\python\python.exe ferramentas\conferir_mapa_multitap.py`
> (hoje: tudo confere).

## Como cada linha foi confirmada

1. **`.info` de cada núcleo** (`retroarch\info\`): diz se tem Jogar Junto
   (`savestate_features`). **Não traz número de jogadores** — conferido nos 9.
2. **Textos de dentro do `.dll` da pasta** (`ferramentas\textos_do_nucleo.py`):
   nome de cada opção, cada valor e o nome de cada tipo de controle. É a única
   fonte que bate com a versão que o aluno roda.
3. **Código-fonte oficial** (GitHub do libretro e dos autores de cada núcleo):
   o **número** de um tipo de controle (ex.: 257) não fica escrito no `.dll`, e
   quantos jogadores cada ligação abre também não. Arquivo e linha anotados
   em cada item do `multitap.json`.
4. **RetroArch da pasta: versão 1.22.2** (perguntado ao próprio
   `retroarch.exe --version`). Os padrões foram lidos no código-fonte
   **dessa mesma versão** (tag `v1.22.2`).
5. **Documentação oficial** (docs.libretro.com, páginas *Netplay FAQ* e
   *Getting Started*): **não fala** do limite de conexões, do multitap nem do
   `input_max_users`. Por isso o código-fonte é a referência.

## Os dois limites do RetroArch (valem para todos os consoles)

| O quê | Chave | Padrão | O que precisa |
|---|---|---|---|
| Quantos colegas entram pelo **Jogar Junto** | `netplay_max_connections` | **3** (v1.22.2, `config.def.h` linha 1367); teto do código 32 | **jogadores do jogo − 1**. Com 3, o 5º jogador é recusado mesmo com o adaptador certo — era o erro da auditoria 1 |
| Quantos controles o RetroArch lê **no mesmo computador** | `input_max_users` | RetroArch 8; **ARENA 2** (Ajustes → Avançado) | **pelo menos o número de jogadores**; com 2, o 3º controle em diante fica mudo |

## Por console (só os que têm jogo na sua pasta)

| Console | Núcleo que o ARENA usa | Jogadores sem adaptador | Como liga o adaptador | Chave = valor exato | Jogadores com adaptador | Jogar Junto |
|---|---|---|---|---|---|---|
| Super Nintendo | snes9x | 2 | **tipo de controle** numa porta ("Multitap") | `input_libretro_device_p2 = "257"` | **5** (8 com as duas portas) | sim |
| NES | fceumm | 2 | **tipo de controle** nas portas 3 e 4 ("4-Player Adapter" / Four Score). O núcleo **já liga sozinho** para os jogos de uma lista interna dele | `input_libretro_device_p3 = "513"` e `input_libretro_device_p4 = "513"` | **4** | sim |
| PS1 jogando junto | pcsx_rearmed | 2 | **opção do núcleo** "Multitap Mode" | `pcsx_rearmed_multitap = "port 1"` (desligado: `"disabled"`) | **5** (`"ports 1 and 2"` = 8) | sim |
| PS1 no mesmo computador | swanstation | 2 | **opção do núcleo** "Multitap Mode" | `swanstation_ControllerPorts_MultitapMode = "Port1Only"` (desligado: `"Disabled"`) | **5** (`"BothPorts"` = 8) | não (núcleo recusa) |
| Sega Saturn | mednafen_saturn | 2 | **opção do núcleo**, uma por porta ("6Player Adaptor") | `beetle_saturn_multitap_port1 = "enabled"` (+ `..._port2 = "enabled"`) | **7** com um, **12** com os dois | **não confirmado** (nunca testado) |
| Nintendo 64 | mupen64plus_next | **4** | não existe: o console já tem 4 entradas | — (só `input_max_users` ≥ 4) | 4 | não (núcleo recusa) |
| Dreamcast | flycast | **4** | não existe: 4 entradas de fábrica | — (só `input_max_users` ≥ 4) | 4 | não (núcleo recusa) |
| PSP | ppsspp | 1 | não existe: aparelho de uma pessoa; multijogador é por rede própria (ad hoc) | — | 1 | não (núcleo recusa) |
| Neo Geo | fbneo | 2 | não existe: no arcade o número vem de cada jogo; os de Neo Geo são de 2 | — | 2 | sim |
| GameCube | Dolphin (externo) | — | fora do RetroArch | — | — | não pelo RetroArch |
| PS2 | PCSX2 (externo) | — | fora do RetroArch; como o PCSX2 liga o multitap dele: **não confirmado** | — | — | não pelo RetroArch |
| PS3 | RPCS3 (externo) | — | fora do RetroArch | — | — | não pelo RetroArch |
| Xbox 360 | Xenia (externo) | — | fora do RetroArch | — | — | não pelo RetroArch |

**Onde cada tipo vai escrito (importa para a Fase B):**
- **Tipo de controle** (SNES, NES): no arquivo de configuração temporário
  da partida, que já existe (`--appendconfig`). Não toca no `retroarch.cfg`.
- **Opção do núcleo** (PS1, Saturn): **não** vai nesse arquivo. Vai no arquivo
  de opções de núcleo, que o ARENA já grava a cada partida
  (`retroarch-core-options.cfg`, com o ajuste de imagem). Na Fase B ela é
  escrita só na partida que precisa e desligada na seguinte, para
  "sozinho ou em dois, nada muda" continuar valendo.

## Não confirmado — o que falta

| Item | O que falta para confirmar |
|---|---|
| `input_max_users` também limita quem **controla** pelo Jogar Junto? | O teste de 5 jogadores entrou com o ARENA em 2, mas "entrar" não prova "controlar". Teste da Fase D (5 instâncias, conferir no registro quem ganhou controle) |
| Jogar Junto do Saturn | Testar com o jogo completo (ver arquivos abaixo) na Fase E |
| NES `513` numa partida de verdade | O número vem da fórmula do `libretro.h`; conferir no registro do RetroArch ("Player 3: Gamepad") na Fase D. **Não há jogo de 4 jogadores de NES na pasta** (Contra é de 2) |
| Multitap do PS2 dentro do PCSX2 | Fora do RetroArch; não pesquisado nesta fase |
| Versões | Chaves e valores foram achados no `.dll` **da pasta**; a contagem de jogadores veio do código-fonte atual de cada núcleo, que pode ser mais novo que o `.dll`. Os testes das Fases D e E confirmam na prática |

A documentação oficial diz que Jogar Junto de PS1 "não funciona por
desempenho". No ARENA ele funciona com o PCSX ReARMed, testado de ponta a
ponta na auditoria 1. Fica registrado que a documentação está mais
pessimista que o teste.

## Arquivos da sua pasta que vão travar a Fase E

| Console | Arquivo | Problema |
|---|---|---|
| GameCube | `Mario Kart - Double Dash!! (USA) (Bonus Disc).rvz` | "Bonus Disc" é o disco de extras, não é o jogo |
| Xbox 360 | `Gears of War (USA) (Bonus Disc).iso` | idem — conferir se é o disco do jogo |
| Dreamcast | só `Marvel vs. Capcom 2 (USA) (Track 3).bin` | faltam o `.gdi` e as trilhas 1 e 2 |
| Sega Saturn | só `Saturn Bomberman (USA) (1S) (Track 01).bin` | faltam o `.cue` e as trilhas de som |
| Neo Geo | `jogos\pessoais\Neo Geo\neogeo.zip` com **0 MB** | vazio (a BIOS usada fica em `retroarch\system`; conferir na Fase E) |
