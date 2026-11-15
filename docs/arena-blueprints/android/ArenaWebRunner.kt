package com.arena.console

import android.content.Context
import android.util.Log
import java.io.File

class ArenaWebRunner(private val context: Context) {
    @Volatile
    private var process: Process? = null

    @Synchronized
    fun start(port: Int = 8080) {
        if (isRunning()) {
            Log.i("ARENA-RUST", "Servidor Rust já está em execução na porta $port")
            return
        }

        val nativeDir = context.applicationInfo.nativeLibraryDir
        val binary = File(nativeDir, "libarena_web.so")
        if (!binary.exists()) {
            Log.e("ARENA-RUST", "Binário não encontrado em ${binary.absolutePath}")
            return
        }
        if (!binary.canExecute()) {
            binary.setExecutable(true)
        }

        val storagePaths = StorageDiscovery.discoverAllStoragePaths(context).joinToString(":")
        val pb = ProcessBuilder(binary.absolutePath)
            .directory(context.filesDir)
            .redirectErrorStream(true)

        pb.environment().apply {
            put("ARENA_PORT", port.toString())
            put("ARENA_DATA_DIR", context.filesDir.absolutePath)
            put("ARENA_STORAGE_PATHS", storagePaths)
            put("RUST_LOG", "info")
        }

        val proc = pb.start()
        process = proc
        Log.i("ARENA-RUST", "libarena_web.so iniciado na porta $port (storage=$storagePaths)")

        Thread {
            try {
                proc.inputStream.bufferedReader().useLines { lines ->
                    lines.forEach { line -> Log.i("ARENA-RUST", line) }
                }
            } catch (_: Exception) {
            }
        }.start()
    }

    fun isRunning(): Boolean {
        val p = process ?: return false
        return try {
            p.exitValue()
            false
        } catch (_: IllegalThreadStateException) {
            true
        }
    }

    @Synchronized
    fun stop() {
        process?.destroy()
        process = null
        Log.i("ARENA-RUST", "Servidor Rust encerrado")
    }
}