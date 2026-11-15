package com.arena.console

import android.content.Context
import android.os.Build
import android.os.Environment
import android.os.storage.StorageManager
import java.io.File

object StorageDiscovery {
    fun discoverAllStoragePaths(context: Context): List<String> {
        val paths = LinkedHashSet<String>()

        val primary = Environment.getExternalStorageDirectory()
        if (primary != null && primary.exists() && primary.canRead()) {
            paths.add(primary.absolutePath)
        }

        val storageManager = context.getSystemService(Context.STORAGE_SERVICE) as? StorageManager
        if (storageManager != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            for (volume in storageManager.storageVolumes) {
                val dir = volume.directory
                if (dir != null && dir.exists() && dir.canRead()) {
                    paths.add(dir.absolutePath)
                }
            }
        }

        // Fallback direto para montagens externas em /storage e /mnt/media_rw (TV Boxes)
        listOf(File("/storage"), File("/mnt/media_rw")).forEach { base ->
            base.listFiles()?.forEach { child ->
                if (child.isDirectory &&
                    child.name != "emulated" &&
                    child.name != "self" &&
                    child.canRead()
                ) {
                    paths.add(child.absolutePath)
                }
            }
        }

        return paths.toList()
    }
}