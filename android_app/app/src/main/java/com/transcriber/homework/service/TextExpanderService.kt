package com.transcriber.homework.service

import android.accessibilityservice.AccessibilityService
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.transcriber.homework.core.ConfigManager
import com.transcriber.homework.core.TextProcessor

/**
 * Android 核心无障碍文本替换服务
 * 监听全局输入框的文字变动，当检测到类似 "135qqq" 时自动擦除并就地展开
 */
class TextExpanderService : AccessibilityService() {

    private lateinit var configManager: ConfigManager
    private val mainHandler = Handler(Looper.getMainLooper())
    private var isReplacing = false
    private var lastReplacedText: String? = null

    override fun onServiceConnected() {
        super.onServiceConnected()
        configManager = ConfigManager.getInstance(this)
        isRunning = true
        Log.i(TAG, "错题自动展开无障碍服务已启动")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null || !isRunning || isReplacing) return
        if (event.eventType != AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED) return

        if (!configManager.isTriggerEnabled) return

        val source = event.source ?: return
        try {
            // 确保当前节点是可编辑的文本框
            if (!source.isEditable) return

            val currentText = source.text?.toString() ?: return
            if (currentText.isEmpty()) return

            // 避免刚才替换生成的文字引起死循环触发
            if (currentText == lastReplacedText) return

            val triggerWord = configManager.triggerWord
            val match = TextProcessor.matchTrigger(currentText, triggerWord) ?: return

            val numbers = TextProcessor.parseNumbers(match.rawNumbers, configManager.splitMode)
            if (numbers.isEmpty()) return

            val formatted = TextProcessor.formatOutput(
                numbers = numbers,
                template = configManager.template,
                separator = configManager.separator
            )

            val prefix = currentText.substring(0, match.startIndex)
            val suffix = currentText.substring(match.endIndex)
            val newText = prefix + formatted + suffix

            // 开始替换文本
            isReplacing = true
            lastReplacedText = newText

            val args = Bundle().apply {
                putCharSequence(
                    AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,
                    newText
                )
            }
            val setResult = source.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)

            if (setResult) {
                // 将光标定位到展开文字的末尾
                val cursorPosition = (prefix + formatted).length
                val cursorArgs = Bundle().apply {
                    putInt(
                        AccessibilityNodeInfo.ACTION_ARGUMENT_SELECTION_START_INT,
                        cursorPosition
                    )
                    putInt(
                        AccessibilityNodeInfo.ACTION_ARGUMENT_SELECTION_END_INT,
                        cursorPosition
                    )
                }
                source.performAction(AccessibilityNodeInfo.ACTION_SET_SELECTION, cursorArgs)
            }
        } catch (e: Exception) {
            Log.e(TAG, "文本替换出错: ${e.message}", e)
        } finally {
            // 延时解除防重入锁，防止文本变更回调重入
            mainHandler.postDelayed({
                isReplacing = false
            }, 300)
            source.recycle()
        }
    }

    override fun onInterrupt() {
        Log.w(TAG, "错题自动展开服务被中断")
    }

    override fun onDestroy() {
        super.onDestroy()
        isRunning = false
        Log.i(TAG, "错题自动展开服务已销毁")
    }

    companion object {
        private const val TAG = "TextExpanderService"

        @Volatile
        var isRunning: Boolean = false
            private set
    }
}
