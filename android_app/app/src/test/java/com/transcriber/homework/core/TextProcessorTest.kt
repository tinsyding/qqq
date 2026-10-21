package com.transcriber.homework.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class TextProcessorTest {

    @Test
    fun testParseNumbersSmartContinuous() {
        val numbers = TextProcessor.parseNumbers("135", "smart")
        assertEquals(listOf("1", "3", "5"), numbers)
    }

    @Test
    fun testParseNumbersSmartAscending() {
        val numbers = TextProcessor.parseNumbers("157111325", "smart")
        assertEquals(listOf("1", "5", "7", "11", "13", "25"), numbers)
    }

    @Test
    fun testParseNumbersSmartKeepsSingleDigitsWhenPossible() {
        assertEquals(listOf("1", "3", "5"), TextProcessor.parseNumbers("135", "smart"))
        assertEquals(listOf("1", "2", "10"), TextProcessor.parseNumbers("1210", "smart"))
    }

    @Test
    fun testParseNumbersSmartSeparated() {
        val numbers = TextProcessor.parseNumbers("1 3 12", "smart")
        assertEquals(listOf("1", "3", "12"), numbers)
    }

    @Test
    fun testParseNumbersWithPunctuation() {
        val numbers = TextProcessor.parseNumbers("1, 3, 5", "smart")
        assertEquals(listOf("1", "3", "5"), numbers)
    }

    @Test
    fun testFormatOutput() {
        val numbers = listOf("1", "3", "5")
        val result = TextProcessor.formatOutput(
            numbers = numbers,
            template = "本次作业的错题题号为：{nums}",
            separator = "，"
        )
        assertEquals("本次作业的错题题号为：1，3，5", result)
    }

    @Test
    fun testFormatOutputWithCustomSeparator() {
        val numbers = listOf("2", "4", "6")
        val result = TextProcessor.formatOutput(
            numbers = numbers,
            template = "错题订正：{nums}",
            separator = "、"
        )
        assertEquals("错题订正：2、4、6", result)
    }

    @Test
    fun testMatchTriggerSuccess() {
        val text = "今天作业135qqq"
        val match = TextProcessor.matchTrigger(text, "qqq")
        assertNotNull(match)
        assertEquals("135", match!!.rawNumbers)
        assertEquals("今天作业".length, match.startIndex)
        assertEquals(text.length, match.endIndex)
    }

    @Test
    fun testMatchTriggerWithSpaces() {
        val text = "第1 3 12qqq"
        val match = TextProcessor.matchTrigger(text, "qqq")
        assertNotNull(match)
        assertEquals("1 3 12", match!!.rawNumbers)
    }

    @Test
    fun testMatchTriggerNoNumbers() {
        val text = "今天天气很好qqq"
        val match = TextProcessor.matchTrigger(text, "qqq")
        assertNull(match)
    }
}
