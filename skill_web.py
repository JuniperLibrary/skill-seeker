import streamlit as st
import os
import subprocess
import tempfile
import shutil
import json
from pathlib import Path

# --- 页面基础配置 ---
st.set_page_config(page_title="Skill Seekers 文档蒸馏器 全功能修复版", layout="wide")
st.title("🤖 Skill Seekers 文档蒸馏工具 | 全模型+全平台支持")
st.markdown("支持海外+国内主流大模型，一键完成文档到AI Skill的蒸馏，内置全平台安装使用教程")
st.divider()

# --- 侧边栏：核心配置区域 ---
st.sidebar.header("🔑 AI模型与密钥配置")
st.sidebar.caption("选择AI提供商，输入对应API Key即可使用")

# 模型提供商分组：海外 + 国内
api_provider = st.sidebar.selectbox(
    "选择AI提供商",
    [
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
    ],
    index=0
)

# 全局变量初始化
api_key = None
api_secret = None
model_name = None
base_url = None
env_config = {}
enhance_level = 0

# --------------------------
# 动态渲染配置项：根据选择的提供商显示对应输入框
# --------------------------
# 1. 海外模型配置
if api_provider == "Anthropic (Claude)":
    api_key = st.sidebar.text_input(
        "Anthropic API Key",
        type="password",
        help="密钥仅在当前会话生效，不会持久化存储"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        index=0
    )
    if api_key:
        env_config["ANTHROPIC_API_KEY"] = api_key
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2, help="2=深度增强，效果最佳")

elif api_provider == "OpenAI":
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        index=0
    )
    if api_key:
        env_config["OPENAI_API_KEY"] = api_key
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "Google Gemini":
    api_key = st.sidebar.text_input(
        "Google API Key",
        type="password"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
        index=0
    )
    if api_key:
        env_config["GOOGLE_API_KEY"] = api_key
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

# 2. 国内模型配置
elif api_provider == "智谱AI (GLM 系列)":
    api_key = st.sidebar.text_input(
        "智谱API Key",
        type="password",
        help="从 https://open.bigmodel.cn/ 获取"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["glm-4-plus", "glm-4-air", "glm-4-flash", "glm-4-long"],
        index=0
    )
    base_url = "https://open.bigmodel.cn/api/paas/v4/"
    if api_key:
        env_config["OPENAI_API_KEY"] = api_key
        env_config["OPENAI_BASE_URL"] = base_url
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "阿里云 通义千问 (Qwen 系列)":
    api_key = st.sidebar.text_input(
        "阿里云API Key (DashScope)",
        type="password",
        help="从 https://dashscope.aliyun.com/ 获取"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["qwen-max-latest", "qwen-plus-latest", "qwen-turbo-latest", "qwen2.5-72b-instruct"],
        index=0
    )
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if api_key:
        env_config["OPENAI_API_KEY"] = api_key
        env_config["OPENAI_BASE_URL"] = base_url
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "字节跳动 豆包大模型":
    api_key = st.sidebar.text_input(
        "火山引擎方舟API Key",
        type="password",
        help="从 https://www.volcengine.com/ark 获取"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["doubao-1.5-pro-32k-250115", "doubao-1.5-flash-8k-250115"],
        index=0
    )
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    if api_key:
        env_config["OPENAI_API_KEY"] = api_key
        env_config["OPENAI_BASE_URL"] = base_url
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "DeepSeek 深度求索":
    api_key = st.sidebar.text_input(
        "DeepSeek API Key",
        type="password",
        help="从 https://platform.deepseek.com/ 获取"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["deepseek-chat", "deepseek-coder"],
        index=0
    )
    base_url = "https://api.deepseek.com/v1"
    if api_key:
        env_config["OPENAI_API_KEY"] = api_key
        env_config["OPENAI_BASE_URL"] = base_url
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "Moonshot AI (Kimi)":
    api_key = st.sidebar.text_input(
        "Moonshot API Key",
        type="password",
        help="从 https://platform.moonshot.cn/ 获取"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        index=0
    )
    base_url = "https://api.moonshot.cn/v1"
    if api_key:
        env_config["MOONSHOT_API_KEY"] = api_key
        env_config["OPENAI_BASE_URL"] = base_url
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

