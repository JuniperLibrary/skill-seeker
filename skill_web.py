import os
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st

from config.models import PROVIDERS, MODEL_CONFIG, TARGET_PLATFORMS, PRESETS
from config.paths import OUTPUT_ROOT, WORK_DIR
from config.settings import APP_TITLE, APP_SUBTITLE, SUPPORTED_FILE_TYPES, DEFAULT_SKILL_NAME
from utils.file_utils import save_uploaded_file, get_file_size_mb
from utils.helpers import mask_content, generate_skill_name
from core.history import get_history_skills, read_skill_content, delete_skill as delete_skill_file
from core.distiller import SkillDistiller

REPO_ROOT = Path(__file__).parent
EVIDENCE_FILES = ("INVENTORY.md", "SHRINK_LOG.md", "EVAL.md", "PROMPT.md")

st.set_page_config(page_title="Skill Seekers", layout="wide")
st.title(APP_TITLE)
st.markdown(APP_SUBTITLE)

# ── 开工契约：UI 的"题目"（与 prompts/deep_distill.md 同源） ──────────────
with st.expander("📐 深度蒸馏契约（四问，先答后做）", expanded=False):
    st.markdown(
        """
| 四问 | 本工具的答案 |
|---|---|
| **顶尖专家会做什么** | 审源料定切分策略 → 写蒸馏契约（能答什么/拒答什么）→ 结论挂证据锚 → 独立盲考 → 机器门禁不过不交付 |
| **从哪些最原始素材入手** | 原始文档字节、TOC 目录树、逐页 raw text、原始字段表与错误码、元数据、上游转换器的失败产物（反面证据）|
| **用什么方法和工具** | 四阶段管线（盘点→建证→瘦身→自证）；PyMuPDF 页锚 [P#] + grep 检索性测试；≤120 行瘦身铁律；A/B/C 证据分级 |
| **谁来证明结果正确** | 机器门禁 `verify_skill.py`（8 项，非人判定）→ 独立盲考官（禁读原文，≥10 题+2 反幻觉）→ 溯源回查（规则可在切分文件 grep 命中）|
"""
    )
    st.caption("产物即证明：INVENTORY / rules.md（锚）/ SHRINK_LOG / EVAL / 机器门禁报告，执行后自动生成并展示。")
st.divider()


def run_machine_gate(skill_path: Path) -> tuple[str, bool]:
    """跑 scripts/verify_skill.py：执行后的第三方证明，非人判定。"""
    r = subprocess.run(
        [sys.executable, "scripts/verify_skill.py", str(skill_path)],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=120,
    )
    out = (r.stdout or r.stderr).strip()
    return out, "ALL PASS" in out


def show_gate(skill_path: Path, key: str):
    out, passed = run_machine_gate(skill_path)
    if passed:
        st.success("✅ 机器门禁 ALL PASS（8/8）")
    else:
        st.error("❌ 机器门禁未过——以下为逐项判定，不要带病交付：")
    st.code(out or "（无输出）", language="text")
    return passed


def show_evidence(skill_path: Path):
    tabs = st.tabs(["📐 INVENTORY", "✂️ SHRINK_LOG", "🧪 EVAL", "📝 PROMPT"])
    for tab, name in zip(tabs, EVIDENCE_FILES):
        with tab:
            p = skill_path / name
            if p.exists():
                st.markdown(p.read_text(encoding="utf-8")[:4000])
            else:
                st.info(f"暂无 {name}（对应阶段未执行）")


# ── 侧栏：AI 配置（数据驱动，不再 5 段 if/elif） ──────────────────────────
api_provider = st.sidebar.selectbox("选择AI提供商", PROVIDERS, index=0)
env_config, api_key, api_secret = {}, None, None
PROVIDER_INPUT = {
    "Anthropic (Claude)": "Anthropic API Key",
    "OpenAI": "OpenAI API Key",
    "Google Gemini": "Google API Key",
    "智谱AI (GLM 系列)": "智谱 API Key",
    "阿里云 通义千问 (Qwen 系列)": "通义千问 API Key",
    "字节跳动 豆包大模型": "豆包 API Key",
    "DeepSeek 深度求索": "DeepSeek API Key",
    "Moonshot AI (Kimi)": "Moonshot API Key",
}
if api_provider in PROVIDER_INPUT:
    api_key = st.sidebar.text_input(PROVIDER_INPUT[api_provider], type="password")
    st.sidebar.selectbox("选择模型", MODEL_CONFIG[api_provider]["models"])
    if api_key:
        cfg = MODEL_CONFIG[api_provider]
        env_config[cfg["env_key"]] = api_key
        if "base_url" in cfg:
            env_config["OPENAI_BASE_URL"] = cfg["base_url"]
elif api_provider == "百度智能云 千帆 (文心一言)":
    api_key = st.sidebar.text_input("千帆 Access Key", type="password")
    api_secret = st.sidebar.text_input("千帆 Secret Key", type="password")
    if api_key and api_secret:
        env_config["QIANFAN_ACCESS_KEY"] = api_key
        env_config["QIANFAN_SECRET_KEY"] = api_secret
        env_config["OPENAI_BASE_URL"] = MODEL_CONFIG[api_provider]["base_url"]
else:
    st.sidebar.info("已关闭AI增强——深度蒸馏不依赖增强等级，靠契约+门禁+盲考保深度")

DEEP_AGENT_CMD = {
    "仅生成深度题目 PROMPT.md": None,
    "用 Claude Code 执行题目": 'claude -p --dangerously-skip-permissions "$(cat {prompt_file})"',
    "用 OpenCode 执行题目": 'opencode run "$(cat {prompt_file})"',
}
st.sidebar.divider()
st.sidebar.header("⚙️ 蒸馏参数")
if "redistill_skill" in st.session_state:
    default_name = st.session_state.pop("redistill_skill")
