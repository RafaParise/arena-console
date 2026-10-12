# Inventário do ARENA

Gerado por `testes\inventario.py --md=...` direto do código (não editar à mão).

## Rotas do servidor

| Rota | Método | Aberta à rede | Quem chama | Funções da tela |
|---|---|---|---|---|
| `/api/acervo` | GET | não | tela | carregarAcervo |
| `/api/acervo/instalar` | POST | não | tela | carregarAcervo |
| `/api/acervo/remover` | POST | não | tela | carregarAcervo |
| `/api/acervo/salvar` | POST | não | tela | ligarEventos |
| `/api/amigo/adicionar` | POST | não | tela | adicionarAmigo |
| `/api/amigo/codigo` | POST | sim | tela | adicionarAmigoCodigo, carregarColegas |
| `/api/amigo/remover` | POST | não | tela | removerAmigo |
| `/api/amigo/testar` | POST | sim | tela | testarAmigo |
| `/api/arrumar/progresso` | GET | não | tela | arrumarJogo |
| `/api/backup` | POST | não | tela | ligarEventos |
| `/api/barreiras` | GET | não | tela | verificarBarreiras |
| `/api/barreiras/fechar` | POST | não | tela | desenharBarreiras |
| `/api/biblioteca-online` | GET | não | tela | carregarBibliotecaOnline |
| `/api/biblioteca-online/instalar` | POST | não | tela | carregarBibliotecaOnline |
| `/api/bios` | GET | não | tela | carregarBios |
| `/api/bios/abrir` | POST | não | tela | ligarEventos |
| `/api/bios/conferir` | POST | não | tela | carregarBios |
| `/api/bios/pasta` | POST | não | tela | abrirPastaDaBios |
| `/api/botoes` | GET | não | tela | desenharBotoes, desenharMapa |
| `/api/capa` | GET | não | tela (endereco que vem do servidor) | — |
| `/api/capa/atualizar` | POST | não | tela | ligarEventos |
| `/api/capa/enviar` | POST | não | tela | ligarEventos |
| `/api/capa/miniatura` | POST | não | tela | proximaMiniatura |
| `/api/capas/buscar-faltando` | POST | não | tela | buscarCapasQueFaltam |
| `/api/capas/parar` | POST | não | tela | buscarCapasQueFaltam |
| `/api/capas/progresso` | GET | não | tela | buscarCapasQueFaltam |
| `/api/catalogo` | GET | não | tela, PARTIDA.bat | carregarCatalogo |
| `/api/cheat/adicionar` | POST | não | tela | adicionarCheat |
| `/api/cheat/alterar` | POST | não | tela | alterarCheat |
| `/api/colegas` | GET | sim | tela | carregarColegas |
| `/api/como-colocar` | GET | não | tela | abrirComoColocar |
| `/api/config` | POST | não | tela | salvarConfig |
| `/api/conquistas` | GET | não | tela | carregarConquistas |
| `/api/estado` | GET | não | tela, PARTIDA.bat | carregarEstado, conferirFaixaTeclas, esperarServidorVoltar, exportarPacote, ligarEventos |
| `/api/estado/apagar` | POST | não | tela | apagarEspaco |
| `/api/exportar` | POST | não | tela | exportarPacote |
| `/api/importar` | POST | não | tela | importarPacote |
| `/api/indexar` | POST | não | tela | ligarEventos |
| `/api/jogar` | POST | não | tela | comecarPartida, jogar |
| `/api/jogo` | GET | não | tela, PARTIDA.bat | abrirEscolhaConsole, abrirGaveta_jogo |
| `/api/jogo/arrumar` | POST | não | tela | arrumarJogo |
| `/api/jogo/console` | POST | não | tela | ligarEventos |
| `/api/jogo/impressao` | GET | sim | PARTIDA.bat | — |
| `/api/jogo/mover` | POST | não | tela | moverJogo |
| `/api/mala` | POST | não | tela | ligarEventos |
| `/api/mapeamento` | GET | não | tela | desenharMapa |
| `/api/mapeamento/definir` | POST | não | tela | capturar, gravaWizard |
| `/api/mapeamento/limpar` | POST | não | tela | ligarEventos |
| `/api/mapeamento/padrao` | POST | não | tela | ligarEventos |
| `/api/partida/procurar` | GET | não | tela | procurarPartidas |
| `/api/partida/testar` | POST | sim | tela | ligarEventos |
| `/api/pasta/abrir` | POST | não | tela | desenharComoColocar |
| `/api/pastas/criar` | POST | não | tela | ligarEventos |
| `/api/perfil-controle` | POST | não | tela | prepararMapa |
| `/api/perfil/foto` | GET | não | tela | atualizarFotoPerfil, ligarEventos |
| `/api/perfil/foto` | POST | não | tela | atualizarFotoPerfil, ligarEventos |
| `/api/perfil/novo` | POST | não | tela | ligarEventos |
| `/api/perfis-controle` | GET | não | tela | desenharMapa, prepararMapa |
| `/api/placar` | POST | não | tela | salvarPlacar |
| `/api/ranking` | GET | sim | tela | carregarRanking |
| `/api/reparar-runtime` | POST | não | tela | ligarEventos |
| `/api/sinc/ola` | POST | sim | PARTIDA.bat, outro ARENA | — |
| `/api/sinc/receber` | POST | sim | outro ARENA | — |
| `/api/sincronizar` | POST | não | tela | enviarRecordes |

## A tela