elif api_provider == "百度智能云 千帆 (文心一言)":
    api_key = st.sidebar.text_input(
        "千帆 API Key (Access Key)",
        type="password",
        help="从 https://qianfan.cloud.baidu.com/ 获取"
    )
    api_secret = st.sidebar.text_input(
        "千帆 Secret Key",
        type="password"
    )
    model_name = st.sidebar.selectbox(
        "选择模型",
        ["ernie-4.0-turbo-8k", "ernie-3.5-8k"],
        index=0
    )
    base_url = "https://qianfan.baidubce.com/v2"
    if api_key and api_secret:
        env_config["QIANFAN_ACCESS_KEY"] = api_key
        env_config["QIANFAN_SECRET_KEY"] = api_secret
        env_config["OPENAI_BASE_URL"] = base_url
        enhance_level = st.sidebar.slider("AI增强等级", 0, 2, 2)

# 不使用AI增强的情况
elif api_provider == "不使用AI增强":
    enhance_level = 0
    st.sidebar.info("已关闭AI增强，仅执行基础文档提取与Skill打包")

# --- 蒸馏基础参数配置 ---
st.sidebar.divider()
st.sidebar.header("⚙️ 蒸馏基础参数")
skill_name = st.sidebar.text_input("Skill 名称", value="my_custom_skill", help="仅支持英文、数字、下划线和横杠")

# 【新增官方原生参数】生成预设
preset = st.sidebar.selectbox(
    "生成预设 (Preset)",
    ["quick (1-2分钟)", "standard (5-10分钟)", "comprehensive (20-60分钟)"],
    index=1,
    help="quick=快速测试, standard=默认推荐, comprehensive=深度分析"
)
preset_value = preset.split(" ")[0]

# 保留原有的目标平台选择（仅用于后续打包适配，不再传入CLI）
target_platform = st.sidebar.selectbox(
    "目标输出平台",
    ["opencode", "claude", "cursor", "openai", "gemini", "markdown", "langchain", "chroma"],
    index=0,
    help="选择你要使用的AI平台，生成对应格式的Skill包"
)

use_ocr = st.sidebar.checkbox("开启OCR识别", value=False, help="仅扫描版/图片PDF需要开启，需提前安装Tesseract引擎")
password = st.sidebar.text_input("PDF解压密码", value="", type="password", help="加密PDF需填写，无密码留空")

# --- 主界面：文件上传与执行 ---
st.subheader("📄 第一步：上传文档")
uploaded_file = st.file_uploader("支持PDF、DOCX、EPub格式，Word文档可直接上传无需转PDF", type=["pdf", "docx", "epub"])

