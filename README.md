# YouTube 视频总结工具

根据 YouTube 频道链接（可限定日期范围）拉取视频，用 AI 总结内容后发送到你的邮箱。

## 功能

- 支持任意频道链接：`/@用户名`、`/channel/ID`、完整 URL
- 可选日期范围：`--date-after`、`--date-before`（格式 `YYYYMMDD` 或 `YYYY-MM-DD`）
- 自动获取视频字幕/自动生成字幕，无字幕时无法总结
- 使用 Google Gemini 对字幕进行中文总结
- 将多条总结合并为一封 HTML 邮件发送

## 环境准备

1. Python 3.10+
2. 安装依赖：

```bash
cd youtube-video-summary
pip install -r requirements.txt
```

3. 复制配置并填写：

```bash
cp config.example.env .env
# 编辑 .env，填入 GEMINI_API_KEY、TO_EMAIL、SMTP_* 等
```

## 配置说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `GEMINI_API_KEY` | 是 | Google Gemini API Key，用于总结（在 [Google AI Studio](https://aistudio.google.com/apikey) 申请） |
| `TO_EMAIL` | 发邮件时必填 | 收件邮箱 |
| `SMTP_HOST` | 发邮件时必填 | 发件 SMTP 服务器，如 QQ：smtp.qq.com |
| `SMTP_PORT` | 否 | 默认 465（SSL） |
| `SMTP_USER` | 发邮件时必填 | 发件邮箱 |
| `SMTP_PASSWORD` | 发邮件时必填 | 发件密码或授权码 |
| `GEMINI_MODEL` | 否 | 默认 gemini-2.5-flash（也可用 gemini-1.5-pro） |

## 使用示例

```bash
# 拉取某频道最近视频（默认最多 10 条），总结并发邮件
python main.py "https://www.youtube.com/@某博主"

# 指定日期范围：2025-01-01 到 2025-01-31
python main.py "https://www.youtube.com/@某博主" --date-after 20250101 --date-before 20250131

# 只总结不发邮件，结果打印到终端
python main.py "https://www.youtube.com/@某博主" --no-email

# 指定收件邮箱、最多 5 条
python main.py "https://www.youtube.com/channel/UCxxxx" --to-email me@example.com --max-videos 5
```

## 注意事项

- 视频需有字幕或自动生成字幕，否则会得到「无可用字幕」类提示。
- Gemini API 有免费额度，可在 [Google AI Studio](https://aistudio.google.com/) 查看；`gemini-2.5-flash` 为新版默认模型。
- 发件邮箱若为 QQ/163 等，需在邮箱设置中开启 SMTP 并使用授权码作为 `SMTP_PASSWORD`。
