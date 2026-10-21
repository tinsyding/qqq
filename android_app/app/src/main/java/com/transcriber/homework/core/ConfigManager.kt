package com.transcriber.homework.core

import android.content.Context
import android.content.SharedPreferences

/**
 * 用户配置持久化存储管理类
 * 对应 Python 原版的 config.json
 */
class ConfigManager private constructor(context: Context) {

    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)

    var triggerWord: String
        get() = prefs.getString(KEY_TRIGGER_WORD, "qqq") ?: "qqq"
        set(value) = prefs.edit().putString(KEY_TRIGGER_WORD, value.trim()).apply()

    var isTriggerEnabled: Boolean
        get() = prefs.getBoolean(KEY_ENABLE_TRIGGER, true)
        set(value) = prefs.edit().putBoolean(KEY_ENABLE_TRIGGER, value).apply()

    var template: String
        get() = prefs.getString(KEY_TEMPLATE, "本次作业的错题题号为：{nums}") ?: "本次作业的错题题号为：{nums}"
        set(value) = prefs.edit().putString(KEY_TEMPLATE, value.trim()).apply()

    var separator: String
        get() = prefs.getString(KEY_SEPARATOR, "，") ?: "，"
        set(value) = prefs.edit().putString(KEY_SEPARATOR, value).apply()

    var splitMode: String
        get() = prefs.getString(KEY_SPLIT_MODE, "smart") ?: "smart"
        set(value) = prefs.edit().putString(KEY_SPLIT_MODE, value).apply()

    companion object {
        private const val PREF_NAME = "homework_transcriber_config"
        private const val KEY_TRIGGER_WORD = "trigger_word"
        private const val KEY_ENABLE_TRIGGER = "enable_trigger"
        private const val KEY_TEMPLATE = "template"
        private const val KEY_SEPARATOR = "separator"
        private const val KEY_SPLIT_MODE = "split_mode"

        @Volatile
        private var instance: ConfigManager? = null

        fun getInstance(context: Context): ConfigManager {
            return instance ?: synchronized(this) {
                instance ?: ConfigManager(context).also { instance = it }
            }
        }
    }
}
