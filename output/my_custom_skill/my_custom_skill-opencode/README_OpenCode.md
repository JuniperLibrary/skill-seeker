# my_custom_skill - OpenCode Skill
## 安装使用方法
### 方法1：项目本地使用（推荐）
1. 将本压缩包所有内容解压到你的项目根目录
2. 确保解压后目录结构为：`你的项目/.opencode/skills/my_custom_skill/SKILL.md`
3. 重启OpenCode，代理会自动发现并加载该Skill

### 方法2：全局安装使用
1. 解压压缩包，找到 `.opencode/skills/my_custom_skill` 文件夹
2. 将该文件夹复制到全局配置目录：
   - Windows：`C:\Users\你的用户名\.config\opencode\skills\`
   - Mac/Linux：`~/.config/opencode/skills/`
3. 重启OpenCode，该Skill会在所有项目中生效

### 验证方法
在OpenCode对话中输入「请使用my_custom_skill的内容回答问题」，AI会自动调用该Skill的知识进行回复
