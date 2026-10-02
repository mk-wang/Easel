# 已知限制

## 原生 Agent

- 原生 agent 可读取技能说明、引用文档和画像，创建不覆盖的文本产物，并在交互式聊天中经用户逐次审批后运行技能目录内已注册的 Python/Node/Bun 脚本；不会暴露 shell 命令。无法展示审批卡的后台 API 会关闭脚本工具。画像 onboarding 仅能修改新画像中既有的六维 Markdown 文件，且只有实际文件变化才报告增强成功。账号登录仍在工作台进行。当前原生模型供应商暂不复用本机 Claude/Gemini/Codex CLI 的订阅登录态；旧的免 API Key 接入依赖 OpenClaw，Easel 不再读取或调用它。暂时请配置 API 兼容供应商或 Anthropic API；本机 CLI 适配器需分别设计受限协议后再实现。
- 当前 provider 请求按轮返回完整模型文本；SSE 事件重放可恢复，但 token 不是从模型端逐段流出。
- `ask_user` 问答卡片保存在 Web 进程内存中；服务重启或多 worker 部署时，待回答卡片不会跨进程同步。
- 会话锁为单进程锁；推荐使用 setup 默认启动方式的单个 Web worker。

## 旧版 OpenClaw 记录

本分支的安装器、CLI 和聊天 API 不再依赖 OpenClaw。历史 gateway 配置与同步脚本保留在仓库中供旧部署/历史问题参考，但不参与原生运行时。
