package com.transcriber.homework.core

/**
 * 错题题号核心解析与格式化引擎 (Kotlin 实现)
 * 对应 Python 原版的 core_engine.py
 */
object TextProcessor {

    /**
     * 智能提取数字列表
     * @param rawText 原始输入的待处理文本（例如 "135" 或 "1 3 12" 或 "1, 2, 5"）
     * @param mode 拆分模式："smart"(智能), "continuous"(逐位), "separated"(仅按分隔符)
     */
    fun parseNumbers(rawText: String, mode: String = "smart"): List<String> {
        val text = rawText.trim()
        if (text.isEmpty()) return emptyList()

        return when (mode) {
            "continuous" -> {
                Regex("""\d""").findAll(text).map { it.value }.toList()
            }
            "separated" -> {
                Regex("""\d+""").findAll(text).map { it.value }.toList()
            }
            else -> { // smart 智能模式
                val hasExplicitSeparator = Regex("""[\s,，、;；|/]""").containsMatchIn(text)
                if (hasExplicitSeparator) {
                    Regex("""\d+""").findAll(text).map { it.value }.toList()
                } else {
                    if (text.length > 1 && text.all { it.isDigit() }) {
                        // 纯连续无分隔符数字，按题号递增规律智能切分
                        // 例如 135 -> 1, 3, 5；157111325 -> 1, 5, 7, 11, 13, 25
                        smartSplitDigits(text)
                    } else {
                        Regex("""\d+""").findAll(text).map { it.value }.toList()
                    }
                }
            }
        }
    }

    /**
     * 将纯数字串切分为严格递增的题号序列，题号数量尽可能多；
     * 数量相同时优先选择最大题号更小的切分方式。
     * 若不存在递增切分，则退化为逐位拆分。
     */
    private fun smartSplitDigits(digits: String): List<String> {
        if (digits.length <= 1) return digits.map { it.toString() }

        val n = digits.length
        val memo = HashMap<Pair<Int, String>, List<String>?>()

        fun isGreater(a: String, b: String): Boolean {
            if (b.isEmpty()) return true
            if (a.length != b.length) return a.length > b.length
            return a > b
        }

        fun isLess(a: String, b: String): Boolean {
            if (a.length != b.length) return a.length < b.length
            return a < b
        }

        fun solve(pos: Int, prev: String): List<String>? {
            if (pos == n) return emptyList()

            val key = pos to prev
            if (memo.containsKey(key)) return memo[key]

            var best: List<String>? = null
            for (end in (pos + 1)..n) {
                val token = digits.substring(pos, end)
                if (token.length > 1 && token[0] == '0') continue
                if (!isGreater(token, prev)) continue

                val rest = solve(end, token) ?: continue
                val candidate = listOf(token) + rest
                val currentBest = best
                if (currentBest == null ||
                    candidate.size > currentBest.size ||
                    (candidate.size == currentBest.size && isLess(candidate.last(), currentBest.last()))
                ) {
                    best = candidate
                }
            }

            memo[key] = best
            return best
        }

        return solve(0, "") ?: digits.map { it.toString() }
    }

    /**
     * 拼接格式化文案
     * @param numbers 题号列表
     * @param template 目标模板（包含 {nums} 占位符）
     * @param separator 分隔符（如 "，" 或 "、" 或 " "）
     */
    fun formatOutput(
        numbers: List<String>,
        template: String = "本次作业的错题题号为：{nums}",
        separator: String = "，"
    ): String {
        if (numbers.isEmpty()) return ""
        val numsStr = numbers.joinToString(separator)
        return if (template.contains("{nums}")) {
            template.replace("{nums}", numsStr)
        } else {
            "$template$numsStr"
        }
    }

    /**
     * 检查文本末尾是否匹配触发词模式
     * 例如匹配 "135qqq" 或 "1 3 12qqq"
     * @return MatchResultData 包含匹配到的数字串、起始/结束索引；未匹配则返回 null
     */
    fun matchTrigger(text: String, triggerWord: String): TriggerMatch? {
        val trigger = triggerWord.trim()
        if (trigger.isEmpty() || text.length < trigger.length + 1) return null

        // 正则：末尾紧跟触发词（不区分大小写），前面是一串数字和可能存在的分隔符
        val escapedTrigger = Regex.escape(trigger)
        val pattern = Regex("""(\d[\d\s,，、;；|/]*)$escapedTrigger$""", RegexOption.IGNORE_CASE)
        val match = pattern.find(text) ?: return null

        val numStr = match.groupValues[1]
        if (!numStr.any { it.isDigit() }) return null

        return TriggerMatch(
            rawNumbers = numStr,
            startIndex = match.range.first,
            endIndex = match.range.last + 1,
            totalLength = match.value.length
        )
    }

    data class TriggerMatch(
        val rawNumbers: String,
        val startIndex: Int,
        val endIndex: Int,
        val totalLength: Int
    )
}
