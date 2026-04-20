import streamlit as st
from pathlib import Path

from config.models import PROVIDERS, MODEL_CONFIG, TARGET_PLATFORMS, PRESETS
from config.paths import OUTPUT_ROOT, WORK_DIR
from config.settings import APP_TITLE, APP_SUBTITLE, SUPPORTED_FILE_TYPES, DEFAULT_SKILL_NAME
from utils.file_utils import save_uploaded_file, get_file_size_mb
from utils.helpers import mask_content, generate_skill_name
from core.history import get_history_skills, read_skill_content, delete_skill as delete_skill_file

st.set_page_config(page_title="Skill Seekers", layout="wide")
st.title(APP_TITLE)
st.markdown(APP_SUBTITLE)
st.divider()

api_provider = st.sidebar.selectbox("选择AI提供商", PROVIDERS, index=0)

api_key = None
api_secret = None
model_name = None
base_url = None
env_config = {}
enhance_level = 0

if api_provider == "Anthropic (Claude)":
    api_key = st.sidebar.text_input("Anthropic API Key", type="password")
    model_name = st.sidebar.selectbox("选择模型", MODEL_CONFIG[api_provider]["models"])
    if api_key:
        env_config["ANTHROPIC_API_KEY"] = api_key
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "OpenAI":
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    model_name = st.sidebar.selectbox("选择模型", MODEL_CONFIG[api_provider]["models"])
    if api_key:
        env_config["OPENAI_API_KEY"] = api_key
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "Google Gemini":
    api_key = st.sidebar.text_input("Google API Key", type="password")
    model_name = st.sidebar.selectbox("选择模型", MODEL_CONFIG[api_provider]["models"])
    if api_key:
        env_config["GOOGLE_API_KEY"] = api_key
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider in ["智谱AI (GLM 系列)", "阿里云 通义千问 (Qwen 系列)", "字节跳动 豆包大模型", "DeepSeek 深度求索"]:
    api_key = st.sidebar.text_input(f"{api_provider} API Key", type="password")
    model_name = st.sidebar.selectbox("选择模型", MODEL_CONFIG[api_provider]["models"])
    if api_key:
        config = MODEL_CONFIG[api_provider]
        env_config[config["env_key"]] = api_key
        if "base_url" in config:
            env_config["OPENAI_BASE_URL"] = config["base_url"]
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "Moonshot AI (Kimi)":
    api_key = st.sidebar.text_input("Moonshot API Key", type="password")
    model_name = st.sidebar.selectbox("选择模型", MODEL_CONFIG[api_provider]["models"])
    if api_key:
        env_config["MOONSHOT_API_KEY"] = api_key
        env_config["OPENAI_BASE_URL"] = MODEL_CONFIG[api_provider]["base_url"]
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "百度智能云 千帆 (文心一言)":
    api_key = st.sidebar.text_input("千帆 Access Key", type="password")
    api_secret = st.sidebar.text_input("千帆 Secret Key", type="password")
    model_name = st.sidebar.selectbox("选择模型", MODEL_CONFIG[api_provider]["models"])
    if api_key and api_secret:
        env_config["QIANFAN_ACCESS_KEY"] = api_key
        env_config["QIANFAN_SECRET_KEY"] = api_secret
        env_config["OPENAI_BASE_URL"] = MODEL_CONFIG[api_provider]["base_url"]
        enhance_level = st.sidebar.slider("AI增��等级", 0, 2, 2)

elif api_provider == "不使用AI增强":
    enhance_level = 0
    st.sidebar.info("已关闭AI增强")

st.sidebar.divider()
st.sidebar.header("⚙️ 蒸馏基础参数")

if 'redistill_skill' in st.session_state:
    default_name = st.session_state['redistill_skill']
    del st.session_state['redistill_skill']
else:
    default_name = DEFAULT_SKILL_NAME

skill_name = st.sidebar.text_input("Skill名称", value=default_name)

preset = st.sidebar.selectbox("生成预设", list(PRESETS.keys()), index=1)
preset_value = preset

target_platform = st.sidebar.selectbox("目标平台", TARGET_PLATFORMS, index=0)
use_ocr = st.sidebar.checkbox("开启OCR", value=False)
password = st.sidebar.text_input("PDF密码", type="password")

output_root = Path(OUTPUT_ROOT)
output_root.mkdir(exist_ok=True)

history_skills = get_history_skills(output_root)

st.sidebar.divider()
st.sidebar.header("📜 历史记录")
if history_skills:
    for skill in history_skills:
        st.sidebar.markdown(f"**{skill['name']}**")
else:
    st.sidebar.info("暂无历史记录")

tab_new, tab_history = st.tabs(["🆕 新建蒸馏", "📜 历史记录"])

