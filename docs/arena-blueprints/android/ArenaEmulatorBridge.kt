package com.arena.console

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class ArenaEmulatorBridge(
    private val context: Context,
    private val webView: WebView
) {
    private fun isLocalOrigin(): Boolean {
        var url: String? = null
        webView.post { url = webView.url }
        val current = webView.url ?: url ?: return true
        return current.startsWith("http://127.0.0.1:") || current.startsWith("http://localhost:")
    }

    private fun isPackageInstalled(pkg: String): Boolean {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                context.packageManager.getPackageInfo(
                    pkg,
                    PackageManager.PackageInfoFlags.of(0)
                )
            } else {
                @Suppress("DEPRECATION")
                context.packageManager.getPackageInfo(pkg, 0)
            }
            true
        } catch (_: Exception) {
            false
        }
    }

    @JavascriptInterface
    fun isAndroidNative(): Boolean = isLocalOrigin()

    @JavascriptInterface
    fun getInstalledEmulators(): String {
        if (!isLocalOrigin()) {
            return JSONObject()
                .put("emulators", JSONObject())
                .put("systems", JSONArray())
                .toString()
        }

        val hasRetroArch = isPackageInstalled("com.retroarch.aarch64") ||
            isPackageInstalled("com.retroarch")
        val hasPcsx2 = isPackageInstalled("xyz.aethersx2.android")
        val hasDolphin = isPackageInstalled("org.dolphinemu.dolphinemu")
        val hasPpsspp = isPackageInstalled("org.ppsspp.ppssppgold") ||
            isPackageInstalled("org.ppsspp.ppsspp")
        val hasDuckStation = isPackageInstalled("com.github.stenzek.duckstation")
        val hasMupen64 = isPackageInstalled("org.mupen64plusae.v3.fzurita.pro") ||
            isPackageInstalled("org.mupen64plusae.v3.fzurita")

        val emulatorsJson = JSONObject()
            .put("retroarch", hasRetroArch)
            .put("pcsx2", hasPcsx2)
            .put("dolphin", hasDolphin)
            .put("ppsspp", hasPpsspp)
            .put("duckstation", hasDuckStation)
            .put("mupen64", hasMupen64)

        val systems = JSONArray()
        if (hasRetroArch) {
            listOf("snes", "nes", "gba", "gbc", "megadrive", "dreamcast", "arcade")
                .forEach { systems.put(it) }
        }
        if (hasPcsx2) systems.put("ps2")
        if (hasDolphin) {
            systems.put("gc")
            systems.put("wii")
        }
        if (hasPpsspp) systems.put("psp")
        if (hasDuckStation || hasRetroArch) systems.put("ps1")
        if (hasMupen64) systems.put("n64")

        return JSONObject()
            .put("emulators", emulatorsJson)
            .put("systems", systems)
            .toString()
    }

    @JavascriptInterface
    fun launchGame(emulator: String, romPath: String, coreName: String): Boolean {
        if (!isLocalOrigin()) return false
        val romFile = File(romPath)
        if (!romFile.exists()) {
            Log.e("ARENA-IPC", "ROM não encontrada: $romPath")
            return false
        }

        return try {
            val intent = when (emulator.lowercase()) {
                "retroarch" -> {
                    val pkg = if (isPackageInstalled("com.retroarch.aarch64")) {
                        "com.retroarch.aarch64"
                    } else {
                        "com.retroarch"
                    }
                    val libCore = "/data/data/$pkg/cores/${coreName}_libretro_android.so"
                    Intent(Intent.ACTION_MAIN).apply {
                        component = ComponentName(
                            pkg,
                            "com.retroarch.browser.retroactivity.RetroActivityFuture"
                        )
                        putExtra("ROM", romFile.absolutePath)
                        putExtra("LIBRETRO", libCore)
                        putExtra("CONFIGFILE", "/storage/emulated/0/Android/data/$pkg/files/retroarch.cfg")
                        putExtra("IME", "com.android.inputmethod.latin/.LatinIME")
                    }
                }
                "pcsx2", "aethersx2", "nethersx2" -> {
                    Intent(Intent.ACTION_MAIN).apply {
                        component = ComponentName(
                            "xyz.aethersx2.android",
                            "xyz.aethersx2.android.EmulationActivity"
                        )
                        putExtra("bootPath", romFile.absolutePath)
                    }
                }
                "dolphin" -> {
                    Intent(Intent.ACTION_MAIN).apply {
                        component = ComponentName(
                            "org.dolphinemu.dolphinemu",
                            "org.dolphinemu.dolphinemu.ui.main.MainActivity"
                        )
                        putExtra("AutoStartFile", romFile.absolutePath)
                    }
                }
                "ppsspp" -> {
                    val pkg = if (isPackageInstalled("org.ppsspp.ppssppgold")) {
                        "org.ppsspp.ppssppgold"
                    } else {
                        "org.ppsspp.ppsspp"
                    }
                    Intent(Intent.ACTION_VIEW).apply {
                        setPackage(pkg)
                        setDataAndType(Uri.fromFile(romFile), "application/octet-stream")
                    }
                }
                "duckstation" -> {
                    Intent(Intent.ACTION_MAIN).apply {
                        component = ComponentName(
                            "com.github.stenzek.duckstation",
                            "com.github.stenzek.duckstation.EmulationActivity"
                        )
                        putExtra("bootPath", romFile.absolutePath)
                    }
                }
                "mupen64" -> {
                    val pkg = if (isPackageInstalled("org.mupen64plusae.v3.fzurita.pro")) {
                        "org.mupen64plusae.v3.fzurita.pro"
                    } else {
                        "org.mupen64plusae.v3.fzurita"
                    }
                    Intent(Intent.ACTION_VIEW).apply {
                        setPackage(pkg)
                        setDataAndType(Uri.fromFile(romFile), "application/octet-stream")
                    }
                }
                else -> return false
            }

            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            true
        } catch (e: Exception) {
            Log.e("ARENA-IPC", "Falha ao abrir emulador $emulator: ${e.message}")
            false
        }
    }
}