### (tela principal)

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button `btnPerfil` | Perfil | — | click | — |
| button `btnAmigos` | Amigos | — | click | — |
| button `btnRecordes` | Recordes | — | click | /api/estado, /api/ranking |
| button `btnConquistas` | Conquistas | — | click | /api/conquistas, /api/estado |
| button `btnAcervo` | Biblioteca | — | click | /api/acervo, /api/estado |
| button `btnTema` | ☾ Escuro | — | click | /api/config, /api/estado |
| button `btnSincronizar` | Enviar recordes 0 | — | click | /api/ranking, /api/sincronizar |
| button `btnAjustes` | Ajustes | — | click | — |
| button | Todos os jogos 0 | — | achado pelo atributo data-plataforma (linha 394) | — |
| button `btnComoColocar` | Como colocar jogos | — | click | /api/como-colocar, /api/estado |
| button `btnCriarPastas` | Criar pastas dos consoles | — | click | /api/catalogo, /api/estado, /api/pastas/criar |
| button `btnAtualizar` | Atualizar lista | — | click | /api/catalogo, /api/estado, /api/indexar |
| button `btnBuscarCapas` | Buscar capas que faltam | — | click | /api/capas/buscar-faltando, /api/capas/parar, /api/capas/progresso, /api/catalogo, /api/estado |
| input `campoBusca` | Procurar jogo | — | input | — |
| button `btnTodosJogos` | Todos | — | ligado num laco do app.js (linha 3722, em ligarEventos) | — |
| button `btnFavoritos` | ★ Favoritos | — | ligado num laco do app.js (linha 3723, em ligarEventos) | — |
| button `btnRecentes` | Recentes | — | ligado num laco do app.js (linha 3724, em ligarEventos) | — |
| button `btnMais` | Mostrar mais | — | click | — |
| button `btnMoverSugerido` | Mover para a pasta certa | — | click | /api/catalogo, /api/estado, /api/jogo/mover |
| button `btnJogarSelecionado` | Jogar agora | — | click | /api/config, /api/jogar |
| button `btnMultiplayerSelecionado` | Jogar multiplayer | — | click | /api/colegas, /api/config, /api/jogar |
| button `btnGerirSelecionado` | Saves e cheats | — | click | /api/estado, /api/jogo |
| button `btnEscolherConsole` | Escolher console | — | click | /api/estado, /api/jogo |
| button `btnAtualizarCapa` | Buscar capa | — | click | /api/capa/atualizar, /api/catalogo, /api/estado |
| input `campoEnviarCapa` | — | — | change | /api/capa/enviar, /api/catalogo, /api/estado |

### gavetaPerfil — Perfil

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela gavetaPerfil | — |
| button | Meu perfil | — | abre a aba perfil | — |
| button | Amigos | — | abre a aba rede | — |
| input `perfilFotoArquivo` | — | perfil | change | /api/estado, /api/perfil/foto |
| button `btnRemoverFotoPerfil` | Remover foto | perfil | click | /api/estado, /api/perfil/foto |
| input `campoApelido` | — | perfil | keydown | /api/config |
| button `btnTrocarApelido` | Salvar apelido | perfil | click | /api/config |
| button `chaveApagarSaves` | Apagar saves e cheats | perfil | click | — |
| button `btnNovoPerfil` | Começar do zero | perfil | click | /api/botoes, /api/catalogo, /api/colegas, /api/estado, /api/mapeamento, /api/partida/procurar, /api/perfil/foto, /api/perfil/novo, /api/perfis-controle, /api/ranking |
| input `amigoCodigo` | ARENA-AB12-CD34 | rede | — | — |
| button `btnAddAmigoCodigo` | Adicionar pelo código | rede | click | /api/amigo/codigo, /api/estado |
| details | Ou digite o endereço na mão                    Use quando o código não funcionar — por exemplo, se vocês estão em           redes que não se enxergam.                                          Apelido do amigo                                                Endereço que ele te passou | rede | abre e fecha (sem rota) | — |
| input `amigoApelido` | lucas | rede | — | — |
| input `amigoUrl` | 192.168.0.22 | rede | — | — |
| button `btnTestarAmigo` | Testar | rede | click | /api/amigo/testar, /api/estado |
| button `btnAddAmigo` | Adicionar | rede | click | /api/amigo/adicionar, /api/estado |
| button `chaveRede` | Aceitar conexões da rede | rede | click | /api/config, /api/estado |
| button `btnEnviarAgora` | Sincronizar agora | rede | click | /api/ranking, /api/sincronizar |
| button `btnMala` | Trocar pelo pen drive | rede | click | /api/estado, /api/mala, /api/ranking |

### gavetaComoColocar — Como colocar jogos

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela gavetaComoColocar | — |
| select `listaComoColocar` | — | — | change | — |

### gavetaAcervo — Biblioteca online

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela gavetaAcervo | — |
| input `campoBuscaOnline` | ex.: Commander Keen, Jazz Jackrabbit | — | input | /api/biblioteca-online, /api/estado |
| input `campoBuscaAcervo` | nome, console ou licença | — | input | /api/acervo, /api/estado |
| button `btnNovoAcervo` | Gerenciar catálogo | — | click | — |

