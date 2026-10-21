package com.transcriber.homework

import android.accessibilityservice.AccessibilityService
import android.content.ClipData
import android.content.ClipboardManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.provider.Settings
import android.text.Editable
import android.text.TextUtils
import android.text.TextWatcher
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.materialswitch.MaterialSwitch
import com.google.android.material.textfield.TextInputEditText
import com.transcriber.homework.core.ConfigManager
import com.transcriber.homework.core.TextProcessor
import com.transcriber.homework.service.TextExpanderService

class MainActivity : AppCompatActivity() {

    private lateinit var config: ConfigManager

    // UI 组件声明
    private lateinit var cardStatus: MaterialCardView
    private lateinit var viewStatusDot: android.view.View
    private lateinit var tvStatusText: android.widget.TextView
    private lateinit var btnOpenAccessibility: MaterialButton

    private lateinit var switchEnableTrigger: MaterialSwitch
    private lateinit var etTriggerWord: TextInputEditText
    private lateinit var btnSaveTriggerWord: MaterialButton

    private lateinit var btnPresetErrorNums: MaterialButton
    private lateinit var btnPresetErrorCount: MaterialButton
    private lateinit var btnPresetConcise: MaterialButton
    private lateinit var etTemplate: TextInputEditText

    private lateinit var rgSeparator: android.widget.RadioGroup
    private lateinit var rbSepCnComma: android.widget.RadioButton
    private lateinit var rbSepDun: android.widget.RadioButton
    private lateinit var rbSepSpace: android.widget.RadioButton