# 上传成功后的校验与提示
if uploaded_file is not None:
    st.success(f"✅ 文件上传成功：{uploaded_file.name} | 文件大小：{round(uploaded_file.size / 1024 / 1024, 2)} MB")

    # 配置合法性校验
    if api_provider not in ["不使用AI增强", "--- 海外主流模型 ---", "--- 国内主流模型 ---"]:
        # 百度千帆需要双密钥校验
        if api_provider == "百度智能云 千帆 (文心一言)" and (not api_key or not api_secret):
            st.warning("⚠️ 请完整输入千帆的Access Key和Secret Key，否则无法使用AI增强")
        # 其他模型校验API Key
        elif not api_key:
            st.warning(f"⚠️ 请输入{api_provider}的API Key，否则无法使用AI增强")

    st.divider()
    st.subheader("🚀 第二步：开始蒸馏")
    if st.button("开始执行Skill蒸馏", type="primary", use_container_width=True):
        # 合并系统环境变量 + 自定义配置
        run_env = os.environ.copy()
        run_env.update(env_config)

        # 📌 修改：固定使用你指定的输出目录
        output_root = Path("/Users/dingchuan/Documents/Repos/skill-seeker/output")
        output_root.mkdir(exist_ok=True)  # 确保目录存在

        # 创建临时目录保存上传的文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = Path(temp_dir) / uploaded_file.name
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # ==============================================
            # 执行命令
            # ==============================================
            cmd = [
                "skill-seekers", "create",
                str(temp_file_path),
                "--name", skill_name,
                "--preset", preset_value,
                "--enhance-level", str(enhance_level),
                "--output", str(output_root / skill_name)  # 输出到指定目录
            ]
            # 附加官方支持的可选参数
            if use_ocr:
                cmd.append("--ocr")
            if password:
                cmd.extend(["--password", password])

            # 执行命令并捕获输出
            with st.status("正在执行蒸馏...", expanded=True) as status:
                try:
                    st.write("正在解析文档...")
                    st.code("执行的官方CLI命令：\n" + " ".join(cmd), language="bash")

                    # 📌 修改：工作目录也切换到你的项目目录，确保路径稳定
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True,
                        cwd="/Users/dingchuan/Documents/Repos/skill-seeker",
                        env=run_env
                    )

                    # 日志脱敏处理
                    safe_stdout = result.stdout
                    safe_stderr = result.stderr
                    if api_key:
                        safe_stdout = safe_stdout.replace(api_key, "*******脱敏*******")
                        safe_stderr = safe_stderr.replace(api_key, "*******脱敏*******")
                    if api_secret:
                        safe_stdout = safe_stdout.replace(api_secret, "*******脱敏*******")
                        safe_stderr = safe_stderr.replace(api_secret, "*******脱敏*******")

                    st.write("✅ 文档解析完成，AI增强处理完成")
                    output_dir = output_root / skill_name
                    target_zip = output_dir / f"{skill_name}-{target_platform}.zip"

                    # ==============================================
                    # 完整保留原有的全平台适配打包逻辑
                    # ==============================================
                    # 1. OpenCode专属适配处理
                    if target_platform == "opencode":
                        st.write("🔧 正在生成OpenCode专属适配包...")
                        opencode_dir = output_dir / f"{skill_name}-opencode"
                        opencode_zip = output_dir / f"{skill_name}-opencode.zip"

                        # 1. 创建OpenCode专属目录结构
                        opencode_skill_dir = opencode_dir / ".opencode" / "skills" / skill_name
                        opencode_skill_dir.mkdir(parents=True, exist_ok=True)

                        # 2. 复制生成的SKILL.md和源文件
                        skill_md_path = output_dir / "SKILL.md"
                        source_dir = output_dir / "source"

                        if skill_md_path.exists():
                            shutil.copy2(skill_md_path, opencode_skill_dir / "SKILL.md")
                        if source_dir.exists():
                            shutil.copytree(source_dir, opencode_skill_dir / "source", dirs_exist_ok=True)

                        # 3. 生成OpenCode专属配置文件
                        opencode_config = {
                            "$schema": "https://opencode.ai/config.json",
                            "skill": {
                                "name": skill_name,
                                "version": "1.0.0",
                                "description": f"基于文档蒸馏生成的OpenCode Skill：{skill_name}"
                            },
                            "permission": {
                                "skill": {
                                    skill_name: "allow",
                                    "*": "ask"
                                }
                            }
                        }
                        with open(opencode_dir / "opencode.json", "w", encoding="utf-8") as f:
                            json.dump(opencode_config, f, indent=2, ensure_ascii=False)

                        # 4. 生成使用说明
                        readme_content = f"# {skill_name} - OpenCode Skill\n## 安装使用方法\n### 方法1：项目本地使用（推荐）\n1. 将本压缩包所有内容解压到你的项目根目录\n2. 确保解压后目录结构为：`你的项目/.opencode/skills/{skill_name}/SKILL.md`\n3. 重启OpenCode，代理会自动发现并加载该Skill\n\n### 方法2：全局安装使用\n1. 解压压缩包，找到 `.opencode/skills/{skill_name}` 文件夹\n2. 将该文件夹复制到全局配置目录：\n   - Windows：`C:\\Users\\你的用户名\\.config\\opencode\\skills\\`\n   - Mac/Linux：`~/.config/opencode/skills/`\n3. 重启OpenCode，该Skill会在所有项目中生效\n\n### 验证方法\n在OpenCode对话中输入「请使用{skill_name}的内容回答问题」，AI会自动调用该Skill的知识进行回复\n"
                        with open(opencode_dir / "README_OpenCode.md", "w", encoding="utf-8") as f:
                            f.write(readme_content)

                        # 5. 打包为OpenCode专属zip包
                        shutil.make_archive(str(opencode_zip).replace(".zip", ""), "zip", opencode_dir)
                        target_zip = opencode_zip
                        st.write("✅ OpenCode专属适配包生成完成")

                    # 2. 其他平台通用打包处理
                    else:
                        st.write(f"🔧 正在生成{target_platform}平台适配包...")
                        platform_dir = output_dir / f"{skill_name}-{target_platform}"
                        platform_dir.mkdir(parents=True, exist_ok=True)

                        # 复制核心文件
                        skill_md_path = output_dir / "SKILL.md"
                        source_dir = output_dir / "source"
                        if skill_md_path.exists():
                            shutil.copy2(skill_md_path, platform_dir / "SKILL.md")
                        if source_dir.exists():
                            shutil.copytree(source_dir, platform_dir / "source", dirs_exist_ok=True)

                        # 生成对应平台的使用说明
                        with open(platform_dir / f"README_{target_platform}.md", "w", encoding="utf-8") as f:
                            f.write(
                                f"# {skill_name} - {target_platform} 平台Skill\n## 核心文件说明\n- SKILL.md：蒸馏后的核心知识、Prompt规则、上下文约束\n- source/：原始文档解析后的源文件\n\n## 安装使用方法\n请参考Streamlit工具页面中的「{target_platform}平台安装教程」标签页，获取详细步骤")

                        # 打包
                        shutil.make_archive(str(target_zip).replace(".zip", ""), "zip", platform_dir)
                        st.write(f"✅ {target_platform}平台适配包生成完成")

                    st.write("🎉 Skill生成成功！")
                    status.update(label="蒸馏执行完成！", state="complete", expanded=False)

                    st.balloons()
                    st.success("🎉 恭喜！Skill蒸馏已全部完成")

                    # 展示运行日志
                    with st.expander("查看完整运行日志"):
                        st.code(safe_stdout, language="text")

                    # 下载按钮
                    if target_zip.exists():
                        with open(target_zip, "rb") as f:
                            st.download_button(
                                label=f"📥 下载 {target_platform} 平台Skill安装包",
                                data=f,
                                file_name=target_zip.name,
                                type="primary",
                                use_container_width=True
                            )
                        # 额外提供核心SKILL.md下载
                        skill_md_path = output_dir / "SKILL.md"
                        if skill_md_path.exists():
                            with open(skill_md_path, "rb") as f:
                                st.download_button(
                                    label="📥 下载核心文件 SKILL.md（全平台通用）",
                                    data=f,
                                    file_name="SKILL.md",
                                    use_container_width=True
                                )
                    st.info(f"📂 所有生成文件已保存在：{output_dir}")

                except subprocess.CalledProcessError as e:
                    status.update(label="蒸馏执行出错", state="error", expanded=True)
                    # 错误日志脱敏
                    safe_err = e.stderr
                    safe_out = e.stdout
                    if api_key:
                        safe_err = safe_err.replace(api_key, "*******脱敏*******")
                        safe_out = safe_out.replace(api_key, "*******脱敏*******")
                    if api_secret:
                        safe_err = safe_err.replace(api_secret, "*******脱敏*******")
                        safe_out = safe_out.replace(api_secret, "*******脱敏*******")
                    st.error("❌ 执行过程中出现错误，详细信息如下：")
                    st.subheader("错误详情 (Stderr)：")
                    st.code(safe_err, language="text")
                    if safe_out:
                        st.subheader("运行日志 (Stdout)：")
                        st.code(safe_out, language="text")