### gavetaAjustes — Ajustes

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela gavetaAjustes | — |
| button | Simples | — | abre a aba simples | — |
| button | Avançado | — | abre a aba avancado | — |
| button | Máquina | — | abre a aba maquina | — |
| button | Controles | — | abre a aba controles | /api/botoes, /api/mapeamento, /api/perfis-controle |
| button | Emuladores | — | abre a aba emuladores | /api/bios, /api/bios/conferir, /api/estado |
| select `listaFundoAnimado` | Fundo animado | simples | change | /api/config, /api/estado |
| button `btnRestaurar` | Voltar tudo ao padrão | avancado | click | /api/config, /api/estado |
| button `btnRepararRuntime` | Copiar para a pasta do ARENA | maquina | click | /api/config, /api/jogar, /api/reparar-runtime |
| button `btnBarreiras` | Verificar agora | maquina | click | /api/barreiras, /api/estado |
| select `listaNivelGrafico` | Nível do gráfico | maquina | change | /api/config, /api/estado |
| button `chaveDesempenho` | Modo desempenho | maquina | click | /api/config, /api/estado |
| button `chaveUltra` | Ultra desempenho | maquina | click | /api/config, /api/estado |
| button `chaveTravar` | Travar teclas do sistema | maquina | click | /api/config, /api/estado |
| button `btnBackup` | Fazer cópia agora | maquina | click | /api/backup, /api/estado |
| button `btnExportar` | Montar meu pacote | maquina | click | /api/estado, /api/exportar |
| select `listaDriverControleTopo` | Tipo de conexão do controle | controles | change | /api/config, /api/estado |
| select `mapaTipo` | Tipo de controle | controles | change | — |
| select `mapaConsole` | Console do mapeamento | controles | change | /api/botoes, /api/estado, /api/mapeamento, /api/perfis-controle |
| button `chaveDirecional` | Usar o direcional | controles | ligado num laco do app.js (linha 1762, em prepararMapa) | /api/botoes, /api/estado, /api/mapeamento, /api/perfil-controle, /api/perfis-controle |
| button `chaveAnalogicoEsq` | Usar o analógico esquerdo | controles | ligado num laco do app.js (linha 1763, em prepararMapa) | /api/botoes, /api/estado, /api/mapeamento, /api/perfil-controle, /api/perfis-controle |
| button `chaveAnalogicoDir` | Usar o analógico direito | controles | ligado num laco do app.js (linha 1764, em prepararMapa) | /api/botoes, /api/estado, /api/mapeamento, /api/perfil-controle, /api/perfis-controle |
| button `chaveVibracao` | Vibração | controles | ligado num laco do app.js (linha 1765, em prepararMapa) | /api/botoes, /api/estado, /api/mapeamento, /api/perfil-controle, /api/perfis-controle |
| select `listaExtra` | Dispositivo do jogador 2 | controles | change | /api/estado, /api/perfil-controle |
| select `mapaJogador` | Jogador | controles | change | /api/botoes, /api/estado, /api/mapeamento, /api/perfis-controle |
| button `btnMapaLimpar` | Limpar tudo | controles | click | /api/botoes, /api/estado, /api/mapeamento, /api/mapeamento/limpar, /api/perfis-controle |
| button `btnMapaPadrao` | Padrão do teclado | controles | click | /api/botoes, /api/estado, /api/mapeamento, /api/mapeamento/padrao, /api/perfis-controle |
| button `btnMapaAuto` | Voltar ao reconhecimento automático | controles | click | /api/botoes, /api/estado, /api/mapeamento, /api/mapeamento/padrao, /api/perfis-controle |
| button `btnMapaWizard` | Configurar com assistente | controles | click | /api/botoes, /api/mapeamento, /api/perfis-controle |
| button `wizardAguardar` | Estou pronto — pressione o botão agora | controles | click | /api/botoes, /api/mapeamento, /api/mapeamento/definir, /api/perfis-controle |
| button `wizardPular` | Não tenho esse botão | controles | click | /api/botoes, /api/mapeamento, /api/perfis-controle |
| select `listaConsoleBotoes` | Console para ver os botões | controles | change | /api/botoes, /api/estado |
| button `btnBiosPasta` | Abrir a pasta BIOS | emuladores | click | /api/bios/pasta, /api/estado |
| button `btnBiosConferir` | Conferir | emuladores | click | /api/bios, /api/bios/conferir, /api/catalogo |
| select `listaPresetGrafico` | — | emuladores | change | /api/config, /api/estado |
| select `listaMotorPs2` | Motor de vídeo do PS2 | emuladores | change | /api/config, /api/estado |
| button `chaveRpcn` | Ligar RPCN | emuladores | click | /api/config, /api/estado |
| select `listaBiosAbrir` | Console para abrir a BIOS | emuladores | — | — |
| button `btnAbrirBios` | Abrir só a BIOS | emuladores | click | /api/bios/abrir, /api/estado |

### gavetaConquistas — Conquistas da turma

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela gavetaConquistas | — |

### gavetaRecordes — Recordes

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela gavetaRecordes | — |
| button | Pontuação | — | abre a aba pontos | — |
| button | Tempo de jogo | — | abre a aba tempo | — |

### gavetaJogo — Jogo

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela gavetaJogo | — |
| button | Save states | — | abre a aba estados | — |
| button | Cheats | — | abre a aba cheats | — |
| select `listaConsoleJogo` | Console deste jogo | estados | change | — |
| input `cheatDescricao` | Vidas infinitas | cheats | — | — |
| textarea `cheatCodigo` | 7E0DBE09 7E0DBF09 | cheats | — | — |
| button `btnAddCheat` | Adicionar código | cheats | click | /api/cheat/adicionar, /api/estado |

### modalJuntoLocal — Jogar junto neste computador

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Fechar | — | fecha a janela modalJuntoLocal | — |
| button `btnAbrirJuntoLocal` | Abrir o jogo | — | click | /api/config, /api/jogar |

### modalPartida — Jogar junto

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| button | Eu abro a partida Cria uma partida. | — | achado pelo atributo data-papel (linha 2694) | — |
| button | Entrar na partida do amigo Entra em uma partida aberta. | — | achado pelo atributo data-papel (linha 2694) | — |
| button | Só assistir Assiste sem controlar. | — | achado pelo atributo data-papel (linha 2694) | — |
| button `chaveInternet` | Jogar pela internet | — | click | — |
| select `listaAmigosPartida` | — | — | change | — |
| select `listaJogadorPartida` | — | — | — | — |
| button `btnTestarPartida` | Testar antes de começar | — | click | /api/estado, /api/partida/testar |
| button | Cancelar | — | fecha a janela modalPartida | — |
| button `btnAbrirPartida` | Começar | — | click | /api/estado, /api/jogar |

### modalPlacar — Registrar pontuação

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| input `campoPontos` | — | — | keydown | /api/estado, /api/placar, /api/ranking |
| button | Cancelar | — | fecha a janela modalPlacar | — |
| button `btnSalvarPontos` | Salvar | — | click | /api/estado, /api/placar, /api/ranking |

