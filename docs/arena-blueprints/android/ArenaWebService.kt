package com.arena.console

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat

class ArenaWebService : Service() {
    private lateinit var runner: ArenaWebRunner

    override fun onCreate() {
        super.onCreate()
        runner = ArenaWebRunner(applicationContext)
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            runner.stop()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return START_NOT_STICKY
        }

        val prefs = getSharedPreferences("arena_prefs", Context.MODE_PRIVATE)
        val port = intent?.getIntExtra(EXTRA_PORT, prefs.getInt("server_port", 8080)) ?: 8080
        prefs.edit().putInt("server_port", port).apply()

        val notification = buildNotification(port)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            ServiceCompat.startForeground(
                this,
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        runner.start(port)
        return START_STICKY
    }

    override fun onDestroy() {
        runner.stop()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Servidor ARENA Console",
                NotificationManager.IMPORTANCE_LOW
            )
            val nm = getSystemService(NotificationManager::class.java)
            nm?.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(port: Int): Notification {
        val openIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, ArenaWebService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("ARENA Console Ativo")
            .setContentText("Servidor local Rust rodando na porta $port")
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setOngoing(true)
            .setContentIntent(openIntent)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Encerrar", stopIntent)
            .build()
    }

    companion object {
        const val CHANNEL_ID = "arena_web_service_channel"
        const val NOTIFICATION_ID = 8080
        const val EXTRA_PORT = "extra_port"
        const val ACTION_STOP = "com.arena.console.ACTION_STOP_SERVER"

        fun start(context: Context, port: Int = 8080) {
            val intent = Intent(context, ArenaWebService::class.java).putExtra(EXTRA_PORT, port)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
    }
}