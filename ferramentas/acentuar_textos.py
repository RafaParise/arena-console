# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 7: acentua as frases que o servidor manda para a TELA.

So mexe dentro dos textos que chegam ao aluno -- os mesmos que
testes\textos_sem_acento.py encontra: self.erro(...) inteiro (todas as
linhas da frase), rotulos em tuplas e as chaves de recado do consoles.json.
Comentario e print da janela preta nao sao tocados.

Uso:
    servidor\python\python.exe ferramentas\acentuar_textos.py          (mostra)
    servidor\python\python.exe ferramentas\acentuar_textos.py --gravar (grava)
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Palavra sem ambiguidade -> com acento. "esta" e "e" ficam de fora de
# proposito: podem ser "está"/"é" ou "esta"/"e" -- vao em FRASES, uma a uma.
PALAVRAS = {
    "nao": "não", "Nao": "Não", "estao": "estão", "voce": "você",
    "Voce": "Você", "voces": "vocês", "Voces": "Vocês", "so": "só",
    "So": "Só", "ja": "já", "Ja": "Já", "tambem": "também",
    "numero": "número", "codigo": "código", "endereco": "endereço",
    "conexao": "conexão", "conexoes": "conexões", "versao": "versão",
    "pagina": "página", "memoria": "memória", "atencao": "atenção",
    "invalido": "inválido", "invalida": "inválida",
    "possivel": "possível", "disponivel": "disponível", "ate": "até",
    "ninguem": "ninguém", "alguem": "alguém", "entao": "então",
    "sera": "será", "audio": "áudio", "video": "vídeo",
    "informacao": "informação", "configuracao": "configuração",
    "configuracoes": "configurações", "funcao": "função",
    "opcao": "opção", "opcoes": "opções", "comeco": "começo",
    "proxima": "próxima", "ultima": "última", "unico": "único",
    "unica": "única", "nucleo": "núcleo", "nucleos": "núcleos",
    "copia": "cópia", "seguranca": "segurança", "espaco": "espaço",
    "proprio": "próprio", "propria": "própria", "especifico": "específico",
    "especifica": "específica", "Peca": "Peça", "OBRIGATORIO": "OBRIGATÓRIO",
    "obrigatorio": "obrigatório", "obrigatoria": "obrigatória",
    "necessario": "necessário", "necessaria": "necessária",
    "ninguem": "ninguém", "tres": "três", "sao": "são", "Sao": "São",
    "voce": "você", "pasta": "pasta", "pre": "pré", "intermediario":
    "intermediário", "rapido": "rápido", "lento": "lento",
    "emulacao": "emulação", "Emulacao": "Emulação", "simulacao": "simulação",
    "sincronizacao": "sincronização", "atualizacao": "atualização",
    "instalacao": "instalação", "permissao": "permissão",
    "conteudo": "conteúdo", "arquivo": "arquivo", "familia": "família",
    "compativel": "compatível", "incompativel": "incompatível",
    "maquina": "máquina", "maquinas": "máquinas", "tambem": "também",
    "pe": "pé", "ha": "há", "Ha": "Há", "apos": "após", "atraves": "através",
    "hospedeiro": "hospedeiro", "possiveis": "possíveis", "sessao": "sessão",
    "portatil": "portátil", "grafico": "gráfico", "graficos": "gráficos",
    "tambem": "também", "vem": "vem", "tera": "terá", "facil": "fácil",
    "dificil": "difícil", "periodo": "período", "minimo": "mínimo",
    "maximo": "máximo", "rapida": "rápida", "logica": "lógica",
    "partida": "partida", "variavel": "variável", "saida": "saída",
    "Saida": "Saída", "unicos": "únicos", "conexao": "conexão",
    "regiao": "região", "comeca": "começa", "alcanco": "alcanço", "alcanca": "alcança",
    "Direcao": "Direção", "Espaco": "Espaço", "Numero": "Número", "Nucleo": "Núcleo",
    "Codigo": "Código", "autorizacao": "autorização", "licenca": "licença", "colecao": "coleção",
    "distribuicao": "distribuição", "valido": "válido", "indisponivel": "indisponível",
    "numeros": "números", "botao": "botão", "indice": "índice", "catalogo": "catálogo", "Indice": "Índice", "voce": "você",
}

# Casos ambiguos: frase exata -> frase certa (conferidos um a um).
FRASES = [
    ("Este endereco e o proprio computador", "Este endereço é o próprio computador"),
    ("ARENA dele esta aberto", "ARENA dele está aberto"),
    ("de quem esta \"\n", "de quem está \"\n"),
    ("de quem esta ", "de quem está "),
    ("Esta plataforma \"\n", "Esta plataforma \"\n"),
    ("\"esta usando o", "\"está usando o"),
    ("nao esta mais no lugar", "não está mais no lugar"),
    ("Ele esta", "Ele está"), ("ele esta", "ele está"),
    ("jogo esta", "jogo está"), ("que esta", "que está"),
    ("rede esta", "rede está"), ("computador esta", "computador está"),
    ("arquivo esta", "arquivo está"), ("pasta esta", "pasta está"),
    ("disco esta", "disco está"), ("BIOS esta", "BIOS está"),
    ("nao esta ", "não está "), ("Nao e imagem", "Não é imagem"),
    ("RetroArch e pouco", "RetroArch é pouco"), ("nao e ", "não é "), ("so e ", "só é "), (" e o unico", " é o único"),
    ("nao da ", "não dá "), ("Voces tem ", "Vocês têm "), ("diagnostico e' so", "diagnóstico é só"),
    ("partida esta fechada", "partida está fechada"), ("isso e ", "isso é "), ("Isso e ", "Isso é "),
]


