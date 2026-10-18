# O ARENA no Android

O APK do ARENA é o **RetroArch 1.22.2 oficial para Android** (o mesmo RetroArch
do Windows, do Linux e do Chromebook) com a tela do ARENA na frente. Nada do
código do RetroArch muda: o montador troca só o nome do aplicativo, o ícone e
a tela que abre primeiro.

- `src/io/github/rafaparise/arena/ArenaActivity.java`: a tela do Android. Um
  WebView com a tela de sempre do ARENA (`launcher/`), com o servidor dentro
  da página do ARENA do Chromebook (`launcher/navegador`), e a ponte
  `ArenaAndroid`, que a página chama para achar a pasta do ARENA no aparelho
  (cartão SD, pen drive no cabo OTG ou memória do aparelho), listar e gravar
  arquivos dela e abrir o jogo no RetroArch nativo.
- `launcher/navegador/android.js`: o outro lado da ponte, na página.
- `ferramentas/preparar_android.py`: o SDK do Android e o emulador dos testes
  (fora do ARENA, em `%LOCALAPPDATA%\ARENA-android`).
- `ferramentas/montar_android.py`: monta e assina o APK (um por tipo de
  processador: `arm64-v8a`, o dos celulares e tablets, e `x86_64`).
- `ferramentas/android_nucleos.json`: a marca de cada núcleo do Android que
  vai no APK (o *nightly* do libretro conferido).

A chave que assina o APK fica fora do git, em
`%LOCALAPPDATA%\ARENA-android\assinatura`. Guarde uma cópia: sem ela, o APK
seguinte não instala por cima do anterior.
