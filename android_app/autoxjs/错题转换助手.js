"ui";

/**
 * 错题快速转换助手 - AutoX.js / Auto.js 脚本版
 * 
 * 使用方式：
 * 1. 在手机上安装 AutoX.js (https://github.com/kkevsekk1/AutoX)
 * 2. 导入本脚本并运行，按照提示开启无障碍权限与悬浮窗权限
 * 3. 支持在 AutoX.js 中点击「打包」直接生成独立 APK 安装包！
 */

// 默认配置
var config = {
    trigger_word: "qqq",
    template: "本次作业的错题题号为：{nums}",
    separator: "，",
    split_mode: "smart"
};

ui.layout(
    <vertical padding="16" bg="#F8FAFC">
        <text text="✍️ 错题快速转换助手 (AutoX.js版)" textSize="18sp" textStyle="bold" textColor="#1E293B"/>
        <text text="支持一键打包为独立 APK · 输入 135qqq 自动展开" textSize="12sp" textColor="#64748B" marginTop="4"/>

        <!-- 权限状态 -->
        <card cardCornerRadius="8" margin="0 12 0 12" cardBackgroundColor="#F0FDF4">
            <horizontal padding="12" gravity="center_vertical">
                <text id="tv_status" text="● 无障碍权限检测中..." textColor="#166534" textStyle="bold" layout_weight="1"/>
                <button id="btn_auth" text="授权/启动" style="Widget.AppCompat.Button.Colored" w="auto" h="36"/>
            </horizontal>
        </card>

        <!-- 触发词配置 -->
        <card cardCornerRadius="8" margin="0 4 0 8" cardBackgroundColor="#FFFFFF" padding="12">
            <vertical padding="12">
                <text text="⚡ 触发字符设置" textStyle="bold" textColor="#1E293B"/>
                <horizontal gravity="center_vertical" marginTop="6">
                    <text text="后缀触发词：" textColor="#334155"/>
                    <input id="et_trigger" text="qqq" w="80" gravity="center"/>
                    <button id="btn_save_trig" text="保存" w="auto" h="36" marginLeft="8"/>
                </horizontal>
            </vertical>
        </card>

        <!-- 模板配置 -->
        <card cardCornerRadius="8" margin="0 4 0 8" cardBackgroundColor="#FFFFFF" padding="12">
            <vertical padding="12">
                <text text="📝 文案模板设置" textStyle="bold" textColor="#1E293B"/>
                <horizontal marginTop="6">
                    <button id="btn_tmpl_1" text="题号模板" style="Widget.AppCompat.Button.Borderless" w="auto" h="32"/>
                    <button id="btn_tmpl_2" text="题数模板" style="Widget.AppCompat.Button.Borderless" w="auto" h="32"/>
                    <button id="btn_tmpl_3" text="简洁订正" style="Widget.AppCompat.Button.Borderless" w="auto" h="32"/>
                </horizontal>
                <input id="et_template" text="本次作业的错题题号为：{nums}" marginTop="4"/>
            </vertical>
        </card>

        <!-- 实时测试区 -->
        <card cardCornerRadius="8" margin="0 4 0 8" cardBackgroundColor="#FFFFFF" padding="12">
            <vertical padding="12">
                <text text="🧪 实时输入测试" textStyle="bold" textColor="#1E293B"/>
                <input id="et_test" hint="输入 135 或 135qqq 测试..." text="135qqq" marginTop="6"/>
                <text text="展开结果预览：" textColor="#64748B" textSize="12sp" marginTop="8"/>
                <text id="tv_preview" text="" textStyle="bold" textColor="#0F172A" marginTop="2"/>
            </vertical>
        </card>

        <text text="💡 提示：在 AutoX.js 菜单中点击「打包应用」，即可将其打包为一个完全独立的手机安装包 (APK)。" textColor="#64748B" textSize="11sp" marginTop="8"/>
    </vertical>
);