with tab_history:
    st.subheader("📜 历史记录")
    if not history_skills:
        st.info("暂无历史记录")
    else:
        for idx, skill in enumerate(history_skills):
            with st.expander(f"📦 {skill['name']}", expanded=(idx == 0)):
                skill_path = skill["path"]
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**预览**")
                    content = read_skill_content(skill_path)
                    if content:
                        st.markdown(content[:1000] + "..." if len(content) > 1000 else content)

                with col2:
                    st.markdown("**下载**")
                    zip_files = list(skill_path.glob("*.zip"))
                    for zf in zip_files:
                        with open(zf, "rb") as f:
                            st.download_button(
                                label=f"📥 {zf.stem}",
                                data=f,
                                file_name=zf.name
                            )

                st.markdown("---")
                if st.button(f"🔄 重新蒸馏", key=f"rd_{skill['name']}"):
                    st.session_state['redistill_skill'] = skill['name']
                    st.rerun()

                if st.button(f"🗑️ 删除", key=f"dl_{skill['name']}"):
                    delete_skill_file(skill_path)
                    st.success(f"已删除 {skill['name']}")
                    st.rerun()

with tab_new:
    st.subheader("📄 上传文档")
    upload_mode = st.radio("上传模式", ["单文件", "批量上传"], horizontal=True)

    if upload_mode == "单文件":
        uploaded_file = st.file_uploader("支持PDF、DOCX、EPub", type=SUPPORTED_FILE_TYPES)
        uploaded_files = [uploaded_file] if uploaded_file else []
    else:
        uploaded_files = st.file_uploader("批量上传", type=SUPPORTED_FILE_TYPES, accept_multiple_files=True)
        if uploaded_files:
            st.markdown(f"**已选择 {len(uploaded_files)} 个文件**")
            for f in uploaded_files:
                st.markdown(f"- {f.name} ({get_file_size_mb(f.size)} MB)")
        uploaded_file = uploaded_files[0] if uploaded_files else None

    if uploaded_files:
        total_size = sum(f.size for f in uploaded_files)
        st.success(f"已选择 {len(uploaded_files)} 个文件，共 {get_file_size_mb(total_size)} MB")

        if api_provider not in ["不使用AI增强", "--- 海���主流模型 ---", "--- 国内主流模型 ---"]:
            if api_provider == "百度智能云 千帆 (文心一言)" and (not api_key or not api_secret):
                st.warning("请输入千帆的Access Key和Secret Key")
            elif not api_key:
                st.warning(f"请输入{api_provider}的API Key")

        st.divider()
        st.subheader("🚀 开始蒸馏")

        if st.button("开始执行Skill蒸馏", type="primary", use_container_width=True):
            import subprocess
            import tempfile

            results = []
            progress_bar = st.progress(0)

            for idx, uploaded_file in enumerate(uploaded_files):
                progress_bar.progress(idx / len(uploaded_files))
                st.markdown(f"### 处理 [{idx + 1}/{len(uploaded_files)}]：{uploaded_file.name}")

                current_skill_name = generate_skill_name(uploaded_file.name)

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir) / uploaded_file.name
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    cmd = [
                        "skill-seekers", "create",
                        str(temp_path),
                        "--name", current_skill_name,
                        "--preset", preset_value,
                        "--enhance-level", str(enhance_level),
                        "--output", str(output_root / current_skill_name)
                    ]
                    if use_ocr:
                        cmd.append("--ocr")
                    if password:
                        cmd.extend(["--password", password])

                    import os
                    run_env = os.environ.copy()
                    run_env.update(env_config)

                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            check=True,
                            cwd=WORK_DIR,
                            env=run_env
                        )
                        safe_stdout = mask_content(result.stdout, api_key, api_secret)
                        safe_stderr = mask_content(result.stderr, api_key, api_secret)

                        results.append({
                            "name": current_skill_name,
                            "status": "success",
                            "output": output_root / current_skill_name
                        })
                        st.success(f"✅ {uploaded_file.name} 完成")
                    except subprocess.CalledProcessError as e:
                        results.append({
                            "name": current_skill_name,
                            "status": "error",
                            "error": e.stderr
                        })
                        st.error(f"❌ {uploaded_file.name} 失败")

            progress_bar.progress(1.0)
            st.markdown("---")

            if results:
                success_count = sum(1 for r in results if r["status"] == "success")
                st.success(f"🎉 完成！成功 {success_count}/{len(results)} 个")

                if success_count > 0:
                    st.subheader("📥 下载")
                    cols = st.columns(min(3, success_count))
                    for i, result in enumerate(results):
                        if result["status"] == "success":
                            zf = list(result["output"].glob("*.zip"))
                            if zf:
                                with open(zf[0], "rb") as f:
                                    with cols[i % 3]:
                                        st.download_button(
                                            label=f"📥 {result['name']}",
                                            data=f,
                                            file_name=zf[0].name
                                        )

                st.info(f"📂 文件保存在：{output_root}")
                st.rerun()