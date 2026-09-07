# 智谱余量监控（zhipu-usage-tray）

一个 Windows 系统托盘小工具，实时监控智谱 AI（open.bigmodel.cn / Z.ai）API 用量额度。Terminal HUD 深色风格，终端绿强调色、等宽字体、分段方块进度条，安静地待在托盘角落。

## 功能特性

- **托盘图标仪表盘**：图标圆盘直接显示 5 小时额度整数百分比，颜色随余量变化（绿 → 青 → 橙 → 红）
- **详情弹窗**：`TOKEN · 5H` 与 `WEEKLY` 两级额度分段方块条展示，附重置时间
- **定时刷新**：可配置刷新间隔（60–3600 秒），后台线程请求，不卡界面
- **多平台支持**：智谱开放平台（open.bigmodel.cn）与 Z.ai（api.z.ai）
- **悬停 Tooltip**：鼠标悬停即可查看 5h / 周两级余量
- **单实例保护**：重复启动自动退出，避免多个托盘图标
- **崩溃日志**：异常自动写入 `%APPDATA%\zhipu-usage-tray\crash.log`

## 安装使用

### 方式一：直接运行打包版

从 [Releases](../../releases) 下载 `智谱余量监控.exe`，双击运行。

首次启动会弹出设置窗口，填入 API Key 即可开始监控。

### 方式二：源码运行

```bash
pip install -r requirements.txt
python main.py
```

## 配置说明

配置文件保存在本机 `%APPDATA%\zhipu-usage-tray\config.json`：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `api_key` | API Key（Base64 编码存储） | 空 |
| `platform` | `zhipu`（智谱）或 `zai`（Z.ai） | `zhipu` |
| `refresh_interval` | 刷新间隔（秒） | `300` |

> **安全说明**：API Key 仅保存在本机配置文件中，不会上传到任何服务器，也不包含在本仓库代码里。

## 开发与打包

```bash
# 生成应用图标（可选，仓库已包含）
python generate_icon.py

# PyInstaller 打包单文件 exe
pyinstaller --onefile --noconsole --icon "icons/app.ico" --add-data "icons/app.ico;icons" --name "智谱余量监控" main.py
```

打包产物位于 `dist/智谱余量监控.exe`。

## 项目结构

```
main.py              入口：单实例检查、全局字体、启动日志
tray_app.py          托盘应用：图标绘制、刷新线程、详情弹窗、菜单
settings_dialog.py   设置弹窗
frameless.py         无边框弹窗基类（圆角 + 实色背景）
theme.py             Terminal HUD 主题：调色板、字体工具
api_client.py        API 客户端：额度查询与解析
config.py            配置读写（API Key Base64 编码）
generate_icon.py     应用图标生成脚本
```

## 常见问题

**托盘图标数字是什么？**
5 小时窗口的已用额度百分比。颜色规则：<25% 绿、25–50% 青、50–75% 橙、≥75% 红。

**查询失败怎么办？**
检查 API Key 是否有效、网络是否可达。错误信息会显示在托盘通知与详情弹窗 `ERR:` 行。

## License

[MIT](./LICENSE)
