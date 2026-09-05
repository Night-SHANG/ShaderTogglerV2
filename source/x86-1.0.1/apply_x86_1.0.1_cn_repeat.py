#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re, shutil, sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
SRC = ROOT / 'src'
MAIN = SRC / 'Main.cpp'
KEY = SRC / 'KeyData.cpp'
PROJ = SRC / 'ShaderToggler.vcxproj'
for p in (MAIN, KEY, PROJ):
    if not p.exists():
        raise SystemExit(f'缺少文件：{p}\n请对官方 ShaderToggler 1.0.1 源码运行本脚本。')

def read(path): return path.read_bytes().decode('utf-8-sig')
def write_cpp(path, text): path.write_bytes(b'\xef\xbb\xbf' + text.encode('utf-8'))
def backup(path):
    bak = path.with_suffix(path.suffix + '.1.0.1-original.bak')
    if not bak.exists(): shutil.copy2(path, bak)

main, key, proj = read(MAIN), read(KEY), read(PROJ)
checks = [
    'extern "C" __declspec(dllexport) const char *NAME = "Shader Toggler";',
    'static ShaderToggler::ShaderManager g_pixelShaderManager;',
    'static ShaderToggler::ShaderManager g_vertexShaderManager;',
    '#define HASH_FILE_NAME\t"ShaderToggler.ini"',
    'groupEditing.storeCollectedHashes(g_pixelShaderManager.getMarkedShaderHashes(), g_vertexShaderManager.getMarkedShaderHashes());',
]
if any(s not in main for s in checks) or 'g_computeShaderManager' in main or 'VK_NUMPAD7' in main or 'Active at startup' in main:
    raise SystemExit('源码与官方 1.0.1 结构不匹配，已停止，未修改文件。')
for p in (MAIN, KEY, PROJ): backup(p)

if '#include <chrono>' not in main:
    main = main.replace('#include <vector>\n', '#include <vector>\n#include <chrono>\n', 1)

marker = '// Classic CN Repeat: hold-to-browse state (1.0.1 x86)'
if marker not in main:
    needle = 'static int g_startValueFramecountCollectionPhase = FRAMECOUNT_COLLECTION_PHASE_DEFAULT;\n'
    helper = '''

// Classic CN Repeat: hold-to-browse state (1.0.1 x86)
// Numpad 1/2 and 4/5 repeat while held. Numpad 3/6 remain single-press mark keys.
struct HuntRepeatState
{
    bool previousDown = false;
    bool holding = false;
    std::chrono::steady_clock::time_point holdStart{};
    std::chrono::steady_clock::time_point lastRepeat{};
};

static HuntRepeatState g_repeatNumpad1;
static HuntRepeatState g_repeatNumpad2;
static HuntRepeatState g_repeatNumpad4;
static HuntRepeatState g_repeatNumpad5;

static bool isHuntKeyDown(effect_runtime* runtime, const uint32_t keyCode)
{
    return runtime->is_key_down(keyCode) ||
           ((GetAsyncKeyState(static_cast<int>(keyCode)) & 0x8000) != 0);
}

static int getHuntRepeatIntervalMs(
    const std::chrono::steady_clock::time_point& holdStart,
    const std::chrono::steady_clock::time_point& now)
{
    const auto heldMs = std::chrono::duration_cast<std::chrono::milliseconds>(now - holdStart).count();
    if(heldMs >= 2400) return 35;
    if(heldMs >= 1400) return 70;
    if(heldMs >= 700) return 120;
    return 200;
}

static bool shouldAdvanceHuntKey(effect_runtime* runtime, const uint32_t keyCode, HuntRepeatState& state)
{
    const auto now = std::chrono::steady_clock::now();
    const bool down = isHuntKeyDown(runtime, keyCode);
    const bool justPressed = down && !state.previousDown;
    state.previousDown = down;

    if(!down)
    {
        state.holding = false;
        return false;
    }

    if(justPressed || !state.holding)
    {
        state.holding = true;
        state.holdStart = now;
        state.lastRepeat = now;
        return true;
    }

    const int intervalMs = getHuntRepeatIntervalMs(state.holdStart, now);
    const auto elapsedMs = std::chrono::duration_cast<std::chrono::milliseconds>(now - state.lastRepeat).count();
    if(elapsedMs >= intervalMs)
    {
        state.lastRepeat = now;
        return true;
    }
    return false;
}
'''
    if needle not in main: raise SystemExit('找不到 1.0.1 全局状态插入点。')
    main = main.replace(needle, needle + helper, 1)