# --- 完整保留原有的全平台Skill安装使用教程板块 ---
st.divider()
st.header("📚 各平台Skill安装使用教程")
# 动态提示当前选中的平台
st.info(f"你当前选择的目标平台是：**{target_platform}**，请点击下方对应标签查看详细安装步骤")

# 按平台拆分标签页（完整保留原有的8个标签页）
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "OpenCode", "Claude", "Cursor", "OpenAI/ChatGPT",
    "Google Gemini", "Markdown通用", "LangChain", "Chroma"
])

# 1. OpenCode平台教程
with tab1:
    st.subheader("OpenCode 平台Skill安装教程")
    st.write("#### 方法1：项目本地安装（推荐，单项目专属生效）")
    st.write("1.  下载生成的 `opencode` 专属Skill压缩包")
    st.write("2.  将压缩包内的所有内容解压到你的项目根目录")
    st.write(f"3.  确认解压后的目录结构为：`你的项目/.opencode/skills/{skill_name}/SKILL.md`")
    st.write("4.  打开OpenCode客户端，加载该项目")
    st.write("5.  重启OpenCode，代理会自动扫描并加载该Skill，无需额外配置")
    st.write("6.  验证方法：在对话中输入「请使用[你的Skill名称]的内容回答问题」，即可触发Skill调用")
    st.write("")
    st.write("#### 方法2：全局安装（所有项目通用生效）")
    st.write("1.  下载并解压Skill压缩包，找到 `.opencode/skills/你的Skill名称` 文件夹")
    st.write("2.  打开OpenCode全局配置目录：")
    st.write("   - Windows系统：`C:\\Users\\你的用户名\\.config\\opencode\\skills\\`")
    st.write("   - Mac/Linux系统：`~/.config/opencode/skills/`")
    st.write("3.  将解压后的Skill文件夹复制到上述 `skills` 目录中")
    st.write("4.  重启OpenCode，该Skill会在所有打开的项目中自动生效")
    st.write("")
    st.write("#### 注意事项")
    st.write("- 生成的压缩包自带 `opencode.json` 权限配置文件，默认允许该Skill自动加载，无需手动修改权限")
    st.write("- 若Skill未自动加载，可检查目录结构是否正确，或在OpenCode中执行「Reload Skills」命令刷新")