else:
    default_name = DEFAULT_SKILL_NAME
skill_name = st.sidebar.text_input("Skill名称", value=default_name)
preset_value = st.sidebar.selectbox("生成预设", list(PRESETS.keys()), index=1)
deep_mode = st.sidebar.selectbox(
    "🔬 深度蒸馏执行方式", list(DEEP_AGENT_CMD.keys()), index=0,
    help="深度题目生成后，可交由本地 coding agent 无头执行四阶段",
)
target_platform = st.sidebar.selectbox("目标平台", TARGET_PLATFORMS, index=0)
use_ocr = st.sidebar.checkbox("开启OCR", value=False)
password = st.sidebar.text_input("PDF密码", type="password")

output_root = Path(OUTPUT_ROOT)
output_root.mkdir(exist_ok=True)
history_skills = get_history_skills(output_root)

st.sidebar.divider()
st.sidebar.header("📜 历史记录")
if history_skills:
    st.sidebar.markdown("、".join(s["name"] for s in history_skills[:12]))
else:
    st.sidebar.info("暂无历史记录")


def deep_enhance_skill(name: str):
    distiller = SkillDistiller(output_root)
    with st.spinner("深度蒸馏执行中…（四阶段：盘点原料→精读建证→重写瘦身→盲测自证）"):
        return distiller.deep_enhance(name, agent_cmd=DEEP_AGENT_CMD[deep_mode])


tab_new, tab_history = st.tabs(["🔬 新建深度蒸馏", "📜 历史证据"])

with tab_new:
    st.subheader("📄 上传文档 → 四阶段深度蒸馏")
    uploaded_files = st.file_uploader(
        "支持PDF、DOCX、EPub（单选或批量）", type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.success(f"已选择 {len(uploaded_files)} 个文件，共 {get_file_size_mb(sum(f.size for f in uploaded_files))} MB")
        if api_provider in PROVIDER_INPUT and not api_key:
            st.warning("未填 API Key：将只跑基线 create + 深度题目生成（无 AI 增强）")
        if st.button("🔬 开始深度蒸馏", type="primary", use_container_width=True):
            for idx, up in enumerate(uploaded_files):
                name = generate_skill_name(up.name)
                st.markdown(f"### [{idx+1}/{len(uploaded_files)}] {up.name} → `{name}`")
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = Path(tmp) / up.name
                    tmp_path.write_bytes(up.getbuffer())
                    cmd = [
                        "skill-seekers", "create", str(tmp_path),
                        "--name", name, "--preset", preset_value,
                        "--enhance-level", "0",  # 深度管线不靠增强等级
                        "--output", str(output_root / name),
                    ]
                    if use_ocr:
                        cmd.append("--ocr")
                    if password:
                        cmd.extend(["--password", password])
                    run_env = os.environ.copy()
                    run_env.update(env_config)
                    try:
                        r = subprocess.run(cmd, capture_output=True, text=True,
                                           check=True, cwd=WORK_DIR, env=run_env)
                        st.caption(mask_content(r.stdout or "", api_key, api_secret)[-600:])
                    except subprocess.CalledProcessError as e:
                        st.error(f"❌ 基线 create 失败：{mask_content(e.stderr or '', api_key, api_secret)[-600:]}")
                        continue
                prompt_file = deep_enhance_skill(name)
                if prompt_file:
                    st.success(f"深度题目已生成：{prompt_file}")
                skill_path = output_root / name
                st.markdown("#### 第三方证明（自动机器门禁）")
                show_gate(skill_path, key=f"gate_new_{name}")
                st.info("下一步建议：在历史证据页查看四阶段产物，并派独立盲考官（禁读原文）按 EVAL 题集判卷。")
        st.divider()
        if history_skills:
            st.subheader("对已有 skill 补跑深度蒸馏")
            pick = st.selectbox("选择 skill", [s["name"] for s in history_skills], key="pick_new")
            if st.button(f"🔬 对 {pick} 执行深度蒸馏", key="deep_new"):
                prompt_file = deep_enhance_skill(pick)
                if prompt_file:
                    st.success(f"已完成。深度题目/执行入口：{prompt_file}")
                    show_gate(output_root / pick, key=f"gate_deep_{pick}")

with tab_history:
    st.subheader("📜 历史记录（证据驱动）")
    if not history_skills:
        st.info("暂无历史记录")
    for idx, skill in enumerate(history_skills):
        with st.expander(f"📦 {skill['name']}", expanded=(idx == 0)):
            skill_path = skill["path"]
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("✅ 机器门禁复检", key=f"gate_{idx}"):
                    show_gate(skill_path, key=f"gate_run_{idx}")
            with c2:
                if st.button("🔬 深度蒸馏", key=f"deep_{idx}",
                             help="四阶段重做：替换不追加，附证据锚与盲测验证"):
                    prompt_file = deep_enhance_skill(skill["name"])
                    if prompt_file:
                        st.success(f"产出：{prompt_file}")
            with c3:
                if st.button("🔄 重新蒸馏", key=f"rd_{idx}"):
                    st.session_state["redistill_skill"] = skill["name"]
                    st.rerun()
            for zf in sorted(skill_path.glob("*.zip")):
                with open(zf, "rb") as f:
                    st.download_button(f"📥 {zf.stem}", f, file_name=zf.name,
                                       key=f"dlzip_{idx}_{zf.name}")
            show_evidence(skill_path)
            content = read_skill_content(skill_path)
            if content:
                with st.expander("📖 SKILL.md 预览"):
                    st.markdown(content[:3000])
            if st.button("🗑️ 删除", key=f"del_{idx}"):
                delete_skill_file(skill_path)
                st.rerun()