old = '''\tif(runtime->is_key_pressed(VK_NUMPAD1))\n\t{\n\t\tg_pixelShaderManager.huntPreviousShader(runtime->is_key_down(VK_CONTROL));\n\t}\n\tif(runtime->is_key_pressed(VK_NUMPAD2))\n\t{\n\t\tg_pixelShaderManager.huntNextShader(runtime->is_key_down(VK_CONTROL));\n\t}\n\tif(runtime->is_key_pressed(VK_NUMPAD3))\n\t{\n\t\tg_pixelShaderManager.toggleMarkOnHuntedShader();\n\t}\n\tif(runtime->is_key_pressed(VK_NUMPAD4))\n\t{\n\t\tg_vertexShaderManager.huntPreviousShader(runtime->is_key_down(VK_CONTROL));\n\t}\n\tif(runtime->is_key_pressed(VK_NUMPAD5))\n\t{\n\t\tg_vertexShaderManager.huntNextShader(runtime->is_key_down(VK_CONTROL));\n\t}\n\tif(runtime->is_key_pressed(VK_NUMPAD6))\n\t{\n\t\tg_vertexShaderManager.toggleMarkOnHuntedShader();\n\t}\n'''
new = '''\tconst bool controlDown = runtime->is_key_down(VK_CONTROL) || ((GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0);\n\tif(shouldAdvanceHuntKey(runtime, VK_NUMPAD1, g_repeatNumpad1))\n\t{\n\t\tg_pixelShaderManager.huntPreviousShader(controlDown);\n\t}\n\tif(shouldAdvanceHuntKey(runtime, VK_NUMPAD2, g_repeatNumpad2))\n\t{\n\t\tg_pixelShaderManager.huntNextShader(controlDown);\n\t}\n\tif(runtime->is_key_pressed(VK_NUMPAD3))\n\t{\n\t\tg_pixelShaderManager.toggleMarkOnHuntedShader();\n\t}\n\tif(shouldAdvanceHuntKey(runtime, VK_NUMPAD4, g_repeatNumpad4))\n\t{\n\t\tg_vertexShaderManager.huntPreviousShader(controlDown);\n\t}\n\tif(shouldAdvanceHuntKey(runtime, VK_NUMPAD5, g_repeatNumpad5))\n\t{\n\t\tg_vertexShaderManager.huntNextShader(controlDown);\n\t}\n\tif(runtime->is_key_pressed(VK_NUMPAD6))\n\t{\n\t\tg_vertexShaderManager.toggleMarkOnHuntedShader();\n\t}\n'''
if old in main: main = main.replace(old, new, 1)
elif 'shouldAdvanceHuntKey(runtime, VK_NUMPAD1' not in main: raise SystemExit('找不到官方 1.0.1 浏览按键代码。')

