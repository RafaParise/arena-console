package com.arena.console

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MediaMountReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        val mountedUri = intent.data?.path
        Log.i("ARENA-STORAGE", "Evento de mídia detectado: $action ($mountedUri)")

        val pendingResult = goAsync()
        Thread {
            try {
                val prefs = context.getSharedPreferences("arena_prefs", Context.MODE_PRIVATE)
                val port = prefs.getInt("server_port", 8080)
                val allPaths = StorageDiscovery.discoverAllStoragePaths(context).toMutableSet()
                if (!mountedUri.isNullOrBlank()) {
                    allPaths.add(mountedUri)
                }

                val jsonBody = JSONObject()
                    .put("paths", JSONArray(allPaths.toList()))
                    .toString()

                val url = URL("http://127.0.0.1:$port/api/storage/sync")
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 3000
                    readTimeout = 10000
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json")
                }

                conn.outputStream.use { it.write(jsonBody.toByteArray(Charsets.UTF_8)) }
                val code = conn.responseCode
                Log.i("ARENA-STORAGE", "Sincronização Rust HTTP $code")
                conn.disconnect()
            } catch (e: Exception) {
                Log.w("ARENA-STORAGE", "Falha ao sincronizar storage com servidor Rust: ${e.message}")
            } finally {
                pendingResult.finish()
            }
        }.start()
    }
}