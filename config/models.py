# AI模型配置

PROVIDERS = [
    "--- 海外主流模型 ---",
    "Anthropic (Claude)",
    "OpenAI",
    "Google Gemini",
    "--- 国内主流模型 ---",
    "智谱AI (GLM 系列)",
    "阿里云 通义千问 (Qwen 系列)",
    "字节跳动 豆包大模型",
    "DeepSeek 深度求索",
    "Moonshot AI (Kimi)",
    "百度智能云 千帆 (文心一言)",
    "不使用AI增强",
]

MODEL_CONFIG = {
    "Anthropic (Claude)": {
        "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "env_key": "ANTHROPIC_API_KEY",
    },
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "env_key": "OPENAI_API_KEY",
    },
    "Google Gemini": {
        "models": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
        "env_key": "GOOGLE_API_KEY",
    },
    "智谱AI (GLM 系列)": {
        "models": ["glm-4-plus", "glm-4-air", "glm-4-flash", "glm-4-long"],
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "env_key": "OPENAI_API_KEY",
    },
    "阿里云 通义千问 (Qwen 系列)": {
        "models": ["qwen-max-latest", "qwen-plus-latest", "qwen-turbo-latest", "qwen2.5-72b-instruct"],
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_key": "OPENAI_API_KEY",
    },
    "字节跳动 豆包大模型": {
        "models": ["doubao-1.5-pro-32k-250115", "doubao-1.5-flash-8k-250115"],
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "env_key": "OPENAI_API_KEY",
    },
    "DeepSeek 深度求索": {
        "models": ["deepseek-chat", "deepseek-coder"],
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "OPENAI_API_KEY",
    },
    "Moonshot AI (Kimi)": {
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "base_url": "https://api.moonshot.cn/v1",
        "env_key": "MOONSHOT_API_KEY",
    },
    "百度智能云 千帆 (文心一言)": {
        "models": ["ernie-4.0-turbo-8k", "ernie-3.5-8k"],
        "base_url": "https://qianfan.baidubce.com/v2",
        "env_keys": ["QIANFAN_ACCESS_KEY", "QIANFAN_SECRET_KEY"],
    },
}

TARGET_PLATFORMS = [
    "opencode", "claude", "cursor", "openai", "gemini", "markdown", "langchain", "chroma"
]

PRESETS = {
    "quick": "quick (1-2分钟)",
    "standard": "standard (5-10分钟)",
    "comprehensive": "comprehensive (20-60分钟)"
}

OUTPUT_ROOT = "/Users/dingchuan/Documents/Repos/skill-seeker/output"