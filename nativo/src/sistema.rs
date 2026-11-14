//! O pouco que o servidor nativo pede direto ao sistema (sem biblioteca de fora): nao morrer com o Ctrl+C (quem
//! decide e' o Python, que fecha direito e devolve o codigo da saida) e, no Linux e no Android, levar o Python junto
//! se o nativo for fechado a forca.

#[cfg(windows)]
mod windows {
    type Bool = i32;
    type Manipulador = unsafe extern "system" fn(u32) -> Bool;
    extern "system" {
        fn SetConsoleCtrlHandler(rotina: Option<Manipulador>, juntar: Bool) -> Bool;
    }

    /// O Ctrl+C e o Ctrl+Break chegam aos dois (o nativo e o Python, que estao na mesma janela). O nativo so diz
    /// "tratei" e espera o Python fechar: a rotina nao passa para o Python (com o SetConsoleCtrlHandler(NULL, TRUE),
    /// o "ignorar" passaria, e o Ctrl+C deixaria de fechar o ARENA).
    unsafe extern "system" fn tratar(evento: u32) -> Bool {
        // 0 = Ctrl+C, 1 = Ctrl+Break. Fechar a janela (2) e sair da conta (5, 6) seguem o caminho normal.
        if evento == 0 || evento == 1 {
            1
        } else {
            0
        }
    }

    pub fn ignorar_ctrl_c() {
        unsafe {
            SetConsoleCtrlHandler(Some(tratar), 1);
        }
    }
}

#[cfg(unix)]
mod unix {
    use std::os::raw::c_int;
    extern "C" {
        fn signal(sinal: c_int, rotina: extern "C" fn(c_int)) -> usize;
        fn prctl(opcao: c_int, ...) -> c_int;
    }
    const SIGINT: c_int = 2;
    const SIGKILL: c_int = 9;
    const PR_SET_PDEATHSIG: c_int = 1;

    extern "C" fn nada(_sinal: c_int) {}

    /// Uma rotina (e nao o "ignorar"): rotina volta ao padrao no exec, entao o Python ainda recebe o Ctrl+C.
    pub fn ignorar_ctrl_c() {
        unsafe {
            signal(SIGINT, nada);
        }
    }

    /// Chamado no processo filho, logo antes do exec do Python: se o nativo morrer (o Android fecha o app a forca),
    /// o Linux mata o Python junto, e ninguem fica segurando a porta.
    pub fn morrer_com_o_pai() {
        unsafe {
            prctl(PR_SET_PDEATHSIG, SIGKILL as std::os::raw::c_ulong);
        }
    }
}

#[cfg(windows)]
pub use windows::ignorar_ctrl_c;

#[cfg(unix)]
pub use unix::{ignorar_ctrl_c, morrer_com_o_pai};

/// Um numero aleatorio de 64 bits, do sorteio do proprio sistema (o RandomState do Rust usa o gerador do sistema:
/// BCryptGenRandom no Windows, getrandom no Linux e no Android).
pub fn sorteio() -> u64 {
    use std::collections::hash_map::RandomState;
    use std::hash::{BuildHasher, Hasher};
    let mut h = RandomState::new().build_hasher();
    h.write_u64(std::process::id() as u64);
    h.finish()
}

/// Um segredo de 32 letras (128 bits) para o nativo e o Python se reconhecerem.
pub fn segredo() -> String {
    format!("{:016x}{:016x}", sorteio(), sorteio())
}
