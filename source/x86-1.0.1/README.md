# x86 / 32-bit：官方 1.0.1 基线

32 位保持 FransBouma 官方老版 1.0.1 的功能范围，只加入：

- 简体中文界面
- Numpad 1/2：Pixel Shader 长按连续查找
- Numpad 4/5：Vertex Shader 长按连续查找
- 200 → 120 → 70 → 35 ms 分阶段加速
- Ctrl + 浏览键继续只浏览已标记 Shader

Numpad 3/6 仍然只做单次标记/取消。

不会加入 Compute Shader、Active at startup 或 Advanced 的其他功能。

`apply_x86_1.0.1_cn_repeat.py` 会先验证源码特征。不是 1.0.1 时会终止，不会盲目修改。

GitHub Actions 会自动完成：官方 1.0.1 tag → 应用补丁 → 编译 Win32 → 输出 `ShaderToggler.addon32` + 完整修改源码 ZIP。