// 将纯数字串切分为严格递增的题号序列，题号数量尽可能多；数量相同时优先选择最大题号更小的切分方式
function smartSplitDigits(digits) {
    var n = digits.length;
    if (n <= 1) return digits.split("");

    var memo = {};

    function isGreater(a, b) {
        if (!b) return true;
        if (a.length !== b.length) return a.length > b.length;
        return a > b;
    }

    function isLess(a, b) {
        if (a.length !== b.length) return a.length < b.length;
        return a < b;
    }

    function solve(pos, prev) {
        if (pos === n) return [];
        var key = pos + ":" + prev;
        if (memo.hasOwnProperty(key)) return memo[key];

        var best = null;
        for (var end = pos + 1; end <= n; end++) {
            var token = digits.substring(pos, end);
            if (token.length > 1 && token.charAt(0) === "0") continue;
            if (!isGreater(token, prev)) continue;

            var rest = solve(end, token);
            if (rest === null) continue;

            var candidate = [token].concat(rest);
            if (best === null || candidate.length > best.length ||
                (candidate.length === best.length &&
                    isLess(candidate[candidate.length - 1], best[best.length - 1]))) {
                best = candidate;
            }
        }

        memo[key] = best;
        return best;
    }

    var result = solve(0, "");
    return result === null ? digits.split("") : result;
}

// 核心数字解析函数
function parseNumbers(rawText, mode) {
    var text = (rawText || "").trim();
    if (!text) return [];

    var hasExplicitSeparator = /[\s,，、;；|/]/.test(text);
    if (hasExplicitSeparator) {
        return text.match(/\d+/g) || [];
    } else {
        if (text.length > 1 && /^\d+$/.test(text)) {
            return smartSplitDigits(text);
        } else {
            return text.match(/\d+/g) || [];
        }
    }
}

// 格式化输出
function formatOutput(numbers, template, separator) {
    if (!numbers || numbers.length === 0) return "";
    var numsStr = numbers.join(separator || "，");
    if (template.indexOf("{nums}") !== -1) {
        return template.replace("{nums}", numsStr);
    }
    return template + numsStr;
}

// 更新预览
function updatePreview() {
    var text = ui.et_test.text().trim();
    var trigger = (ui.et_trigger.text().trim() || "qqq").toLowerCase();
    
    if (text.toLowerCase().endsWith(trigger)) {
        text = text.substring(0, text.length - trigger.length).trim();
    }
    
    var nums = parseNumbers(text);
    if (nums && nums.length > 0) {
        var res = formatOutput(nums, ui.et_template.text().trim(), config.separator);
        ui.tv_preview.setText(res);
    } else {
        ui.tv_preview.setText("（等待输入数字...）");
    }
}

// 刷新状态
function checkStatus() {
    if (auto.service != null) {
        ui.tv_status.setText("● 无障碍服务运行中 (可随时打字自动展开)");
        ui.tv_status.setTextColor(colors.parseColor("#166534"));
        ui.btn_auth.setText("已开启");
        ui.btn_auth.setEnabled(false);
    } else {
        ui.tv_status.setText("● 无障碍服务未开启");
        ui.tv_status.setTextColor(colors.parseColor("#991B1B"));
        ui.btn_auth.setText("开启服务");
        ui.btn_auth.setEnabled(true);
    }
}

// 事件监听
ui.btn_auth.click(function() {
    app.startActivity({
        action: "android.settings.ACCESSIBILITY_SETTINGS"
    });
});

ui.btn_save_trig.click(function() {
    toast("触发词已更新为：" + ui.et_trigger.text());
    updatePreview();
});

ui.btn_tmpl_1.click(function() {
    ui.et_template.setText("本次作业的错题题号为：{nums}");
    updatePreview();
});

ui.btn_tmpl_2.click(function() {
    ui.et_template.setText("本次作业的错题数为：{nums}");
    updatePreview();
});

ui.btn_tmpl_3.click(function() {
    ui.et_template.setText("错题订正：{nums}");
    updatePreview();
});

ui.et_test.addTextChangedListener({
    onTextChanged: function() {
        updatePreview();
    }
});

updatePreview();
checkStatus();
