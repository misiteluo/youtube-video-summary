"""
使用 Google Gemini 对视频字幕/文本进行总结。
"""
import os

from google import genai
from google.genai import types

from youtube_fetcher import VideoInfo, fetch_video_transcript


def _get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


def summarize_with_gemini(
    text: str,
    video_title: str,
    model_name: str = "gemini-2.5-flash",
    max_output_tokens: int = 8192,
) -> str:
    """
    调用 Google Gemini 对文本做总结。
    :param text: 原始文本（如字幕内容）
    :param video_title: 视频标题，用于上下文
    :param model_name: 模型名，如 gemini-2.5-flash、gemini-1.5-pro
    :param max_output_tokens: 总结最大输出 token 数
    """
    if not text or not text.strip():
        return "（无可用字幕，无法总结）"

    prompt = f"""你是一个视频内容总结助手。请根据以下视频的字幕/转录文本，用中文写一份简洁、有条理的总结。

视频标题：{video_title}

要求：
1. 概括视频主要内容和观点；
2. 分点或分段，便于阅读；
3. 控制在 300～800 字以内；
4. 若文本为英文，请用中文总结。

字幕/转录文本：
---
{text[:500000]}
---
请直接输出总结内容，不要重复标题或多余说明。"""

    client = _get_client()
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_output_tokens),
    )
    try:
        out = (response and response.text) or ""
    except (ValueError, AttributeError):
        out = ""
    if not out.strip():
        return "（Gemini 未返回有效内容，可能被安全策略拦截）"
    return out.strip()


def summarize_video(
    video: VideoInfo,
    lang_prefer: list[str] | None = None,
    model: str = "gemini-2.5-flash",
) -> str:
    """
    获取视频字幕并生成 AI 总结。
    """
    transcript = fetch_video_transcript(video.url, lang_prefer=lang_prefer)
    return summarize_with_gemini(transcript, video.title, model_name=model)
