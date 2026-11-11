## Parity: 83.8 / 100

features 83.8  (20 counted, must-haves 5 of 6 done)

Not shippable yet: 1 must-have features are not done.

## By area, weakest first
- escala                        80.6  (10 features)
- quadros                       86.8  (10 features)

## Missing, in build order
- [must] quadros: Gerar quadros copiando a tela (LSFG do LS; MSM FG / DLSS MFG / XeSS MFG do MFG), partial  (usa o MFG Super Motion (ou o LS) instalado, configurado e aberto pelo ARENA (servidor\mfg.py, servidor\lossless.py); nativo em Python puro nao e' viavel: precisa de Direct3D 12 e a placa da escola nao aguenta (UHD 730 do proprio MFG: 13,6 ms por par))
- [could] escala: NIS da NVIDIA (LS), no  (FSR e Catmull cobrem; o NIS (licenca MIT) pode entrar depois)
- [could] escala: SGSR da Qualcomm (LS), no  (feito para placa de celular: candidato para o Android numa proxima versao)
- [could] escala: Nitidez ajustavel (sharpness do LS; sharpness e over_sharpness do MFG), partial  (RCAS automatico; sem controle de intensidade)
- [could] escala: Vizinho mais proximo (Nearest do LS; upscaler=3 do MFG), partial  (o "original" desenha sem filtro; sem opcao propria)
- [could] escala: xBR (LS), partial  (o ScaleFX (suave) faz o mesmo papel e pesou menos (+5.7 contra +8.8 pontos de placa))
- [could] quadros: Aprender por jogo (Adaptive Motion Learning do MFG), partial  (o Desempenho que aprende ajusta por console sem desenhar o estudo na tela; o AML fica desligado (desenha no jogo))
- [could] quadros: Limitar quadros (frame_limit do MFG; FPS limit do LS), partial  (o vsync do ARENA limita; sem opcao propria)

## Left out on purpose (not scored)
- LS1 (escala propria do LS): algoritmo fechado do Lossless Scaling; nada para estudar alem do resultado
- VRR e HDR (MFG e LS): as maquinas da escola nao tem tela VRR nem HDR
- Contador de quadros desenhado no jogo (Draw FPS do LS; counter do MFG): o ARENA mede sem desenhar nada na tela (servidor\desempenho.py)
- Compartilhar a imagem com outro programa (Spout do MFG): transmissao e gravacao desligadas de proposito no ARENA (dados dos alunos)

## Yours, not in the original (not scored)
- Quadros de verdade no PS2: patch 60 FPS do proprio PCSX2
- Janela leve do navegador (perfil so do ARENA)
- Descanso do fundo animado
- 60 quadros no GameCube e no Wii (codigos do Dolphin)
