# Repasse da turma: partida entre casas sem lista pública

Feito em 10/11/2026. Código: `servidor\repasse_proprio.py`. Guia do aluno: `5-AMIGOS.md` ("Voltou em 10/11/2026").
Este documento é para quem **monta** o repasse (o professor) e serve de **exemplo de tomada de decisão** em redes:
cada escolha vem com o problema, as opções e o porquê.

## O problema

Dois alunos, cada um na sua casa, querem jogar juntos. Cada casa tem um roteador que deixa sair, mas não deixa
ninguém de fora entrar. Então o computador de um não consegue chegar no do outro. O RetroArch resolve isso com um
**repasse** (em inglês, *relay*, *tunnel server* ou *MITM*): os dois se ligam a um terceiro computador que está na
internet, e ele passa os dados de um para o outro.

## Decisão 1: repasse público do libretro ou repasse próprio?

| | Repasse público (libretro) | Repasse próprio (este) |
|---|---|---|
| Custo | grátis | grátis (um aparelho que já existe) |
| Como o amigo acha a sala | pela **lista pública** de salas na internet | por um **código de 6 números** |
| O que fica exposto | apelido de quem abriu, jogo, país, versão | nada: não existe lista |
| Depende de | servidores do libretro | um aparelho ligado na casa do professor |

**Escolha:** repasse próprio. A turma é de menores de idade, e a lista pública mostraria o apelido deles e o que
jogam. O preço é manter um aparelho ligado, e isso a bancada do professor já faz.

## Decisão 2: onde ele roda?

- **No PC do professor:** é a máquina mais forte, mas desligar o PC derrubaria todas as partidas. E o PC também joga.
- **Num servidor na nuvem:** os planos grátis que servem pedem cartão de crédito, e o ARENA só usa o que é grátis
  sem cartão.
- **No celular velho da bancada (Termux):** fica sempre ligado na tomada, e o programa parado gasta perto de 0% de
  CPU. Na tomada, o Android não entra no modo soneca (*Doze*), que cortaria a rede do Termux.

**Escolha:** o celular. O PC vira só mais um jogador. Comando no aparelho: `repasse ligar | desligar | estado |
registro | testar`. Ele sobe sozinho quando o celular liga.

## Decisão 3: quantas portas abrir?

Cada porta aberta no roteador é uma porta a mais para vigiar. O repasse do RetroArch e o pedido do código usam a
**mesma porta (55440, TCP)**: o repasse olha os 4 primeiros bytes da conversa ("GET " ou "POST" é o ARENA pedindo o
código; "RATS" ou "RATL" é o RetroArch). **Uma porta só.**

## Decisão 4: como o código encontra a sala, sem lista?

1. O ARENA de quem abre pede um código (`POST /sala`). O repasse sorteia 6 números e anota o endereço de quem pediu.
2. Logo depois, o RetroArch dele pede uma sessão de repasse (`RATS`). Ele sai do **mesmo endereço exato**, e é assim
   que o repasse sabe que aquela sessão é daquele código.
3. Quem entra digita o código; o ARENA dele pergunta ao repasse (`GET /sala/<código>`) e recebe a sessão, que vai para
   o RetroArch no `--mitm-session`.

Um RetroArch que chega **sem** reserva é recusado: o repasse não fica aberto para qualquer um usar.

## Decisão 5: quanta segurança é o bastante?

O repasse fica de frente para a internet, num celular. Os limites, todos no código:

- até 2 salas abertas por internet, 32 no total, 6 horas de vida por sala;
- 30 consultas de código por minuto por internet (no IPv6, conta o bloco /64 inteiro da casa);
- 60 códigos errados a cada 10 minutos por vizinhança de rede (/24 do IPv4, /48 do IPv6);
- quem liga e não diz nada em 10 segundos é desligado; ligação parada por 5 minutos cai;
- nada gravado em disco (nem endereço de ninguém); a regra do firewall também não registra o tráfego.

**Risco aceito:** muitas redes diferentes tentando códigos ao mesmo tempo. Um bloqueio geral contra isso foi testado
e descartado, porque qualquer pessoa poderia disparar o bloqueio de propósito e travar todo mundo. O pior caso é um
estranho entrar como jogador numa partida. O RetroArch mostra na tela o apelido de quem entrou, e fechar o jogo
fecha a sala.

## O caminho de um pacote (bancada do professor)

```
aluno A (casa 1) ─┐                                            ┌─ aluno B (casa 2)
                  └─> internet ─> roteador da casa do professor
                         (porta 55440 encaminhada para o firewall)
                      ─> firewall (VIP: porta 55440 da WAN -> celular na DMZ)
                      ─> celular, Termux: repasse_proprio.py
```

O que precisa existir, em ordem:

1. **Endereço público de verdade.** Se a operadora usa CGNAT (o roteador recebe um endereço 100.64.x.x ou outro
   endereço privado na WAN), ninguém de fora chega, com nenhuma regra. Para conferir, compare o endereço da WAN na página
   do roteador com o de um site de "meu IP": se forem diferentes, é CGNAT. Nesse caso a saída é pedir à operadora um IP
   público, ou usar IPv6 se ela der.
2. **Encaminhamento no roteador da operadora:** porta 55440 TCP para o firewall. Se o roteador estiver em modo ponte,
   esse passo não existe.
3. **Firewall:** o VIP `ARENA_REPASSE_VIP` e a regra `INTERNET_PARA_REPASSE_ARENA` (no projeto de infraestrutura do
   professor, aplicados junto com as outras regras).
4. **Celular:** `repasse estado` mostra "ligado".
5. **Teste de fora:** um celular no 4G (Wi-Fi desligado) com o ARENA, endereço do repasse em Amigos → Partidas entre
   casas → **Testar**.

## O endereço que o aluno escreve

É o endereço público da casa do professor (ou um nome de DNS que aponte para ele), com `:55440` se precisar.
**Ele não vai no pacote público do ARENA**: publicar o endereço da casa de alguém na internet é pedir problema. O
professor passa na aula. Se a operadora troca o endereço de vez em quando, um nome de DNS dinâmico grátis evita
repassar o endereço novo, mas isso exige criar uma conta num serviço, e essa decisão é do professor.

## Testes

- `servidor\tests\test_repasse_proprio.py`: o protocolo byte a byte e os limites, com o repasse de verdade aberto
  no PC.
- `testes\teste_repasse_proprio_retroarch.py`: dois RetroArch de verdade pelo túnel. Com `ARENA_REPASSE=host:porta`,
  usa um repasse que já está no ar. Em 10/11/2026 passou pelo repasse do celular da bancada, na rede de casa, com ping
  de 45 ms.
- `testes\teste_repasse_proprio_pelo_arena.py`: o ARENA de verdade abre com código, entra pelo código e explica os
  erros.
