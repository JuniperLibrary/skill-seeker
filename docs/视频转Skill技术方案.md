# 视频转Skill 技术方案

## 需求概述

支持用户输入视频链接（YouTube、本地视频、在线视频URL），自动提取视频内容并蒸馏成AI Skill。

## 处理流程

```
视频URL/文件 → 音频提取 → Whisper转写 → LLM summarization → Skill输出
```

## 技术选型

| 步骤 | 方案 | 说明 |
|------|------|------|
| **音频提取** | ffmpeg | 提取音频流 |
| **本地视频转写** | OpenAI Whisper | 本地运行，无需API |
| **YouTube字幕** | yt-dlp | 直接获取字幕 |
| **内容增强** | LLM | AI summarization和结构化 |

## 支持的视频源

1. **本地视频**：MP4, MOV, AVI, MKV, WebM
2. **YouTube视频**：直接获取字幕
3. **在线视频URL**：先下载再转写

## 实现方案

### 1. 依赖安装

```bash
# 视频处理
pip install ffmpeg-python

# YouTube下载
pip install yt-dlp

# 语音转写
pip install whisper

# 或使用openai-whisper
pip install openai-whisper
```

### 2. 核心模块设计

```python
# core/video_processor.py

class VideoProcessor:
    """视频处理器"""

    def process(self, source: str, source_type: str) -> str:
        """
        处理视频，返回转写文本
        :param source: 视频源（URL或本地路径）
        :param source_type: video/youtube/local
        :return: 转写文本
        """
        if source_type == "youtube":
            return self._process_youtube(source)
        elif source_type == "local":
            return self._process_local(source)
        else:
            return self._process_url(source)
```

### 3. YouTube处理

```python
def _process_youtube(self, url: str) -> str:
    # 使用yt-dlp获取字幕
    cmd = [
        "yt-dlp",
        "--write-subs",
        "--write-auto-subs",
        "--subs-format=srt",
        "--skip-download",
        "-o", "video.%(ext)s",
        url
    ]
    subprocess.run(cmd, check=True)
    # 解析SRT为纯文本
    return self._parse_srt("video.en.srt")
```

### 4. 本地视频处理

```python
def _process_local(self, video_path: str) -> str:
    # 提取音频
    audio_path = video_path.replace(".mp4", ".wav")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_path
    ]
    subprocess.run(cmd, check=True)

    # Whisper转写
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="zh")
    return result["text"]
```

### 5. 集成到Web UI

在 `skill_web.py` 中新增：

1. 视频上传选项卡
2. 支持YouTube URL输入
3. 本地视频文件上传
4. 转写进度显示
5. 转写完成后自动触发蒸馏

## 竞品参考

| 项目 | 特点 |
|------|------|
| Video Transcribe | 本地Whisper + SRT字幕 |
| whisper-transcription | 带时间戳的文字 |
| youtube-summarizer | YouTube视频摘要 |

## 实现难点与解决方案

| 难点 | 解决方案 |
|------|----------|
| 长视频处理 | 分片转写，合并结果 |
| 中文识别 | 使用large-v2/v3模型 |
| 多说话人 | 添加speaker diarization |
| 网络下载 | 进度条显示 |
| 存储清理 | 处理完成后删除临时文件 |

## 待实现功能

- [ ] 支持本地视频文件上传
- [ ] 支持YouTube URL输入
- [ ] 支持在线视频URL
- [ ] 视频转写功能
- [ ] 转写内容自动蒸馏成Skill
