# Como contribuir com o ARENA

Obrigado por querer ajudar! O ARENA é usado em sala de aula, por alunos
menores de idade, e o próprio código é material de estudo. Por isso há
algumas regras que não mudam. Leia também o
[código de conduta](CODE_OF_CONDUCT.md).

## Relatar um problema

1. Confira a versão do ARENA (aparece no topo da tela, ao lado do nome).
2. Rode o **`VERIFICAR.bat`** — ele confere e conserta a maior parte dos
   problemas sozinho. Para a partida a dois, rode o **`PARTIDA.bat`**.
3. Se não resolveu, abra uma issue com o modelo **Relatar um problema**:
   versão do ARENA, versão do Windows, console e nome do jogo, o passo a
   passo, o que você esperava e o que aconteceu, e o resultado do
   `VERIFICAR.bat`.

**Nunca anexe** jogo, BIOS, firmware, save, o banco de recordes (`arena.db`)
ou qualquer dado de aluno (nome, escola, turma, foto, e-mail). As issues são
públicas.

## Sugerir uma melhoria

Abra uma issue com o modelo **Sugerir uma melhoria**: o que você quer fazer,
por que ajuda (de preferência um caso real de sala de aula) e como imagina
que funcione.

## Contribuir com código

As regras abaixo são o ambiente real das escolas. Uma mudança que quebra
alguma delas não entra, por melhor que seja:

| Regra | Por quê |
|---|---|
| **Python só com a biblioteca padrão** (sem `pip install`) | Computador de escola não deixa instalar nada |
| **Nada que peça senha de administrador** | Conta de aluno não tem |
| **Roda de pen drive**: caminhos relativos, nada gravado fora da pasta do ARENA | O ARENA vai de um computador para outro |
| **Funciona sem internet** | Internet é bônus, nunca requisito |
| **Leve**: a régua é um notebook com Celeron N5100, sem AVX ([`docs/MAQUINA-ALVO.md`](docs/MAQUINA-ALVO.md)) | É o computador mais fraco da escola |
| **Código, comentários e textos da tela em português do Brasil** | Quem estuda o código são alunos do ensino médio |
| **Sem gravação de vídeo nem transmissão ao vivo** | Decisão para proteger alunos menores de idade |

Antes de enviar:

1. Rode a bateria de testes (a mesma do `RODAR_TESTES.bat`) e confira que
   tudo passa:
   ```
   servidor\python\python.exe servidor\tests\run.py
   ```
2. Mudou uma função que o usuário vê? Atualize o guia correspondente
   (`LEIA-ME.md` e os guias `1` a `6`) na mesma mudança.
3. Corrigiu um defeito? Acrescente um teste que teria pegado o defeito
   (`servidor\tests\` ou `testes\`), com um comentário contando o que
   aconteceu.
4. Confira que nada proibido vai junto:
   ```
   servidor\python\python.exe ferramentas\conferir_antes_de_publicar.py
   ```
   Ela recusa BIOS, jogos, saves, o banco de recordes, senhas, tokens e
   e-mails de aluno ou institucionais. (Quem trabalha na pasta do projeto usa
   o `SINCRONIZAR.bat`, que já roda essa conferência.)
5. Abra o pull request para o ramo `main`, descrevendo o que mudou, por quê e
   como você testou. Pull request pequeno, de um assunto só, é revisado mais
   rápido.

O projeto é mantido por um professor só, no tempo que sobra das aulas: a
resposta pode demorar alguns dias.

## Licença

Ao contribuir, você concorda que a sua contribuição seja distribuída sob a
licença do projeto, a [GPL-3.0](LICENSE).
