/*
 * O lancador do Python do ARENA no Android (item 14).
 *
 * No Windows o ARENA roda com o python.exe e no Linux com o python3 do
 * python-linux. O Python do Android (o do Chaquopy, ferramentas\python_android.py)
 * vem so como biblioteca (libpython3.13.so), sem o programa "python". Este e'
 * o programa: ele entrega a linha de comando inteira ao Python, como o
 * python.exe faz.
 *
 * O nome dele no APK e' libarenapython.so: o Android so deixa um app rodar
 * programa que esteja na pasta de bibliotecas dele, e so copia para la os
 * arquivos lib*.so. Quem o roda e' o ArenaServico.java (o servidor do ARENA).
 */

/* De Python.h: a mesma funcao que o main do python.exe chama. */
extern int Py_BytesMain(int argc, char **argv);

int main(int argc, char **argv)
{
   return Py_BytesMain(argc, argv);
}