# 2. Claude平台教程
with tab2:
    st.subheader("Claude 平台Skill安装教程")
    st.write("#### 方法1：Claude 网页版（claude.ai）")
    st.write("1.  下载生成的 `claude` 格式Skill压缩包")
    st.write("2.  打开 claude.ai 并登录你的账号")
    st.write("3.  新建一个对话，点击输入框上方的「回形针附件」图标")
    st.write("4.  选择「Add Knowledge」，点击「Upload file」，上传下载的zip压缩包")
    st.write("5.  上传完成后，该Skill会被添加到你的Claude知识库中，对话时会自动调用")
    st.write("6.  手动触发：在对话中输入「基于[你的Skill名称]的内容回答」，即可精准调用")
    st.write("")
    st.write("#### 方法2：Claude Desktop 客户端")
    st.write("1.  打开Claude客户端，点击左下角的设置图标")
    st.write("2.  选择「Knowledge」→「Upload Knowledge」")
    st.write("3.  上传下载的Skill压缩包，等待解析完成")
    st.write("4.  该Skill会在所有对话中生效，支持跨对话调用")
    st.write("")
    st.write("#### 注意事项")
    st.write("- Claude 免费版单知识库最大支持200MB文件，超出请拆分文档后分批蒸馏")
    st.write("- 上传后可在「Settings → Knowledge」中管理已上传的Skill，支持重命名、删除")

# 3. Cursor平台教程
with tab3:
    st.subheader("Cursor 编辑器Skill安装教程")
    st.write("#### 方法1：项目级规则（推荐，仅当前项目生效）")
    st.write("1.  下载生成的 `cursor` 格式Skill包，解压后找到 `.cursorrules` 文件")
    st.write("2.  将该文件复制到你的项目根目录")
    st.write("3.  重启Cursor编辑器，打开该项目，AI会自动加载该Skill规则")
    st.write("4.  验证方法：在代码编辑或对话中，输入相关问题，AI会自动遵循Skill中的内容回答")
    st.write("")
    st.write("#### 方法2：全局规则（所有项目生效）")
    st.write("1.  打开Cursor编辑器，点击左下角的设置图标")
    st.write("2.  选择「Features」→「Cursor Rules」")
    st.write("3.  将解压后的 `.cursorrules` 文件中的内容，完整复制到全局规则输入框中")
    st.write("4.  点击保存，所有项目都会自动应用该Skill规则")
    st.write("")
    st.write("#### 注意事项")
    st.write("- 项目级规则优先级高于全局规则，若同时存在，会优先使用项目根目录的 `.cursorrules`")
    st.write("- 支持在规则中添加代码规范、业务逻辑、专属知识库，AI会在生成代码时严格遵循")

# 4. OpenAI/ChatGPT平台教程
with tab4:
    st.subheader("OpenAI/ChatGPT 平台Skill安装教程")
    st.write("#### 方法1：导入为自定义GPTs（推荐，可分享、可精细化配置）")
    st.write("1.  下载生成的 `openai` 格式Skill包，解压后找到 `SKILL.md` 和 `source` 文件夹")
    st.write("2.  打开 chat.openai.com，登录账号，点击左侧「Explore」→「Create a GPT」")
    st.write("3.  在「Configure」选项卡中，填写GPT名称和描述，将 `SKILL.md` 中的内容完整复制到「Instructions」输入框")
    st.write("4.  点击「Knowledge」→「Upload files」，上传 `source` 文件夹中的所有文档内容")
    st.write("5.  配置完成后，点击「Save」，即可生成专属GPT，随时调用")
    st.write("6.  支持开启「Web Browsing」「Code Interpreter」等功能，扩展GPT能力")
    st.write("")
    st.write("#### 方法2：自定义指令（快速使用，全对话生效）")
    st.write("1.  打开ChatGPT，点击左下角你的头像→「Custom instructions」")
    st.write(
        "2.  将 `SKILL.md` 中的核心规则和内容，复制到「What would you like ChatGPT to know about you to provide better responses?」输入框")
    st.write("3.  点击保存，所有新建对话都会自动遵循该Skill的内容")
    st.write("")
    st.write("#### 注意事项")
    st.write("- 自定义GPTs需要ChatGPT Plus账号，自定义指令免费版账号也可使用")
    st.write("- 单GPT最多上传20个文件，超出请合并文档内容后重新蒸馏")

