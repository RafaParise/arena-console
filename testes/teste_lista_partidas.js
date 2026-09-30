// Confere a logica da lista "Entrar na partida do amigo" (launcherpp.js)
// sem navegador: extrai as funcoes do arquivo e simula o <select>.
//
// Precisa do Node (so o PC de desenvolvimento tem; NAO faz parte da bateria
// nem do pacote). Criado na revisao de 30/09/2026, que achou aqui: com duas
// partidas abertas, a que a tela tinha marcado sozinha continuava marcada.
//
// Uso: node testes	este_lista_partidas.js
const fs = require("fs");
const path = require("path");
const fonte = fs.readFileSync(path.join(__dirname, "..", "launcher", "app.js"), "utf8");

function extrair(nome) {
  const inicio = fonte.indexOf(`function ${nome}(`);
  if (inicio < 0) throw new Error("nao achei " + nome);
  let i = fonte.indexOf("{", inicio), prof = 0;
  for (; i < fonte.length; i++) {
    if (fonte[i] === "{") prof++;
    else if (fonte[i] === "}" && --prof === 0) break;
  }
  return fonte.slice(inicio, i + 1);
}

class Opcao { constructor() { this.value = ""; this.textContent = ""; this.dataset = {}; } }
class Select {
  constructor() { this.options = []; this.dataset = {}; this._sel = 0; this.reconstrucoes = 0; }
  replaceChildren() { this.options = []; this._sel = 0; this.reconstrucoes++; }
  append(o) { this.options.push(o); }
  get value() { return this.options[this._sel] ? this.options[this._sel].value : ""; }
  set value(v) { const i = this.options.findIndex((o) => o.value === v); if (i >= 0) this._sel = i; }
}
const lista = new Select();
global.document = { createElement: () => new Opcao() };
global.$ = (sel) => (sel === "#listaAmigosPartida" ? lista : null);
global.estado = {};
eval(extrair("preencherAmigosPartida") + "\nglobal.preencher = preencherAmigosPartida;");
eval(extrair("amigoEstaOnline") + "\nglobal.online = amigoEstaOnline;");

let falhas = 0;
function confere(nome, ok, extra) {
  console.log(`  [${ok ? "OK" : "FALHOU"}] ${nome}${extra ? " " + extra : ""}`);
  if (!ok) falhas++;
}
const textos = () => lista.options.map((o) => o.textContent);

// 1. Nada encontrado
estado.partidasEncontradas = [];
preencher();
confere("vazia: explica o que fazer", /Nenhuma partida aberta/.test(textos()[0]), JSON.stringify(textos()));

// 2. Uma partida: ja vem marcada
estado.jogoDaPartida = { id: "jogos/pessoais/super nintendo/sb4.smc" };
estado.partidasEncontradas = [
  { url: "http://10.0.0.2:8777", apelido: "Ana", partida_aberta: true, jogo_partida: "Super Bomberman 4",
    jogo_id_partida: "jogos/turma/super nintendo/sb4.smc" },
  { url: "http://10.0.0.5:8777", apelido: "Bia", partida_aberta: false }];
preencher();
confere("uma partida: so ela na lista", lista.options.length === 1, JSON.stringify(textos()));
confere("uma partida: ja marcada", lista.value === "http://10.0.0.2:8777");
confere("mesmo arquivo em outra pasta NAO e' 'OUTRO JOGO'", !/OUTRO JOGO/.test(textos()[0]), textos()[0]);

// 3. Nada mudou: nao redesenha (nao fecha a lista aberta)
const antes = lista.reconstrucoes;
preencher();
confere("sem mudanca: nao redesenha", lista.reconstrucoes === antes);

// 4. Duas partidas: ninguem marcado
estado.partidasEncontradas.push({ url: "http://10.0.0.9:8777", apelido: "Caio", partida_aberta: true,
  jogo_partida: "Mega Bomberman", jogo_id_partida: "jogos/pessoais/mega drive/mb.md" });
preencher();
confere("duas partidas: 3 linhas (escolha + 2)", lista.options.length === 3, JSON.stringify(textos()));
confere("duas partidas: nenhuma marcada", lista.value === "");
confere("jogo diferente marcado 'OUTRO JOGO'", /OUTRO JOGO: Mega Bomberman/.test(textos()[2]), textos()[2]);

// 5. Aluno escolhe, a lista atualiza com mudanca: escolha mantida
lista.value = "http://10.0.0.9:8777"; estado.partidaEscolhida = lista.value;  // evento change
estado.partidasEncontradas[0].jogo_partida = "Super Bomberman 4 (novo nome)";
preencher();
confere("escolha mantida depois de atualizar", lista.value === "http://10.0.0.9:8777");

// 6. Online: apelidos (Sincronizar), vigia e busca recente
estado.servidoresOnline = ["Bia"];
confere("online pelo vigia (apelido)", Boolean(online({ apelido: "Bia", url: "x" }, [])));
confere("online pelo Sincronizar (apelido)", Boolean(online({ apelido: "Dani", url: "y" }, ["Dani"])));
estado.partidasEm = Date.now();
confere("online pela busca recente (id)",
  Boolean(online({ apelido: "Ana", id: "", url: "http://10.0.0.2:8777" }, [])));
estado.partidasEm = Date.now() - 120000;
confere("busca velha (2 min) nao vale", !online({ apelido: "Ana", id: "", url: "http://10.0.0.2:8777" }, []));
confere("fora do ar", !online({ apelido: "Zeca", url: "http://9.9.9.9:8777" }, []));

// 7. Codigo de aparelho repetido (imagem clonada): so o endereco decide
estado.partidasEm = Date.now();
estado.servidoresOnline = [];
estado.partidasEncontradas = [
  { url: "http://10.0.0.7:8777", id: "igual", apelido: "Eva", partida_aberta: true, jogo_partida: "X" }];
// Um so aparelho com aquele codigo: e' o amigo que trocou de IP (caso comum).
confere("um so com o codigo: vale como IP novo do amigo",
  Boolean(online({ apelido: "Fabi", id: "igual", url: "http://10.0.0.8:8777" }, [])));
estado.partidasEncontradas.push({ url: "http://10.0.0.8:8777", id: "igual", apelido: "Fabi" });
const achado = online({ apelido: "Fabi", id: "igual", url: "http://10.0.0.8:8777" }, []);
confere("codigo repetido: cada um pelo seu endereco", achado && achado.apelido === "Fabi");
confere("IP mudou e o codigo e' unico: acha pelo codigo",
  Boolean(online({ apelido: "Gil", id: "unico", url: "http://10.0.0.1:8777" },
    [{ url: "http://10.0.0.99:8777", id: "unico", apelido: "Gil" }])));

console.log(falhas ? `RESULTADO: FALHOU (${falhas})` : "RESULTADO: PASSOU");
process.exit(falhas ? 1 : 0);