    private lateinit var etTestInput: TextInputEditText
    private lateinit var tvPreviewResult: android.widget.TextView
    private lateinit var btnCopyPreview: MaterialButton

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        config = ConfigManager.getInstance(this)
        initViews()
        bindData()
        setupListeners()
    }

    override fun onResume() {
        super.onResume()
        updateServiceStatus()
        updateTestPreview()
    }

    private fun initViews() {
        cardStatus = findViewById(R.id.cardStatus)
        viewStatusDot = findViewById(R.id.viewStatusDot)
        tvStatusText = findViewById(R.id.tvStatusText)
        btnOpenAccessibility = findViewById(R.id.btnOpenAccessibility)

        switchEnableTrigger = findViewById(R.id.switchEnableTrigger)
        etTriggerWord = findViewById(R.id.etTriggerWord)
        btnSaveTriggerWord = findViewById(R.id.btnSaveTriggerWord)

        btnPresetErrorNums = findViewById(R.id.btnPresetErrorNums)
        btnPresetErrorCount = findViewById(R.id.btnPresetErrorCount)
        btnPresetConcise = findViewById(R.id.btnPresetConcise)
        etTemplate = findViewById(R.id.etTemplate)

        rgSeparator = findViewById(R.id.rgSeparator)
        rbSepCnComma = findViewById(R.id.rbSepCnComma)
        rbSepDun = findViewById(R.id.rbSepDun)
        rbSepSpace = findViewById(R.id.rbSepSpace)

        etTestInput = findViewById(R.id.etTestInput)
        tvPreviewResult = findViewById(R.id.tvPreviewResult)
        btnCopyPreview = findViewById(R.id.btnCopyPreview)
    }

    private fun bindData() {
        switchEnableTrigger.isChecked = config.isTriggerEnabled
        etTriggerWord.setText(config.triggerWord)
        etTemplate.setText(config.template)

        when (config.separator) {
            "、" -> rbSepDun.isChecked = true
            " " -> rbSepSpace.isChecked = true
            else -> rbSepCnComma.isChecked = true
        }
    }

    private fun setupListeners() {
        // 跳转到系统无障碍权限设置
        btnOpenAccessibility.setOnClickListener {
            try {
                val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                startActivity(intent)
                Toast.makeText(this, "请在列表中找到【错题快速转换助手】并开启", Toast.LENGTH_LONG).show()
            } catch (e: Exception) {
                Toast.makeText(this, "打开系统设置失败: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }

        // 触发开关
        switchEnableTrigger.setOnCheckedChangeListener { _, isChecked ->
            config.isTriggerEnabled = isChecked
            updateTestPreview()
        }

        // 保存触发词
        btnSaveTriggerWord.setOnClickListener {
            val word = etTriggerWord.text?.toString()?.trim() ?: ""
            if (word.isEmpty()) {
                Toast.makeText(this, "触发词不能为空", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            config.triggerWord = word
            Toast.makeText(this, "触发词已更新为: $word", Toast.LENGTH_SHORT).show()
            updateTestPreview()
        }

        // 模板预设按钮
        btnPresetErrorNums.setOnClickListener {
            val tmpl = "本次作业的错题题号为：{nums}"
            etTemplate.setText(tmpl)
            config.template = tmpl
            updateTestPreview()
        }

        btnPresetErrorCount.setOnClickListener {
            val tmpl = "本次作业的错题数为：{nums}"
            etTemplate.setText(tmpl)
            config.template = tmpl
            updateTestPreview()
        }

        btnPresetConcise.setOnClickListener {
            val tmpl = "错题订正：{nums}"
            etTemplate.setText(tmpl)
            config.template = tmpl
            updateTestPreview()
        }

        // 模板输入监听
        etTemplate.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                config.template = s?.toString()?.trim() ?: "本次作业的错题题号为：{nums}"
                updateTestPreview()
            }
            override fun afterTextChanged(s: Editable?) {}
        })

        // 分隔符监听
        rgSeparator.setOnCheckedChangeListener { _, checkedId ->
            val sep = when (checkedId) {
                R.id.rbSepDun -> "、"
                R.id.rbSepSpace -> " "
                else -> "，"
            }
            config.separator = sep
            updateTestPreview()
        }

        // 测试输入框监听
        etTestInput.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                updateTestPreview()
            }
            override fun afterTextChanged(s: Editable?) {}
        })

        // 一键复制结果
        btnCopyPreview.setOnClickListener {
            val text = tvPreviewResult.text?.toString() ?: ""
            if (text.isNotEmpty() && !text.startsWith("（")) {
                val clipboard = getSystemService(CLIPBOARD_SERVICE) as ClipboardManager
                clipboard.setPrimaryClip(ClipData.newPlainText("错题文案", text))
                Toast.makeText(this, "已复制到剪贴板！", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun updateTestPreview() {
        val input = etTestInput.text?.toString()?.trim() ?: ""
        val trigger = config.triggerWord.lowercase()

        val rawNumbers = if (input.lowercase().endsWith(trigger)) {
            input.substring(0, input.length - trigger.length).trim()
        } else {
            input
        }

        val numbers = TextProcessor.parseNumbers(rawNumbers, config.splitMode)
        if (numbers.isNotEmpty()) {
            val result = TextProcessor.formatOutput(numbers, config.template, config.separator)
            tvPreviewResult.text = result
        } else {
            tvPreviewResult.text = "（输入数字如 135 或 135$trigger 预览结果）"
        }
    }

    private fun updateServiceStatus() {
        val isEnabled = isAccessibilityServiceEnabled(this, TextExpanderService::class.java)

        if (isEnabled) {
            cardStatus.setCardBackgroundColor(ContextCompat.getColor(this, R.color.status_green_bg))
            cardStatus.strokeColor = ContextCompat.getColor(this, R.color.status_green_border)
            tvStatusText.setTextColor(ContextCompat.getColor(this, R.color.status_green_text))
            tvStatusText.text = "✅ 错题自动展开服务正在运行中"
            btnOpenAccessibility.text = "已启用"
            btnOpenAccessibility.isEnabled = false

            val dot = viewStatusDot.background as? GradientDrawable
            dot?.setColor(ContextCompat.getColor(this, R.color.status_green_dot))
        } else {
            cardStatus.setCardBackgroundColor(ContextCompat.getColor(this, R.color.status_amber_bg))
            cardStatus.strokeColor = ContextCompat.getColor(this, R.color.status_amber_border)
            tvStatusText.setTextColor(ContextCompat.getColor(this, R.color.status_amber_text))
            tvStatusText.text = "⚠️ 无障碍服务未开启，无法自动替换"
            btnOpenAccessibility.text = "去开启"
            btnOpenAccessibility.isEnabled = true

            val dot = viewStatusDot.background as? GradientDrawable
            dot?.setColor(ContextCompat.getColor(this, R.color.status_amber_dot))
        }
    }

    private fun isAccessibilityServiceEnabled(
        context: Context,
        service: Class<out AccessibilityService>
    ): Boolean {
        val expectedComponentName = ComponentName(context, service).flattenToString()
        val enabledServicesSetting = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false

        val colonSplitter = TextUtils.SimpleStringSplitter(':')
        colonSplitter.setString(enabledServicesSetting)
        while (colonSplitter.hasNext()) {
            val componentNameString = colonSplitter.next()
            if (componentNameString.equals(expectedComponentName, ignoreCase = true)) {
                return true
            }
        }
        return false
    }
}
