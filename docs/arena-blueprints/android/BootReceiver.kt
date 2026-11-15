package com.arena.console

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        Log.i("ARENA-BOOT", "Boot detectado ($action)")
        val prefs = context.getSharedPreferences("arena_prefs", Context.MODE_PRIVATE)
        val port = prefs.getInt("server_port", 8080)
        ArenaWebService.start(context.applicationContext, port)
    }
}