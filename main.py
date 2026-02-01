#!/usr/bin/env python3
"""
YouTube 频道视频总结工具：按频道（可选日期范围）拉取视频 → AI 总结 → 发送邮件。
"""
import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from email_sender import send_summary_email
from summarizer import summarize_video
from youtube_fetcher import VideoInfo, fetch_channel_videos

load_dotenv()


def _parse_date(s: str) -> str:
    """将 YYYY-MM-DD 或 YYYYMMDD 转为 YYYYMMDD"""
    s = s.strip().replace("-", "")
    if len(s) != 8 or not s.isdigit():
        raise ValueError(f"日期格式应为 YYYYMMDD 或 YYYY-MM-DD: {s}")
    return s


def _build_html_email(videos: list[tuple[VideoInfo, str]], channel_name: str) -> str:
    """生成邮件 HTML 正文"""
    rows = []
    for i, (v, summary) in enumerate(videos, 1):
        rows.append(
            f"""
            <div style="margin-bottom: 1.5em; padding: 1em; border: 1px solid #eee; border-radius: 8px;">
                <h3 style="margin-top: 0;">{i}. <a href="{v.url}">{v.title}</a></h3>
                <p style="color: #666; font-size: 0.9em;">发布时间：{v.upload_date or '未知'} | 链接：<a href="{v.url}">{v.url}</a></p>
                <div style="white-space: pre-wrap; line-height: 1.6;">{summary}</div>
            </div>
            """
        )
    body = "\n".join(rows)
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: sans-serif; max-width: 720px; margin: 0 auto;">
        <h2>YouTube 视频总结 - {channel_name}</h2>
        <p>共 {len(videos)} 个视频，以下为 AI 总结内容。</p>
        {body}
    </body>
    </html>
    """


def main() -> None:
    parser = argparse.ArgumentParser(
        description="拉取 YouTube 频道视频，AI 总结后发送到邮箱。"
    )
    parser.add_argument(
        "channel_url",
        help="频道链接，例如 https://www.youtube.com/@xxx 或 https://www.youtube.com/channel/UCxxx",
    )
    parser.add_argument(
        "--to-email",
        default=os.environ.get("TO_EMAIL"),
        help="收件邮箱（也可用环境变量 TO_EMAIL）",
    )
    parser.add_argument(
        "--date-after",
        metavar="YYYYMMDD",
        help="只处理该日期之后发布的视频，例如 20250101",
    )
    parser.add_argument(
        "--date-before",
        metavar="YYYYMMDD",
        help="只处理该日期之前发布的视频，例如 20250131",
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=10,
        help="最多处理多少个视频（默认 10）",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="只打印总结，不发邮件",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        help="Gemini 模型名（默认 gemini-2.0-flash）",
    )
    args = parser.parse_args()

    date_after = None
    date_before = None
    if args.date_after:
        try:
            date_after = _parse_date(args.date_after)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    if args.date_before:
        try:
            date_before = _parse_date(args.date_before)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    if not args.no_email and not args.to_email:
        print("错误：请设置 --to-email 或环境变量 TO_EMAIL", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("GEMINI_API_KEY"):
        print("错误：请设置环境变量 GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    print("正在获取频道视频列表…")
    videos = fetch_channel_videos(
        args.channel_url,
        date_after=date_after,
        date_before=date_before,
        max_videos=args.max_videos,
    )
    if not videos:
        print("未获取到任何视频，请检查频道链接与日期范围。")
        return
    channel_name = videos[0].channel if videos else "YouTube 频道"
    print(f"共获取 {len(videos)} 个视频，开始逐条总结…")

    results: list[tuple[VideoInfo, str]] = []
    for i, v in enumerate(videos, 1):
        print(f"  [{i}/{len(videos)}] {v.title[:50]}...")
        try:
            summary = summarize_video(v, model=args.model)
            results.append((v, summary))
            print(f"      总结完成，约 {len(summary)} 字")
        except Exception as e:
            print(f"      失败: {e}")
            results.append((v, f"（总结失败: {e}）"))

    if not results:
        print("没有可用的总结结果。")
        return

    if args.no_email:
        print("\n" + "=" * 60)
        for v, summary in results:
            print(f"\n【{v.title}】\n{v.url}\n{summary}\n")
        return

    subject = f"YouTube 视频总结 - {channel_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    html = _build_html_email(results, channel_name)
    try:
        send_summary_email(args.to_email, subject, html)
        print(f"\n已发送到 {args.to_email}")
    except Exception as e:
        print(f"发送邮件失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