# 5. Google Gemini平台教程
with tab5:
    st.subheader("Google Gemini 平台Skill安装教程")
    st.write("#### 方法1：Gemini Advanced 网页版")
    st.write("1.  下载生成的 `gemini` 格式Skill包，解压后找到 `SKILL.md` 文件")
    st.write("2.  打开 gemini.google.com，登录你的账号")
    st.write("3.  点击左上角的菜单图标，选择「Settings」→「Custom instructions」")
    st.write("4.  将 `SKILL.md` 中的内容完整复制到自定义指令输入框中，点击保存")
    st.write("5.  新建对话，Gemini会自动遵循该Skill的内容进行回答")
    st.write("")
    st.write("#### 方法2：Gemini API 调用")
    st.write("1.  解压后的 `SKILL.md` 和 `source` 文件，可直接作为Prompt上下文，传入Gemini API的调用参数中")
    st.write("2.  支持将内容向量化后，结合RAG流程调用，生成的markdown格式可直接适配")
    st.write("3.  兼容LangChain、LlamaIndex等主流开发框架")
    st.write("")
    st.write("#### 注意事项")
    st.write("- 自定义指令功能需要Gemini Advanced账号，免费版可直接将SKILL内容粘贴到对话开头使用")
    st.write("- 支持上传文档到Gemini对话，可将source文件夹中的文件直接上传，作为上下文参考")

# 6. Markdown通用格式教程
with tab6:
    st.subheader("Markdown 通用格式使用教程")
    st.write("#### 适用场景")
    st.write("所有支持自定义Prompt、知识库、RAG系统的AI平台，包括但不限于：")
    st.write("- 国内大模型：文心一言、通义千问、智谱清言、豆包、Kimi等")
    st.write("- 开源大模型：Llama、Qwen、GLM、DeepSeek等")
    st.write("- 私有化部署AI平台、知识库系统、低代码AI平台")
    st.write("")
    st.write("#### 使用方法")
    st.write("1.  下载生成的 `markdown` 格式Skill包，解压后得到完整的 `SKILL.md` 文件")
    st.write("2.  该文件包含了蒸馏后的结构化知识、核心规则、问答指令、上下文约束，可直接复制使用")
    st.write("3.  快速使用：将 `SKILL.md` 中的内容完整复制到AI对话的开头，作为System Prompt使用")
    st.write("4.  知识库导入：可直接导入到任何知识库系统、RAG框架、向量数据库中，实现语义检索")
    st.write("5.  二次编辑：支持手动修改、补充内容，适配你的专属使用场景")
    st.write("")
    st.write("#### 核心优势")
    st.write("- 无平台限制，兼容所有支持Markdown格式的AI产品")
    st.write("- 内容完全开源，可自由修改、分发、二次开发")
    st.write("- 结构化排版，AI识别准确率高，无格式兼容问题")