def trocar(texto):
    for velho, novo in FRASES:
        texto = texto.replace(velho, novo)
    return re.sub(r"\b[A-Za-z]+\b", lambda m: PALAVRAS.get(m.group(0), m.group(0)), texto)


def trechos_de_tela(nome, texto):
    """Devolve (inicio, fim) de cada trecho de texto que chega na tela."""
    trechos = []
    if nome.endswith(".py"):
        # self.erro( ... ) inteiro, contando parenteses fora de aspas.
        for m in re.finditer(r"self\.erro\(", texto):
            i, nivel, aspas = m.end(), 1, False
            while i < len(texto) and nivel:
                c = texto[i]
                if c == '"' and texto[i - 1] != "\\":
                    aspas = not aspas
                elif not aspas and c == "(":
                    nivel += 1
                elif not aspas and c == ")":
                    nivel -= 1
                i += 1
            trechos.append((m.end(), i))
        padroes = [r'"(?:rotulo|motivo|aviso|mensagem|titulo|acao|erro)"\s*:\s*("[^"]+"(?:\s*"[^"]+")*)',
                   r'return\s+"[a-z_]+",\s*("[^"]+")',
                   r'\("[a-z_.0-9]+",\s*"[a-z_]+",\s*("[^"]+")\)']
    else:
        padroes = [r'"(?:rotulo|motivo|aviso|mensagem|titulo|acao|erro|motivo_sem_partida|'
                   r'netplay_motivo|netplay_aviso)"\s*:\s*("(?:[^"\\]|\\.)+")']
    for p in padroes:
        for m in re.finditer(p, texto):
            trechos.append((m.start(1), m.end(1)))
    return trechos


# Segunda passada: mensagens de tela fora de self.erro (ValueError que vira
# erro na tela, dicas de controle, veredito do "testar partida"...). Linhas
# conferidas uma a uma; a linha seguinte entra junto quando continua a frase.
# De fora de proposito: chave interna ("ele nao tem", "nao medido"), print
# da janela preta, diagnostico.py e partida.py (ASCII de proposito).
LINHAS = {
    "acervo.py": [66, 183, 185, 220],
    "arena.py": [680, 718, 764, 1102, 1109, 1470, 1504, 1505, 1822, 2197, 2394,
                 2721, 2764, 2765, 2976, 2978, 3000, 3154, 3175, 3795, 3842,
                 3843, 3847, 3851, 3855, 3858, 3861, 3862, 3866, 4533, 4537,
                 4539, 4545],
    "barreiras.py": [257],
    "capas_online.py": [87],
    "cheats.py": [130, 198, 200, 202, 203, 260],
    "controles.py": [268, 273, 281, 286, 288, 297, 416, 428],
    "graficos.py": [803, 805, 815],
    "internet_archive.py": [137, 147, 151, 156, 171, 212, 213],
}


def trocar_por_linha(nome, texto):
    linhas = texto.split("\n")
    alvo = set()
    for n in LINHAS.get(nome, []):
        alvo.add(n - 1)
        seguinte = n
        while (seguinte < len(linhas) and linhas[seguinte].lstrip().startswith('"')
               and not re.match(r'\s*"[^"]*"\s*:', linhas[seguinte])):  # chave de dicionario nao
            alvo.add(seguinte)
            seguinte += 1
    for i in sorted(alvo):
        velho = linhas[i]
        novo = re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: trocar(m.group(0)), velho)
        if novo != velho:
            print("%s:%d: %s\n   -> %s" % (nome, i + 1, velho.strip()[:130], novo.strip()[:130]))
            linhas[i] = novo
    return "\n".join(linhas)


def principal():
    gravar = "--gravar" in sys.argv
    if "--linhas" in sys.argv:
        for nome in LINHAS:
            caminho = os.path.join(RAIZ, "servidor", nome)
            texto = open(caminho, encoding="utf-8").read()
            novo = trocar_por_linha(nome, texto)
            if gravar and novo != texto:
                with open(caminho, "w", encoding="utf-8", newline="") as f:
                    f.write(novo)
        return
    total = 0
    for nome in sorted(os.listdir(os.path.join(RAIZ, "servidor"))):
        if not nome.endswith((".py", ".json")):
            continue
        caminho = os.path.join(RAIZ, "servidor", nome)
        texto = open(caminho, encoding="utf-8").read()
        novo, deslocamento = texto, 0
        for inicio, fim in sorted(trechos_de_tela(nome, texto)):
            velho = texto[inicio:fim]
            # So as partes entre aspas mudam (nunca nome de variavel).
            trocado = re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: trocar(m.group(0)), velho)
            if trocado != velho:
                total += 1
                print("%s: %s\n   -> %s" % (nome, velho.strip()[:150], trocado.strip()[:150]))
                a, b = inicio + deslocamento, fim + deslocamento
                novo = novo[:a] + trocado + novo[b:]
                deslocamento += len(trocado) - len(velho)
        if gravar and novo != texto:
            with open(caminho, "w", encoding="utf-8", newline="") as f:
                f.write(novo)
    print("\n%d trecho(s) %s." % (total, "gravado(s)" if gravar else "a trocar (use --gravar)"))


if __name__ == "__main__":
    principal()
