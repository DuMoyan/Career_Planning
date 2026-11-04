# 部署说明

系统由 PostgreSQL、Redis、FastAPI 后端和 Nginx 前端四个服务组成。PostgreSQL 与上传文件使用命名卷；后端启动前执行 Alembic 迁移；Nginx 对 SSE 禁用缓冲并为 SPA 提供回退。

1. 安装 Docker Desktop，复制 `.env.example` 为 `.env` 并设置随机 `JWT_SECRET`。
2. 执行 `docker compose build`、`docker compose up -d`、`docker compose ps`。
3. 执行 `docker compose exec backend python -m app.cli.seed`。
4. 执行 `powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1`。

生产环境需替换演示账号、启用 HTTPS、对象存储、集中日志和密钥管理。