repls = {
'extern "C" __declspec(dllexport) const char *NAME = "Shader Toggler";':'extern "C" __declspec(dllexport) const char *NAME = "Shader Toggler 经典中文版";',
'extern "C" __declspec(dllexport) const char *DESCRIPTION = "Add-on which allows you to define groups of game shaders to toggle on/off with one key press.";':'extern "C" __declspec(dllexport) const char *DESCRIPTION = "基于官方 1.0.1 x86：保留旧版功能与 INI 格式，加入长按加速查找和简体中文。";',
'ImGui::Text(" Shader is part of this toggle group.");':'ImGui::TextUnformatted(" 当前着色器已加入此切换组。");',
'ImGui::Text("Collecting active shaders... frames to go: %d", counterValue);':'ImGui::Text("正在收集活动着色器……剩余帧数：%d", counterValue);',
'ImGui::Text("Editing the shaders for group: %s", editingGroupName.c_str());':'ImGui::Text("正在查找切换组的着色器：%s", editingGroupName.c_str());',
'ImGui::CollapsingHeader("General info and help")':'ImGui::CollapsingHeader("基本说明与帮助")',
'ImGui::TextUnformatted("The Shader Toggler allows you to create one or more groups with shaders to toggle on/off. You can assign a keyboard shortcut (including using keys like Shift, Alt and Control) to each group, including a handy name. Each group can have one or more vertex or pixel shaders assigned to it. When you press the assigned keyboard shortcut, any draw calls using these shaders will be disabled, effectively hiding the elements in the 3D scene.");':'ImGui::TextUnformatted("Shader Toggler 可以创建一个或多个着色器切换组，并给每个组设置名称和快捷键。每个组可加入像素或顶点着色器；触发快捷键后，使用这些着色器的绘制调用会被阻止，从而隐藏对应 HUD、特效或场景元素。");',
'ImGui::TextUnformatted("\\nThe following (hardcoded) keyboard shortcuts are used when you click a group\'s \'Change Shaders\' button:");':'ImGui::TextUnformatted("\\n点击“查找着色器”后使用以下固定快捷键：");',
'ImGui::TextUnformatted("* Numpad 1 and Numpad 2: previous/next pixel shader");':'ImGui::TextUnformatted("* 小键盘 1 / 2：上一个 / 下一个像素着色器（支持长按加速）");',
'ImGui::TextUnformatted("* Ctrl + Numpad 1 and Ctrl + Numpad 2: previous/next marked pixel shader in the group");':'ImGui::TextUnformatted("* Ctrl + 小键盘 1 / 2：上一个 / 下一个已标记像素着色器（支持长按）");',
'ImGui::TextUnformatted("* Numpad 3: mark/unmark the current pixel shader as being part of the group");':'ImGui::TextUnformatted("* 小键盘 3：标记 / 取消标记当前像素着色器");',
'ImGui::TextUnformatted("* Numpad 4 and Numpad 5: previous/next vertex shader");':'ImGui::TextUnformatted("* 小键盘 4 / 5：上一个 / 下一个顶点着色器（支持长按加速）");',
'ImGui::TextUnformatted("* Ctrl + Numpad 4 and Ctrl + Numpad 5: previous/next marked vertex shader in the group");':'ImGui::TextUnformatted("* Ctrl + 小键盘 4 / 5：上一个 / 下一个已标记顶点着色器（支持长按）");',
'ImGui::TextUnformatted("* Numpad 6: mark/unmark the current vertex shader as being part of the group");':'ImGui::TextUnformatted("* 小键盘 6：标记 / 取消标记当前顶点着色器");',
'ImGui::TextUnformatted("\\nWhen you step through the shaders, the current shader is disabled in the 3D scene so you can see if that\'s the shader you were looking for.");':'ImGui::TextUnformatted("\\n浏览着色器时，当前选择的着色器会暂时被禁用，便于观察它是否对应需要定位的 HUD 或效果。浏览键现在支持长按并逐渐加速。");',
'ImGui::TextUnformatted("When you\'re done, make sure you click \'Save all toggle groups\' to preserve the groups you defined so next time you start your game they\'re loaded in and you can use them right away.");':'ImGui::TextUnformatted("完成后请点击“保存所有切换组”，下次启动游戏会继续读取原来的 ShaderToggler.ini。");',
'ImGui::CollapsingHeader("Shader selection parameters", ImGuiTreeNodeFlags_DefaultOpen)':'ImGui::CollapsingHeader("着色器查找参数", ImGuiTreeNodeFlags_DefaultOpen)',
'ImGui::SliderFloat("Overlay opacity", &g_overlayOpacity, 0.2f, 1.0f);':'ImGui::SliderFloat("查找提示透明度", &g_overlayOpacity, 0.2f, 1.0f);',
'ImGui::SliderInt("# of frames to collect", &g_startValueFramecountCollectionPhase, 10, 1000);':'ImGui::SliderInt("收集帧数", &g_startValueFramecountCollectionPhase, 10, 1000);',
'showHelpMarker("This is the number of frames the addon will collect active shaders. Set this to a high number if the shader you want to mark is only used occasionally. Only shaders that are used in the frames collected can be marked.");':'showHelpMarker("插件会在指定帧数内收集实际使用的着色器。目标着色器如果只偶尔出现，可以提高该数值。只有收集期间出现过的着色器才能被查找和标记。");',
'ImGui::CollapsingHeader("List of Toggle Groups", ImGuiTreeNodeFlags_DefaultOpen)':'ImGui::CollapsingHeader("切换组列表", ImGuiTreeNodeFlags_DefaultOpen)',
'ImGui::Button(" New ")':'ImGui::Button(" 新建 ")',
'ImGui::Button("Edit")':'ImGui::Button("编辑")',
'ImGui::Button(" Done ")':'ImGui::Button(" 完成 ")',
'ImGui::Button("Change shaders")':'ImGui::Button("查找着色器")',
'group.isActive() ? ", is active" : ""':'group.isActive() ? ", 已启用" : ""',
'ImGui::Text("Edit group %d", group.getId());':'ImGui::Text("编辑切换组 %d", group.getId());',
'ImGui::Text("Name");':'ImGui::Text("名称");',
'ImGui::Text("Key shortcut");':'ImGui::Text("快捷键");',
'ImGui::Button("Cancel")':'ImGui::Button("取消")',
'ImGui::Button("Save all Toggle Groups")':'ImGui::Button("保存所有切换组")',
}
for a,b in repls.items(): main = main.replace(a,b)
main = main.replace('ImGui::Text("# of pipelines with vertex shaders: %d. # of different vertex shaders gathered: %d.", g_vertexShaderManager.getPipelineCount(), g_vertexShaderManager.getShaderCount());','ImGui::Text("包含顶点着色器的管线：%d；已收集不同顶点着色器：%d", g_vertexShaderManager.getPipelineCount(), g_vertexShaderManager.getShaderCount());')
main = main.replace('ImGui::Text("# of pipelines with pixel shaders: %d. # of different pixel shaders gathered: %d.", g_pixelShaderManager.getPipelineCount(), g_pixelShaderManager.getShaderCount());','ImGui::Text("包含像素着色器的管线：%d；已收集不同像素着色器：%d", g_pixelShaderManager.getPipelineCount(), g_pixelShaderManager.getShaderCount());')
main = main.replace('ImGui::Text("# of vertex shaders active: %d. # of vertex shaders in group: %d", g_vertexShaderManager.getAmountShaderHashesCollected(), g_vertexShaderManager.getMarkedShaderCount());','ImGui::Text("当前活动顶点着色器：%d；组内：%d", g_vertexShaderManager.getAmountShaderHashesCollected(), g_vertexShaderManager.getMarkedShaderCount());')
main = main.replace('ImGui::Text("Current selected vertex shader: %d / %d.", g_vertexShaderManager.getActiveHuntedShaderIndex(), g_vertexShaderManager.getAmountShaderHashesCollected());','ImGui::Text("当前选择顶点着色器：%d / %d", g_vertexShaderManager.getActiveHuntedShaderIndex(), g_vertexShaderManager.getAmountShaderHashesCollected());')
main = main.replace('ImGui::Text("# of pixel shaders active: %d. # of pixel shaders in group: %d", g_pixelShaderManager.getAmountShaderHashesCollected(), g_pixelShaderManager.getMarkedShaderCount());','ImGui::Text("当前活动像素着色器：%d；组内：%d", g_pixelShaderManager.getAmountShaderHashesCollected(), g_pixelShaderManager.getMarkedShaderCount());')
main = main.replace('ImGui::Text("Current selected pixel shader: %d / %d", g_pixelShaderManager.getActiveHuntedShaderIndex(), g_pixelShaderManager.getAmountShaderHashesCollected());','ImGui::Text("当前选择像素着色器：%d / %d", g_pixelShaderManager.getActiveHuntedShaderIndex(), g_pixelShaderManager.getAmountShaderHashesCollected());')