### modalAcervo — Adicionar jogo autorizado

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| input `acervoId` | meu-homebrew | — | — | — |
| input `acervoTitulo` | Meu jogo homebrew | — | — | — |
| input `acervoPlataforma` | Nintendo NES | — | — | — |
| textarea `acervoDescricao` | Jogo criado e liberado pelo autor. | — | — | — |
| input `acervoLicenca` | CC0, domínio público ou autorização do autor | — | — | — |
| input `acervoFonte` | https://github.com/... | — | — | — |
| input `acervoUrl` | https://raw.githubusercontent.com/... | — | — | — |
| input `acervoDestino` | NES/Meu jogo.nes | — | — | — |
| input `acervoSha256` | 64 caracteres hexadecimais | — | — | — |
| input `acervoAutorizado` | — | — | — | — |
| button | Cancelar | — | fecha a janela modalAcervo | — |
| button `btnSalvarAcervo` | Salvar item | — | click | /api/acervo, /api/acervo/salvar, /api/estado |

### modalConsole — Qual é o console deste jogo?

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| select `listaConsoleJogoModal` | — | — | — | — |
| button | Cancelar | — | fecha a janela modalConsole | — |
| button `btnSalvarConsole` | Salvar escolha | — | click | /api/catalogo, /api/estado, /api/jogo/console |

### modalApelido — Como podemos chamar você?

| Controle | Texto | Aba | O que faz | Rotas |
|---|---|---|---|---|
| input `campoApelidoInicial` | ex.: PixelMaster | — | keydown | — |
| button `btnSalvarApelido` | Começar | — | click | — |

### Botões que o app.js cria sozinho

| Função | Texto | Rotas do clique |
|---|---|---|
| `desenharPlataformas` | — | /api/catalogo, /api/estado, /api/jogo/mover |
| `linhaDoJogo` | — | — |
| `linhaDoJogo` | estaFavorito ? "★" : "☆" | — |
| `desenharAvisosDoJogo` | a.arrumar.rotulo | /api/arrumar/progresso, /api/catalogo, /api/estado, /api/jogo/arrumar |
| `desenharBarreiras` | `Fechar ${alvo.nome}` / "Fechado" | /api/barreiras/fechar, /api/estado |
| `desenharPerfis` | — | — |
| `controleDaOpcao` | — | /api/config, /api/estado |
| `linhaDoRecurso` | "por exemplo…" | — |
| `carregarColegas` | "Adicionar" | /api/amigo/codigo, /api/botoes, /api/colegas, /api/estado, /api/mapeamento, /api/partida/procurar, /api/perfil/foto, /api/perfis-controle |
| `desenharPacotes` | "Trazer de volta" | /api/estado, /api/importar |
| `desenharMapa` | atual ? "Trocar" : "Definir" | /api/botoes, /api/mapeamento, /api/mapeamento/definir, /api/perfis-controle |
| `desenharBiosConsoles` | `Abrir a pasta BIOS\\${pasta}` | /api/bios/pasta, /api/estado |
| `desenharAmigos` | "remover" | /api/amigo/remover, /api/estado |
| `desenharEspacos` | "apagar" | /api/estado, /api/estado/apagar |
| `desenharCheats` | — | /api/cheat/alterar, /api/estado |
| `desenharCheats` | "apagar" | /api/cheat/alterar, /api/estado |
| `carregarAcervo` | item.instalado ? "Instalado" : "Instalar" / "Baixando…" / "Instalar" | /api/acervo, /api/acervo/instalar, /api/catalogo, /api/estado |
| `carregarAcervo` | "Editar" | — |
| `carregarAcervo` | "Remover" | /api/acervo, /api/acervo/remover, /api/estado |
| `desenharComoColocar` | "Abrir a pasta" | /api/estado, /api/pasta/abrir |
| `desenharComoColocar` | "Abrir a pasta da BIOS" | /api/bios/pasta, /api/estado |
| `desenharComoColocar` | "Conferir" | /api/bios, /api/bios/conferir, /api/catalogo, /api/como-colocar, /api/estado |
| `carregarBibliotecaOnline` | "Instalar" / "Instalando…" / "Instalado" | /api/acervo, /api/biblioteca-online/instalar, /api/catalogo, /api/estado |

## Temporizadores da tela

| Arquivo:linha | Tipo | Espera | Função |
|---|---|---|---|
| app.js:137 | setTimeout | 2000 | esperarServidorVoltar |
| app.js:139 | setTimeout | 3000 | esperarServidorVoltar |
| app.js:170 | setTimeout | duracaoMs | recado |
| app.js:527 | setTimeout | 400 | pedirMiniatura |
| app.js:547 | setTimeout | 30 | proximaMiniatura |
| app.js:861 | setTimeout | 1000 | arrumarJogo |
| app.js:1997 | requestAnimationFrame | — | wizardAguardar |
| app.js:2001 | requestAnimationFrame | — | wizardAguardar |
| app.js:2165 | requestAnimationFrame | — | capturar |
| app.js:2169 | requestAnimationFrame | — | capturar |
| app.js:2920 | setInterval | 4000 | vigiarPartidas |
| app.js:3536 | setTimeout | 1000 | buscarCapasQueFaltam |
| app.js:3710 | setTimeout | 130 | ligarEventos |
| app.js:3860 | setTimeout | 300 | ligarEventos |
| app.js:3864 | setTimeout | 300 | ligarEventos |
| field-background.js:791 | requestAnimationFrame | — | (fora de funcao) |
| field-background.js:806 | requestAnimationFrame | — | (fora de funcao) |
| field-background.js:847 | setInterval | 3000 | (fora de funcao) |
| galaxy-background.js:796 | requestAnimationFrame | — | (fora de funcao) |
| galaxy-background.js:807 | requestAnimationFrame | — | (fora de funcao) |
| galaxy-background.js:836 | setInterval | 3000 | (fora de funcao) |

## Linhas de execução do servidor