# 7. LangChain平台教程
with tab7:
    st.subheader("LangChain 平台Skill使用教程")
    st.write("#### 前置准备")
    st.write("1.  下载生成的 `langchain` 格式Skill包，解压后得到结构化的Prompt模板和分块文档")
    st.write("2.  在你的Python项目中，安装核心依赖：")
    st.code("pip install langchain langchain-core langchain-community", language="bash")
    st.write("")
    st.write("#### 快速使用步骤")
    st.write("1.  导入Prompt模板：将解压后的Prompt模板文件，导入到你的项目中，作为System Prompt使用")
    st.code(
        "from langchain_core.prompts import SystemMessagePromptTemplate\n# 读取SKILL.md中的Prompt模板\nwith open(\"SKILL.md\", \"r\", encoding=\"utf-8\") as f:\n    skill_content = f.read()\n# 构建系统提示词\nsystem_prompt = SystemMessagePromptTemplate.from_template(skill_content)",
        language="python")
    st.write("2.  加载知识库文档：将 `source` 文件夹中的文档内容，通过LangChain文档加载器，加载到向量数据库中")
    st.code(
        "from langchain_community.document_loaders import DirectoryLoader\nfrom langchain_text_splitters import RecursiveCharacterTextSplitter\n# 加载文档\nloader = DirectoryLoader(\"./source\")\ndocuments = loader.load()\n# 文档分块\ntext_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)\nsplits = text_splitter.split_documents(documents)",
        language="python")
    st.write("3.  构建RAG问答链：结合检索器和LLM，实现基于该Skill的专属问答能力")
    st.code(
        "from langchain_core.runnables import RunnablePassthrough\nfrom langchain_core.output_parsers import StrOutputParser\n# 构建检索链\nrag_chain = (\n    {\"context\": retriever | format_docs, \"question\": RunnablePassthrough()}\n    | system_prompt\n    | llm\n    | StrOutputParser()\n)\n# 调用问答\nrag_chain.invoke(\"你的问题\")",
        language="python")
    st.write("")
    st.write("#### 注意事项")
    st.write("- 兼容LangChain v0.2+ 所有版本，支持Python 3.10+")
    st.write("- 支持对接所有主流LLM和向量数据库，可无缝集成到现有项目中")

# 8. Chroma向量数据库平台教程
with tab8:
    st.subheader("Chroma 向量数据库Skill使用教程")
    st.write("#### 前置准备")
    st.write("1.  下载生成的 `chroma` 格式Skill包，解压后得到分块后的文档数据、元数据和导入脚本")
    st.write("2.  安装Chroma核心依赖：")
    st.code("pip install chromadb", language="bash")
    st.write("")
    st.write("#### 快速使用步骤")
    st.write("1.  导入Skill知识库到Chroma")
    st.write("- 解压后的文件中包含了可直接执行的导入脚本，运行脚本即可一键完成知识库创建")
    st.code("python import_to_chroma.py", language="bash")
    st.write("- 手动导入方式：")
    st.code(
        "import chromadb\nfrom chromadb.utils import embedding_functions\n# 初始化Chroma客户端\nclient = chromadb.PersistentClient(path=\"./chroma_db\")\n# 创建集合（使用Skill名称作为集合名）\ncollection = client.create_collection(\n    name=\"your_skill_name\",\n    embedding_function=embedding_functions.DefaultEmbeddingFunction()\n)\n# 导入分块文档\ncollection.add(\n    documents=文档内容列表,\n    metadatas=元数据列表,\n    ids=文档id列表\n)",
        language="python")
    st.write("2.  语义检索调用")
    st.code(
        "# 查询相关内容\nresults = collection.query(\n    query_texts=[\"你的问题\"],\n    n_results=5\n)\n# 输出检索结果\nprint(results[\"documents\"])",
        language="python")
    st.write("3.  对接AI框架：导入完成后，可直接对接LangChain、LlamaIndex等主流RAG框架，实现专属问答能力")
    st.write("")
    st.write("#### 注意事项")
    st.write("- 支持本地持久化存储和服务端部署，可跨项目、跨设备调用")
    st.write("- 兼容所有主流Embedding模型，可根据你的需求更换嵌入函数")
    st.write("- 生成的分块文档已优化好长度和重叠率，无需二次处理")

# --- 底部补充说明（完整保留） ---
st.divider()
with st.expander("🔧 常见问题与基础使用说明"):
    st.write("1. Word文档处理：官方CLI已原生支持DOCX格式，可直接上传，无需手动转PDF，避免格式错乱")
    st.write("2.  国内模型API获取：点击每个模型输入框的「?」可直达官方API获取地址，大部分模型都有免费测试额度")
    st.write("3.  OCR功能：扫描版/图片PDF需要开启OCR，需提前安装Tesseract引擎，否则会执行失败")
    st.write("4.  依赖冲突：推荐使用uv创建虚拟环境运行，避免与本地其他Python包产生依赖冲突")
    st.write("5.  密钥安全：所有API密钥仅在当前浏览器会话中生效，不会上传、存储到任何地方，日志也会自动脱敏处理")
    st.write("6.  Skill生成失败：请检查API密钥是否正确、账户是否有可用余额、网络是否可正常访问对应模型接口")