key = key.replace('_keyAsString = "Press a key";', '_keyAsString = "请按下按键";')

# UTF-8 compile option, only Release|Win32
pat = re.compile(r'(<ItemDefinitionGroup Condition="\'\$\(Configuration\)\|\$\(Platform\)\'==\'Release\|Win32\'">.*?<ClCompile>)(.*?)(</ClCompile>)', re.S)
m = pat.search(proj)
if not m: raise SystemExit('找不到 Release|Win32 ClCompile。')
body=m.group(2)
if '/utf-8' not in body:
    body += '\n      <AdditionalOptions>/utf-8 %(AdditionalOptions)</AdditionalOptions>\n    '
    proj=proj[:m.start(2)]+body+proj[m.end(2):]
# Release Win32 output -> addon32
pat2=re.compile(r'(<PropertyGroup Condition="\'\$\(Configuration\)\|\$\(Platform\)\'==\'Release\|Win32\'">.*?<TargetExt>)\.addon(</TargetExt>.*?</PropertyGroup>)', re.S)
proj,n=pat2.subn(r'\1.addon32\2',proj,count=1)
if n!=1: raise SystemExit('找不到 Release|Win32 TargetExt。')

if 'g_computeShaderManager' in main or 'ActiveAtStartup' in main: raise SystemExit('安全检查失败：意外引入后续版功能。')
write_cpp(MAIN, main); write_cpp(KEY, key); PROJ.write_text(proj, encoding='utf-8-sig')
print('完成：1.0.1 x86 中文 + 长按加速；INI 序列化源码未修改。')
