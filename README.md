# 2026 藏历火马年 ICS 日历

把用户提供的《2026（农历）藏历火马年月历.pdf》转换为可订阅的标准 iCalendar 文件。

## 文件

- `calendar-2026.ics`：最终日历，365 个全天事件。
- `generate_ics.py`：根据 `data/calendar-2026.json` 重新生成 ICS。
- `data/calendar-2026.json`：公历、农历、藏历及 PDF 事项的结构化数据。
- `index.html`：面向 iPhone 的订阅说明页。

## 本地预览

```powershell
python -m http.server 8080
```

浏览器打开 <http://localhost:8080>。本地 HTTP 地址可用于测试，但 iPhone 长期订阅最好使用公开 HTTPS 地址。

## 部署到 GitHub Pages

1. 在 GitHub 新建一个公开仓库。
2. 将本 `calendar-site` 目录里的文件上传到仓库根目录。
3. 打开仓库的 `Settings -> Pages`。
4. 在 `Build and deployment` 中选择 `Deploy from a branch`，分支选 `main`，目录选 `/ (root)`。
5. 部署完成后，公开地址通常为：

```text
https://<GitHub用户名>.github.io/<仓库名>/
```

6. 用 iPhone Safari 打开该地址，点击“订阅 2026 藏历”。

订阅直接使用的 ICS 地址为：

```text
https://<GitHub用户名>.github.io/<仓库名>/calendar-2026.ics
```

## 更新日历

修改 `data/calendar-2026.json` 后运行：

```powershell
python generate_ics.py
```

## 校验

生成器会检查记录数必须为 365。生成的 ICS 已使用 Python `icalendar` 解析验证：
365 个 VEVENT、UID 唯一、日期型 DTSTART/DTEND、每条物理行不超过 RFC 5545 的 75 字节限制。

## 🐟 标记版订阅

在保留原订阅的同时，额外提供独立的鱼类标记日历：

```text
https://haihuarao.github.io/tibetan-calendar-2026/calendar-2026-fish.ics
```

规则：萨嘎月整月每天显示 🐟；其他月份只在藏历初八、十五、三十显示 🐟。

生成命令：

```powershell
python generate_ics.py --fish --output calendar-2026-fish.ics
```

## Android 版订阅

Android 订阅使用独立文件和独立 UID，内容与 iOS internal v2 相同：

```text
https://haihuarao.github.io/tibetan-calendar-2026/calendar-2026-fish-android.ics
```

页面：

```text
https://haihuarao.github.io/tibetan-calendar-2026/android.html
```

日历名称为 `2026 藏历火马年_v2_Android`。Android 的 Google Calendar App 通常不直接支持 ICS URL，可在 Google Calendar 网页版中通过“其他日历 → 通过网址添加”订阅。

## HarmonyOS 版订阅

HarmonyOS 订阅使用独立文件和独立 UID，内容与 iOS internal v2 相同：

```text
https://haihuarao.github.io/tibetan-calendar-2026/calendar-2026-fish-harmony.ics
```

页面：

```text
https://haihuarao.github.io/tibetan-calendar-2026/harmony.html
```

日历名称为 `2026 藏历火马年_v2_HarmonyOS`。HarmonyOS 的设备日历是否直接支持 URL 订阅取决于版本；如果没有“订阅日历/通过网址添加”入口，可使用支持 ICS URL 的第三方日历应用，或先在 Google Calendar 网页版添加后同步查看。
