package com.transcriber.homework

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import com.transcriber.homework.core.ConfigManager
import com.transcriber.homework.core.TextProcessor

/**
 * 划选文本快捷替换 Activity (Android 6.0+ Process Text 标准系统集成)
 * 在任意第三方软件中长按划选数字 "135"，系统弹出菜单会出现 "转为错题格式"，点击即可就地替换
 */
class ProcessTextActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val selectedText = intent.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)?.toString()
        val isReadOnly = intent.getBooleanExtra(Intent.EXTRA_PROCESS_TEXT_READONLY, false)

        if (!selectedText.isNullOrBlank()) {
            val config = ConfigManager.getInstance(this)
            val numbers = TextProcessor.parseNumbers(selectedText, config.splitMode)

            if (numbers.isNotEmpty()) {
                val formatted = TextProcessor.formatOutput(
                    numbers = numbers,
                    template = config.template,
                    separator = config.separator
                )

                if (!isReadOnly) {
                    val resultIntent = Intent().apply {
                        putExtra(Intent.EXTRA_PROCESS_TEXT, formatted)
                    }
                    setResult(RESULT_OK, resultIntent)
                } else {
                    // 若目标是只读文本框，则将结果写入系统剪贴板并提示
                    val clipboard = getSystemService(CLIPBOARD_SERVICE) as ClipboardManager
                    clipboard.setPrimaryClip(ClipData.newPlainText("错题文案", formatted))
                    Toast.makeText(this, "已复制: $formatted", Toast.LENGTH_SHORT).show()
                }
            }
        }

        finish()
    }
}
