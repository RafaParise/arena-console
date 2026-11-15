package com.arena.console

import android.annotation.SuppressLint
import android.os.Build
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.view.WindowInsets
import android.view.WindowManager
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import java.net.InetSocketAddress
import java.net.Socket

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private val serverPort = 8080

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        applyImmersiveMode()

        webView = WebView(this).apply {
            setLayerType(View.LAYER_TYPE_HARDWARE, null)
            isFocusable = true
            isFocusableInTouchMode = true
            requestFocus()

            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                allowFileAccess = true
                mediaPlaybackRequiresUserGesture = false
                cacheMode = WebSettings.LOAD_DEFAULT
            }

            setOnApplyWindowInsetsListener { v, _ ->
                v.setPadding(0, 0, 0, 0)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    WindowInsets.CONSUMED
                } else {
                    @Suppress("DEPRECATION")
                    v.onApplyWindowInsets(WindowInsets(null))
                }
            }

            webViewClient = WebViewClient()
            webChromeClient = WebChromeClient()
            addJavascriptInterface(ArenaEmulatorBridge(this@MainActivity, this), "ArenaAndroid")
        }

        setContentView(webView)

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                }
                // Mantém o Launcher ativo sem sair para a tela vazia
            }
        })

        StoragePermissionHelper.requestNotificationsIfNeeded(this)
        if (!StoragePermissionHelper.hasAllFilesAccess(this)) {
            StoragePermissionHelper.requestAllFilesAccess(this)
        }

        ArenaWebService.start(applicationContext, serverPort)
        waitForServerAndLoad()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            applyImmersiveMode()
            webView.requestFocus()
        }
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        val code = event.keyCode
        val isGamepadOrDpad = code == KeyEvent.KEYCODE_DPAD_UP ||
            code == KeyEvent.KEYCODE_DPAD_DOWN ||
            code == KeyEvent.KEYCODE_DPAD_LEFT ||
            code == KeyEvent.KEYCODE_DPAD_RIGHT ||
            code == KeyEvent.KEYCODE_DPAD_CENTER ||
            code == KeyEvent.KEYCODE_BUTTON_A ||
            code == KeyEvent.KEYCODE_BUTTON_B ||
            code == KeyEvent.KEYCODE_BUTTON_X ||
            code == KeyEvent.KEYCODE_BUTTON_Y ||
            code == KeyEvent.KEYCODE_BUTTON_L1 ||
            code == KeyEvent.KEYCODE_BUTTON_R1 ||
            code == KeyEvent.KEYCODE_BUTTON_START ||
            code == KeyEvent.KEYCODE_BUTTON_SELECT

        if (isGamepadOrDpad) {
            if (!webView.hasFocus()) {
                webView.requestFocus()
            }
            return webView.dispatchKeyEvent(event)
        }
        return super.dispatchKeyEvent(event)
    }

    private fun applyImmersiveMode() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val controller = WindowInsetsControllerCompat(window, window.decorView)
        controller.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        controller.hide(WindowInsetsCompat.Type.systemBars())
    }

    private fun waitForServerAndLoad() {
        Thread {
            var ready = false
            repeat(40) {
                if (!ready) {
                    try {
                        Socket().use { socket ->
                            socket.connect(InetSocketAddress("127.0.0.1", serverPort), 150)
                            ready = true
                        }
                    } catch (_: Exception) {
                        Thread.sleep(150)
                    }
                }
            }
            runOnUiThread {
                webView.loadUrl("http://127.0.0.1:$serverPort")
            }
        }.start()
    }
}