| Arquivo:linha | Função | Nasce em | Em laço | Esperas |
|---|---|---|---|---|
| servidor\arena.py:3310 | `perguntar` | `procurar_partidas` | não | — |
| servidor\arena.py:3782 | `testar` | `quem_esta_online` | não | — |
| servidor\arena.py:4915 | `rodar` | `api_post` | não | — |
| servidor\arena.py:5226 | `buscar_capas_que_faltam` | `api_post` | não | — |
| servidor\arena.py:5698 | `executar_jogo` | `api_post` | não | — |
| servidor\arena.py:5926 | `atualizar_adaptadores` | `nome_do_adaptador` | não | — |
| servidor\arena.py:6124 | `encerrar_depois_da_resposta` | `trocar_escuta_de_rede` | não | 0.3 |
| servidor\arena.py:6352 | `rodar_vigia` | `principal` | sim | INTERVALO_VIGIA |
| servidor\arena.py:6353 | `anunciar_e_escutar` | `principal` | sim | 1.0 |
| servidor\arena.py:6356 | `conferir_vulkan` | `principal` | não | — |
| servidor\arena.py:6358 | `conferir_fliperamas` | `principal` | sim | 1.0 if ECONOMICO else 0.2, 5.0, 8.0 |
| servidor\arena.py:6361 | `organizar_bios` | `principal` | não | esperar |
| servidor\arena.py:6372 | `abrir_janela` | `principal` | não | — |
| servidor\arrumar.py:512 | `trabalhar` | `_iniciar` | sim | — |
| servidor\janela_preta.py:121 | `self._passar_para_a_janela` | `__init__` | sim | — |

## Chaves de configuração e onde são lidas

