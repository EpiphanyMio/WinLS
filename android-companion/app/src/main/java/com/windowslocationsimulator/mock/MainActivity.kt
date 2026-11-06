package com.windowslocationsimulator.mock

import android.app.Activity
import android.app.AppOpsManager
import android.content.Intent
import android.os.Bundle
import android.os.Process
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 72, 48, 48)
            gravity = Gravity.CENTER_HORIZONTAL
        }
        layout.addView(TextView(this).apply {
            text = "定位模拟器配套应用"
            textSize = 23f
        })
        layout.addView(TextView(this).apply {
            text = "在开发者选项中选择本应用作为模拟位置信息应用；开启 USB 调试并允许电脑连接。然后在 Windows 程序中刷新设备。"
            textSize = 16f
            setPadding(0, 36, 0, 36)
        })
        status = TextView(this).apply { textSize = 16f }
        layout.addView(status)
        layout.addView(Button(this).apply {
            text = "打开开发者选项"
            setOnClickListener { startActivity(Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)) }
        })
        setContentView(layout)
    }

    override fun onResume() {
        super.onResume()
        val appOps = getSystemService(APP_OPS_SERVICE) as AppOpsManager
        val allowed = appOps.checkOpNoThrow(AppOpsManager.OPSTR_MOCK_LOCATION,
            Process.myUid(), packageName) == AppOpsManager.MODE_ALLOWED
        status.text = if (allowed) "已选为模拟定位应用" else "尚未选为模拟定位应用"
    }
}
