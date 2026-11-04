# AI智能体大学生职业生涯规划系统（MVP）

学生可完成档案、测评、能力证据、岗位比较、可降级规划、任务打卡和周报复盘；导师仅在授权范围内查看进展并评论，管理员仅查看岗位、量表版本和审计摘要。

## 本地验证

```powershell
cd backend; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
cd ..\frontend; pnpm test --run; pnpm build
```

## 容器启动

复制 `.env.example` 为 `.env` 并更换密钥，然后运行 `docker compose up --build -d`，访问 http://localhost:8080 。演示账号为 `demo-student`、`demo-mentor`、`demo-admin`，统一演示密码 `Demo!2026`，不得用于生产。

详见 [部署说明](docs/deployment.md)、[演示脚本](docs/demo-script.md)和[需求追踪](docs/requirements-traceability.md)。