| Chave | Lida em |
|---|---|
| `abaixo_do_original` | servidor\arena.py, servidor\graficos.py, launcher\app.js |
| `apelido` | servidor\arena.py, servidor\diagnostico.py, servidor\partida.py, launcher\app.js |
| `avancado` | servidor\arena.py, launcher\app.js |
| `bios` | servidor\arena.py, servidor\bios.py, servidor\bios_catalogo.py, servidor\como_colocar.py, servidor\graficos.py, launcher\app.js |
| `codigo_proprio` | servidor\arena.py |
| `dispositivo_id` | servidor\arena.py, servidor\partida.py, launcher\app.js |
| `favoritos` | servidor\arena.py, launcher\app.js |
| `fundo_animado` | servidor\arena.py, launcher\app.js |
| `modo_desempenho` | servidor\arena.py, launcher\app.js |
| `modo_modesto` | servidor\arena.py, launcher\app.js |
| `motor_ps2` | servidor\arena.py, launcher\app.js |
| `nome_dispositivo` | servidor\arena.py |
| `perfil_controle` | servidor\arena.py |
| `perfil_grafico` | servidor\arena.py, launcher\app.js |
| `permitir_rede` | servidor\arena.py, servidor\partida.py, launcher\app.js |
| `preset_grafico_externo` | servidor\arena.py, launcher\app.js |
| `recentes` | servidor\arena.py, launcher\app.js |
| `rpcn_ativo` | servidor\arena.py, servidor\graficos.py, launcher\app.js |
| `servidores` | servidor\arena.py, servidor\diagnostico.py, launcher\app.js |
| `tema` | servidor\arena.py, launcher\app.js |
| `tipo_controle` | servidor\arena.py |
| `travar_teclas` | servidor\arena.py, launcher\app.js |
| `ultra_desempenho` | servidor\arena.py, launcher\app.js |
| `avancado.audio_enable` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.audio_sync` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.audio_volume` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.fastforward_ratio` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.fps_show` | servidor\arena.py, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.input_analog_deadzone` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.input_analog_sensitivity` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.input_joypad_driver` | launcher\app.js, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.input_max_users` | servidor\arena.py, servidor\graficos.py, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.input_menu_toggle_gamepad_combo` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.input_turbo_period` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.pause_nonactive` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.rewind_buffer_size` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.run_ahead_frames` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.run_ahead_secondary_instance` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.savestate_thumbnail_enable` | servidor\arena.py, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.slowmotion_ratio` | servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.video_driver` | servidor\arena.py, launcher\app.js, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.video_fullscreen` | servidor\arena.py, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.video_scale_integer` | servidor\arena.py, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |
| `avancado.video_swap_interval` | servidor\arena.py, servidor\arena.py:1486 (todas de uma vez: viram opcoes do RetroArch) |

## Internet (endereços fixos no código)

| Arquivo | Endereços |
|---|---|
| servidor\capas_do_disco.py | art.gametdb.com, download.xbox.com |
| servidor\capas_online.py | raw.githubusercontent.com, thumbnails.libretro.com |
| servidor\internet_archive.py | archive.org |
| launcher\index.html | github.com, npcap.com, raw.githubusercontent.com |

## Pastas

| Pasta | Arquivos | MB |
|---|---|---|
| emuladores | 11756 | 10250.4 |
| retroarch | 15235 | 2456.9 |
| BIOS | 59 | 30.8 |
| servidor | 112 | 22.5 |
| dados | 191 | 3.0 |
| testes | 130 | 0.9 |
| docs | 36 | 0.7 |
| ferramentas | 54 | 0.6 |
| launcher | 6 | 0.3 |
| (raiz) | 13 | 0.2 |
| perfil | 33 | 0.1 |

## Arquivos do ARENA (258)

| Arquivo | KB | Linhas |
|---|---|---|
| .gitignore | 2.5 |  |
| 1-COMECAR.md | 15.6 | 435 |
| 2-JOGOS.md | 49.3 | 1031 |
| 3-IMAGEM-SOM-CONTROLE.md | 51.5 | 1305 |
| 4-SAVES.md | 17.1 | 513 |
| 5-AMIGOS.md | 30.0 | 763 |
| 6-RECURSOS-E-REPARO.md | 16.5 | 525 |
| ARENA.bat | 3.9 | 110 |
| COLETAR.bat | 2.9 | 81 |
| docs\abrir_todos_bruto.json | 45.4 | 1693 |
| docs\auditoria2\linha_base_fase0.json | 1.8 | 110 |
| docs\auditoria2\linha_base_fase8.json | 1.8 | 110 |
| docs\auditoria2\medir_fase0\arena.json | 1.7 | 67 |
| docs\auditoria2\medir_fase0\arena.txt | 1.1 | 31 |
| docs\auditoria2\medir_fase0\arena_janela_preta.txt | 0.0 | 0 |
| docs\auditoria2\medir_fase8\arena.json | 1.9 | 73 |
| docs\auditoria2\medir_fase8\arena.txt | 1.4 | 35 |
| docs\auditoria2\medir_fase8\arena_janela_preta.txt | 0.0 | 0 |
| docs\auditoria2\medir_tela_fase2.json | 0.3 | 16 |
| docs\auditoria3\inventario_antes.json | 160.5 | 6868 |
| docs\auditoria3\inventario_antes.md | 38.7 | 686 |
| docs\auditoria3\linha_base_antes.json | 39.1 | 1767 |
| docs\auditoria3\varredura_fase1.json | 64.1 | 2174 |
| docs\cenarios_sala_bruto.json | 0.4 | 18 |
| docs\fuzz_rotas_bruto.json | 51.2 | 2512 |
| docs\gravacoes_parado_bruto.json | 0.2 | 7 |
| docs\inventario_bruto.json | 13.3 | 666 |
| docs\linha_base_bruta.json | 1.8 | 110 |
| docs\linha_base_depois_bruta.json | 1.8 | 109 |
| docs\longa_duracao_bruto.json | 2.6 | 139 |
| docs\MAPA-MULTITAP.md | 9.5 | 114 |
| docs\MAQUINA-ALVO.md | 23.8 | 362 |
| docs\matriz_jogos_bruto.json | 1.5 | 57 |
| docs\matriz_multitap_bruto.json | 6.4 | 228 |
| docs\medir_tela_bruto.json | 0.3 | 16 |
| docs\netplay_5_jogadores_bruto.json | 2.3 | 70 |
| docs\PLANO-AUDITORIA.md | 33.1 | 480 |
| docs\rede_ruim_bruto.json | 0.9 | 41 |
| docs\RELATORIO-AUDITORIA-1.md | 108.1 | 1691 |
| docs\RELATORIO-AUDITORIA-2.md | 29.5 | 527 |
| docs\RELATORIO-QUALIDADE.md | 20.0 | 245 |
| docs\rodada_final_bruta.json | 48.6 | 1212 |
| docs\ROTEIRO-MULTITAP.md | 3.8 | 72 |
| docs\varredura_fase1_bruta.json | 10.3 | 429 |
| docs\varredura_fase2_css_bruta.json | 0.7 | 31 |
| ferramentas\acentuar_textos.py | 9.8 | 196 |
| ferramentas\aplicar_protege_cfg.py | 1.4 | 33 |
| ferramentas\baixar_capas.py | 1.8 | 44 |
| ferramentas\chaves_bios_nucleos.py | 1.1 | 27 |
| ferramentas\coletar_maquina.py | 44.1 | 958 |
| ferramentas\conferir_bios_neogeo.py | 1.8 | 47 |
| ferramentas\conferir_mapa_multitap.py | 3.3 | 78 |
| ferramentas\converter_fliperama_decriptado.py | 10.2 | 238 |
| ferramentas\corrigir_chaves_graficos.py | 2.7 | 62 |
| ferramentas\inventario_jogos.py | 1.5 | 36 |
| ferramentas\limpar_botoes_retroarch_cfg.py | 1.5 | 41 |
| ferramentas\limpar_registros_de_teste.py | 3.3 | 76 |
| ferramentas\limpar_retroarch_cfg.py | 1.4 | 38 |
| ferramentas\medir_arena.py | 51.3 | 1090 |
| ferramentas\medir_parado.py | 5.7 | 130 |
| ferramentas\modo_alvo.py | 7.2 | 155 |
| ferramentas\montar_relatorio_aud2.py | 6.9 | 155 |
| ferramentas\montar_versao_alunos.py | 40.0 | 770 |
| ferramentas\opcoes_do_nucleo.py | 0.8 | 20 |
| ferramentas\rodada_final.py | 9.7 | 206 |
| ferramentas\testar_controles.py | 4.5 | 126 |
| ferramentas\teste_aceite_pasta_movida.py | 3.9 | 116 |
| ferramentas\teste_amigo_ip_muda.py | 3.6 | 103 |
| ferramentas\teste_backup_falha_cancela_apagamento.py | 5.2 | 134 |
| ferramentas\teste_biblioteca_online.py | 2.9 | 80 |
| ferramentas\teste_capa_online.py | 4.6 | 109 |
| ferramentas\teste_controle_neogeo.py | 2.1 | 62 |
| ferramentas\teste_correcao_caminhos.py | 2.9 | 81 |
| ferramentas\teste_memory_card_ps1.py | 10.0 | 226 |
| ferramentas\teste_netplay_check_frames.py | 9.6 | 244 |
| ferramentas\teste_netplay_megadrive.py | 5.4 | 138 |
| ferramentas\teste_netplay_neogeo.py | 5.7 | 143 |
| ferramentas\teste_netplay_ps1.py | 5.5 | 142 |
| ferramentas\teste_netplay_suporte_nucleos.py | 3.1 | 95 |
| ferramentas\teste_netplay_xbox360.py | 3.3 | 95 |
| ferramentas\teste_pcsx2_completo.py | 4.6 | 129 |
| ferramentas\teste_pcsx_rearmed_basico.py | 2.0 | 63 |
| ferramentas\teste_perfil_foto.py | 3.7 | 104 |
| ferramentas\teste_qualidade_pcsx2.py | 3.4 | 96 |
| ferramentas\teste_rede_ps2_gt4.py | 3.8 | 107 |
| ferramentas\teste_rodizio_logs.py | 2.2 | 58 |
| ferramentas\teste_rpcn.py | 3.5 | 102 |
| ferramentas\textos_do_nucleo.py | 1.6 | 44 |
| ferramentas\trocar_testdb.py | 4.1 | 101 |
| launcher\app.js | 164.7 | 4362 |
| launcher\estilo.css | 48.8 | 1778 |
| launcher\field-background.js | 33.8 | 848 |
| launcher\galaxy-background.js | 32.8 | 837 |
| launcher\index.html | 48.9 | 1044 |
| launcher\pixel-sprites.js | 2.4 | 58 |
| LEIA-ME.md | 8.3 | 223 |
| PARTIDA.bat | 0.8 | 29 |
| RODAR_TESTES.bat | 1.4 | 40 |
| servidor\acervo.py | 8.9 | 230 |
| servidor\arena.py | 290.7 | 6416 |
| servidor\arrumar.py | 24.4 | 513 |
| servidor\barreiras.py | 39.5 | 647 |
| servidor\bios.py | 67.4 | 1445 |
| servidor\bios_catalogo.py | 17.6 | 274 |
| servidor\capas_do_disco.py | 8.0 | 179 |
| servidor\capas_online.py | 25.5 | 566 |
| servidor\cheats.py | 9.2 | 266 |
| servidor\como_colocar.py | 14.8 | 242 |
| servidor\consoles.json | 31.6 | 1277 |
| servidor\controles.py | 22.7 | 579 |
| servidor\diagnostico.py | 21.9 | 539 |
| servidor\graficos.json | 17.5 | 551 |
| servidor\graficos.py | 115.0 | 2565 |
| servidor\hardware.py | 28.6 | 743 |
| servidor\identificador.py | 12.4 | 345 |
| servidor\indexador.py | 54.9 | 1151 |
| servidor\integridade.py | 4.6 | 124 |
| servidor\internet_archive.py | 11.1 | 265 |
| servidor\janela_preta.py | 9.7 | 233 |
| servidor\jogadores.py | 8.4 | 200 |
| servidor\motivo_do_erro.py | 15.2 | 291 |
| servidor\multitap.json | 10.6 | 189 |
| servidor\nomes_arcade.py | 13.8 | 340 |
| servidor\partida.py | 10.8 | 291 |
| servidor\perfis_controle.json | 13.5 | 271 |
| servidor\processos.py | 6.8 | 182 |
| servidor\recursos.json | 21.9 | 644 |
| servidor\tests\__init__.py | 0.0 | 0 |
| servidor\tests\run.py | 26.7 | 624 |
| servidor\tests\test_arrumar.py | 13.7 | 296 |
| servidor\tests\test_barreiras.py | 9.4 | 177 |
| servidor\tests\test_bios.py | 18.0 | 353 |
| servidor\tests\test_cache_ps1.py | 2.4 | 68 |
| servidor\tests\test_capas_que_faltavam.py | 12.7 | 237 |
| servidor\tests\test_converter_fliperama.py | 6.8 | 145 |
| servidor\tests\test_graficos_acervo.py | 18.8 | 392 |
| servidor\tests\test_janela_preta.py | 3.6 | 96 |
| servidor\tests\test_jogadores.py | 12.0 | 224 |
| servidor\tests\test_motivo_do_erro.py | 15.2 | 296 |
| servidor\tests\test_multitap.py | 8.4 | 186 |
| testes\abrir_dois_arenas.py | 3.8 | 97 |
| testes\abrir_para_teste_manual.py | 7.0 | 144 |
| testes\apertar_teclas.ps1 | 0.7 | 14 |
| testes\comparar_linhas_produto.py | 2.6 | 69 |
| testes\controles_detectados.py | 2.2 | 52 |
| testes\foto_pcsx2_janela.ps1 | 0.9 | 18 |
| testes\foto_rpcs3.ps1 | 1.2 | 21 |
| testes\foto_tela.ps1 | 0.5 | 9 |
| testes\funcoes_js_mortas.py | 1.1 | 26 |
| testes\fuzz_rotas.py | 15.5 | 360 |
| testes\ids_da_tela.py | 1.8 | 37 |
| testes\inventario.py | 36.8 | 791 |
| testes\jogos_de_teste.py | 1.0 | 25 |
| testes\limpeza.py | 3.0 | 86 |
| testes\linha_base.py | 20.2 | 429 |
| testes\medir_cache_ps1.py | 4.0 | 88 |
| testes\medir_gravacoes_parado.py | 5.6 | 143 |
| testes\medir_tela.ps1 | 2.9 | 57 |
| testes\neogeo_bios_registro.py | 2.1 | 48 |
| testes\protege_cfg.py | 1.2 | 35 |
| testes\proxy_rede_ruim.py | 3.5 | 100 |
| testes\tela_sem_janela.py | 13.3 | 308 |
| testes\teste_abaixo_do_original.py | 24.4 | 398 |
| testes\teste_abrir_todos.py | 5.1 | 106 |
| testes\teste_acervo_download_real.py | 3.8 | 86 |
| testes\teste_acervo_sha256.py | 4.0 | 106 |
| testes\teste_acesso_de_rede.py | 6.4 | 137 |
| testes\teste_adaptadores_sem_laco.py | 5.4 | 133 |
| testes\teste_adaptadores_vpn.py | 2.6 | 61 |
| testes\teste_alcas_sem_vazamento.py | 4.4 | 119 |
| testes\teste_arquivos_corrompidos.py | 3.8 | 96 |
| testes\teste_arrumar_jogos.py | 11.9 | 220 |
| testes\teste_atualizar_versao_alunos.py | 9.2 | 181 |
| testes\teste_backup_rodizio.py | 5.7 | 118 |
| testes\teste_barreiras_api.py | 4.5 | 104 |
| testes\teste_barreiras_modo_restrito.py | 3.3 | 74 |
| testes\teste_biblioteca_busca.py | 7.5 | 163 |
| testes\teste_bios_consoles.py | 8.6 | 168 |
| testes\teste_bios_organizador.py | 10.8 | 190 |
| testes\teste_caminho_comprido.py | 2.6 | 60 |
| testes\teste_caminho_fora_no_cfg.py | 3.3 | 78 |
| testes\teste_capas_miniaturas.py | 7.5 | 158 |
| testes\teste_capas_todos_os_consoles.py | 12.8 | 242 |
| testes\teste_cenarios_sala.py | 8.7 | 200 |
| testes\teste_cfg_sem_linha_repetida.py | 4.4 | 97 |
| testes\teste_chaves_graficos.py | 3.3 | 78 |
| testes\teste_coletar_regua.py | 11.5 | 197 |
| testes\teste_como_colocar.py | 12.0 | 205 |
| testes\teste_concorrencia.py | 6.3 | 155 |
| testes\teste_dados_tortos.py | 6.5 | 137 |
| testes\teste_descoberta_30_maquinas.py | 6.1 | 148 |
| testes\teste_disco_amostras.py | 4.3 | 115 |
| testes\teste_disco_cheio.py | 4.2 | 101 |
| testes\teste_dns_rebinding.py | 4.9 | 110 |
| testes\teste_dolphin_config.py | 7.2 | 146 |
| testes\teste_estresse_catalogo.py | 4.1 | 107 |
| testes\teste_fase7.py | 3.4 | 91 |
| testes\teste_fat32_arquivo_grande.py | 3.7 | 85 |
| testes\teste_filtro_de_tela.py | 6.0 | 124 |
| testes\teste_fliperama_nomes.py | 11.9 | 216 |
| testes\teste_fundos_animados.py | 8.5 | 173 |
| testes\teste_imagem_ps1.py | 4.4 | 100 |
| testes\teste_internet_archive_download.py | 4.4 | 118 |
| testes\teste_kof2002_convertido.py | 4.9 | 104 |
| testes\teste_lista_partidas.js | 5.6 | 108 |
| testes\teste_local_4_jogadores.py | 5.2 | 116 |
| testes\teste_longa_duracao.py | 6.9 | 169 |
| testes\teste_mala_validacao.py | 3.7 | 87 |
| testes\teste_matriz_jogos.py | 9.8 | 217 |
| testes\teste_matriz_multitap.py | 9.9 | 202 |
| testes\teste_motivo_fliperama.py | 6.3 | 134 |
| testes\teste_multitap_5_jogadores_arena.py | 10.2 | 219 |
| testes\teste_multitap_opcao_nucleo_real.py | 4.0 | 87 |
| testes\teste_multitap_por_console.py | 12.3 | 250 |
| testes\teste_multitap_regra_de_ouro.py | 14.8 | 299 |
| testes\teste_netplay_5_jogadores.py | 11.4 | 259 |
| testes\teste_netplay_isolamento.py | 5.0 | 126 |
| testes\teste_opcoes_nucleo_ponta_a_ponta.py | 5.6 | 117 |
| testes\teste_orcamentos_modo_alvo.py | 5.4 | 114 |
| testes\teste_partida_aparece.py | 12.8 | 276 |
| testes\teste_partida_colega.py | 2.8 | 69 |
| testes\teste_partida_testar_timing.py | 3.3 | 82 |
| testes\teste_pasta_somente_leitura.py | 3.5 | 87 |
| testes\teste_pcsx2_bissecao.py | 3.5 | 86 |
| testes\teste_pcsx2_inicia.py | 4.1 | 97 |
| testes\teste_pcsx2_motor.py | 5.3 | 126 |
| testes\teste_pcsx2_placa.py | 4.6 | 114 |
| testes\teste_pcsx2_portatil.py | 2.8 | 66 |
| testes\teste_pcsx2_seguro.py | 8.8 | 182 |
| testes\teste_perfil_apelido.py | 6.7 | 135 |
| testes\teste_ps2_sem_bios.py | 4.2 | 94 |
| testes\teste_ps3_sem_firmware.py | 2.9 | 73 |
| testes\teste_psp_pulo_de_quadros.py | 5.7 | 123 |
| testes\teste_qual_opcao_de_nucleo_vale.py | 4.1 | 93 |
| testes\teste_quebrar_api.py | 12.6 | 261 |
| testes\teste_queda_no_meio_da_gravacao.py | 4.0 | 100 |
| testes\teste_rede_ruim.py | 6.6 | 164 |
| testes\teste_rede_sem_reabrir.py | 5.5 | 131 |
| testes\teste_rpcs3_controles.py | 2.4 | 61 |
| testes\teste_satellaview_aviso.py | 4.3 | 96 |
| testes\teste_servidor_que_cai.py | 14.0 | 303 |
| testes\teste_sinc_migracao_e_lotes.py | 4.2 | 93 |
| testes\teste_sinc_sem_relogio.py | 3.2 | 69 |
| testes\teste_tela_4k.py | 7.8 | 150 |
| testes\teste_tela_motivo.py | 6.6 | 121 |
| testes\teste_temp_esparso.py | 3.1 | 84 |
| testes\teste_travessia_capa.py | 3.5 | 87 |
| testes\teste_ultra_promessas.py | 6.3 | 144 |
| testes\teste_varios_discos.py | 9.8 | 182 |
| testes\teste_verificador_arquivos.py | 3.2 | 70 |
| testes\teste_vulkan_de_verdade.py | 3.5 | 82 |
| testes\teste_xenia_abre.py | 2.5 | 55 |
| testes\teste_zip_danificado.py | 6.2 | 130 |
| testes\textos_sem_acento.py | 2.5 | 56 |
| testes\varredura_auditoria3.py | 16.6 | 384 |
| testes\varredura_fase1.py | 7.4 | 189 |
| testes\varredura_fase2_css.py | 1.6 | 49 |
| VERIFICAR.bat | 0.9 | 37 |
