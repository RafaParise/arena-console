"""A "mao" DENTRO da tela do ARENA no celular: roda JavaScript na pagina do app e le o que ela mostra.

Por que existe (25/10/2026): o celular_mao.py toca nas coordenadas da tela e le o que o Android
enxerga, mas o WebView do ARENA e' uma pagina so. Por aqui eu clico num botao pelo nome (id), leio o
texto de uma lista, mando um pedido ao servidor do app e ate meco o tempo de resposta, tudo sem
depender de coordenadas. Precisa do APK de teste (montar_android.py --teste), que liga a depuracao
do WebView, e do celular em Depuracao USB. Nada e' instalado no aparelho.

Uso (cada comando imprime o resultado em JSON):
    servidor\\python\\python.exe testes\\celular_pagina.py js "document.title"
    servidor\\python\\python.exe testes\\celular_pagina.py clicar "#btnAjustes"
    servidor\\python\\python.exe testes\\celular_pagina.py texto "#listaAparelho"
    servidor\\python\\python.exe testes\\celular_pagina.py rota /api/android/aparelho
    servidor\\python\\python.exe testes\\celular_pagina.py abrir_ajustes maquina      abre Ajustes e a aba
    servidor\\python\\python.exe testes\\celular_pagina.py rolar "#blocoAparelho"      leva o bloco para a tela

O aparelho e' sempre escolhido (o fisico, ou o da variavel ANDROID_SERIAL), como no celular_mao.py.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import celular_mao  # noqa: E402  (escolhe o aparelho e o adb)
import teste_android as t  # noqa: E402


def preparar():
    """Aponta o teste_android para o aparelho e o adb que o celular_mao escolheu (o celular, nunca o emulador)."""
    os.environ["ANDROID_SERIAL"] = celular_mao.escolher()
    t.ADB = celular_mao.ADB
    return t.Pagina(segundos=20)


def principal(argumentos):
    if not argumentos:
        print(__doc__)
        return 2
    verbo, resto = argumentos[0], argumentos[1:]
    pagina = preparar()
    try:
        if verbo == "js":
            resultado = pagina.avaliar(resto[0])
        elif verbo == "clicar":
            resultado = pagina.avaliar("(() => { const e = document.querySelector(%s); if (!e) return 'sem elemento'; e.click(); return 'clicado'; })()"
                                       % json.dumps(resto[0]))
        elif verbo == "texto":
            resultado = pagina.avaliar("(() => { const e = document.querySelector(%s); return e ? e.innerText : 'sem elemento'; })()"
                                       % json.dumps(resto[0]))
        elif verbo == "rota":
            resultado = pagina.pedir(resto[0], json.loads(resto[1]) if len(resto) > 1 else None)
        elif verbo == "abrir_ajustes":
            aba = resto[0] if resto else "simples"
            resultado = pagina.avaliar("(() => { document.querySelector('#btnAjustes').click(); "
                                       "const a = document.querySelector('[data-aba=%s]'); if (a) a.click(); return !!a; })()" % aba)
        elif verbo == "rolar":
            resultado = pagina.avaliar("(() => { const e = document.querySelector(%s); if (!e) return 'sem elemento'; "
                                       "e.scrollIntoView({block: 'start'}); return 'rolado'; })()" % json.dumps(resto[0]))
        else:
            print("verbo desconhecido: %s\n%s" % (verbo, __doc__))
            return 2
        print(json.dumps(resultado, ensure_ascii=False, indent=2) if not isinstance(resultado, str) else resultado)
        return 0
    finally:
        pagina.fechar()


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
