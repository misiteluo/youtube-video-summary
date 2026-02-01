"""
从 YouTube 频道获取视频列表，支持按日期范围筛选。
"""
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp


@dataclass
class VideoInfo:
    """单个视频信息"""
    id: str
    title: str
    url: str
    upload_date: str  # YYYYMMDD
    duration: int | None
    channel: str


def _normalize_channel_url(url: str) -> str:
    """支持频道链接、用户链接、/channel/ID、/@handle 等格式；拉取视频列表时使用 /videos 页面"""
    url = url.strip()
    if not re.match(r"^https?://", url):
        url = "https://www.youtube.com/" + url.lstrip("/")
    # 频道页只返回频道本身，需用 /videos 才能拿到视频列表
    if "/videos" not in url and "/streams" not in url and "/playlist" not in url:
        url = url.rstrip("/") + "/videos"
    return url


def fetch_channel_videos(
    channel_url: str,
    date_after: str | None = None,
    date_before: str | None = None,
    max_videos: int = 50,
) -> list[VideoInfo]:
    """
    获取频道内视频列表。
    :param channel_url: 频道链接（或 /@xxx、/channel/xxx）
    :param date_after: 起始日期 YYYYMMDD，例如 20250101
    :param date_before: 结束日期 YYYYMMDD，例如 20250131
    :param max_videos: 最多获取数量
    :return: VideoInfo 列表
    """
    url = _normalize_channel_url(channel_url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "force_generic_extractor": False,
    }
    # 日期筛选（yt-dlp 格式：YYYYMMDD）
    if date_after:
        opts["date_after"] = date_after
    if date_before:
        opts["date_before"] = date_before

    out: list[VideoInfo] = []
    seen = set()

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            return out
        entries = info.get("entries") or []
        channel_name = info.get("channel") or info.get("uploader") or "未知频道"
        for entry in entries:
            if len(out) >= max_videos:
                break
            if not entry:
                continue
            vid = entry.get("id") or entry.get("url", "").split("?v=")[-1].split("&")[0]
            # 跳过非视频条目：视频 ID 为 11 位，频道 ID 以 UC 开头
            if not vid or vid in seen or len(vid) != 11 or vid.startswith("UC"):
                continue
            seen.add(vid)
            title = entry.get("title") or "无标题"
            upload_date = entry.get("upload_date") or ""
            duration = entry.get("duration")
            video_url = f"https://www.youtube.com/watch?v={vid}"
            out.append(
                VideoInfo(
                    id=vid,
                    title=title,
                    url=video_url,
                    upload_date=upload_date,
                    duration=duration,
                    channel=channel_name,
                )
            )
    return out


def fetch_video_transcript(video_url: str, lang_prefer: list[str] | None = None) -> str:
    """
    获取视频字幕/自动生成字幕文本。若无字幕则返回空字符串。
    :param video_url: 视频 watch 链接
    :param lang_prefer: 优先语言，如 ['zh-Hans', 'zh-Hant', 'en']
    """
    lang_prefer = lang_prefer or ["zh-Hans", "zh-Hant", "en", "en-US", "en-GB"]
    with tempfile.TemporaryDirectory() as tmpdir:
        # 字幕会保存为 tmpdir/%(id)s.语言.vtt
        out_tpl = str(Path(tmpdir) / "%(id)s")
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": lang_prefer,
            "subtitlesformat": "vtt",
            "outtmpl": out_tpl,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
        if not info:
            return ""
        # 查找生成的字幕文件
        vtt_files = list(Path(tmpdir).glob("*.vtt"))
        if not vtt_files:
            return ""
        text_parts = []
        for vtt in vtt_files:
            raw = vtt.read_text(encoding="utf-8", errors="ignore")
            for ln in raw.splitlines():
                ln = ln.strip()
                if not ln or ln.startswith("WEBVTT") or " --> " in ln or ln.isdigit():
                    continue
                text_parts.append(ln)
        return "\n".join(text_parts).strip()


if __name__ == "__main__":
    # 简单测试
    test_url = "https://www.youtube.com/@YouTube"
    videos = fetch_channel_videos(test_url, max_videos=3)
    for v in videos:
        print(v.id, v.title, v.upload_date)
