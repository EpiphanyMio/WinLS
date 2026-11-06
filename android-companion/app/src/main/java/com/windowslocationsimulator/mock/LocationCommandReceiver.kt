package com.windowslocationsimulator.mock

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.location.Criteria
import android.location.Location
import android.location.LocationManager
import android.os.SystemClock

@Suppress("DEPRECATION")
class LocationCommandReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        try {
            require(intent.action == ACTION) { "无效命令" }
            val manager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
            when (intent.getStringExtra("command")) {
                "set" -> {
                    val latitude = intent.getStringExtra("latitude")?.toDoubleOrNull()
                    val longitude = intent.getStringExtra("longitude")?.toDoubleOrNull()
                    require(latitude != null && latitude.isFinite() && latitude in -90.0..90.0 &&
                        longitude != null && longitude.isFinite() && longitude in -180.0..180.0) {
                        "坐标无效"
                    }
                    for (provider in PROVIDERS) {
                        // Re-adding an existing test provider can throw; subsequent updates reuse it.
                        try {
                            manager.addTestProvider(provider, false, false, false, false,
                                true, true, true, Criteria.POWER_LOW, Criteria.ACCURACY_FINE)
                        } catch (_: IllegalArgumentException) { }
                        manager.setTestProviderEnabled(provider, true)
                        val location = Location(provider).apply {
                            this.latitude = latitude
                            this.longitude = longitude
                            accuracy = 1f
                            time = System.currentTimeMillis()
                            elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos()
                        }
                        manager.setTestProviderLocation(provider, location)
                    }
                }
                "clear" -> {
                    for (provider in PROVIDERS) {
                        try { manager.removeTestProvider(provider) }
                        catch (_: IllegalArgumentException) { }
                    }
                }
                else -> error("未知定位命令")
            }
            setResultCode(200) // distinct from the default broadcast result 0
            setResultData("OK")
        } catch (error: Exception) {
            setResultCode(400)
            setResultData(error.message ?: error.javaClass.simpleName)
        }
    }

    companion object {
        private const val ACTION = "com.windowslocationsimulator.mock.LOCATION_COMMAND"
        private val PROVIDERS = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
    }
}
