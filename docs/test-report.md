# MVP 发布验证报告

验证日期：2026-11-04（Asia/Shanghai）  
分支：`feature/career-planning-mvp`

## 环境

- Windows / PowerShell
- 主机 Python 3.13.5；部署镜像目标 Python 3.11
- Node.js 24.10.0、pnpm 10.30.3
- Docker：未安装（`docker` 命令不存在）

## 自动化结果

- `ruff check app tests`：通过。
- Alembic PostgreSQL 离线迁移 `0001`–`0010`：生成成功。
- `pytest --cov=app --cov-report=term`：78 项通过，总覆盖率 89%。
- 前端 `pnpm test --run`：21 项通过。
- 前端 `vue-tsc -b && vite build`：通过，生产包成功生成。
- 幂等种子：重复执行后用户 3、量表 2、题目 57（36/21）、能力项 9、岗位 4，数量稳定。

## 并发一致性

- 50 次同键计划激活：通过，仅一个激活版本及一套任务。
- 50 次同键任务打卡：通过，仅一条打卡记录及一次状态变化。
- 精确选择器复验结果：2 passed。

## 容器与冒烟

已提供 PostgreSQL、Redis、FastAPI、Nginx 四服务 Compose、健康检查、迁移前置、持久卷、SPA 回退、SSE 禁缓冲和完整学生冒烟脚本。

本地 Uvicorn 真实 HTTP 冒烟已通过全部 8 步：学生登录、读取档案、读取两套量表、比较两个岗位、规则模式生成规划、激活计划、任务打卡、获取周报。当前主机尚未成功安装 Docker，因此未执行 `docker compose build/up/down -v`；此项不伪报通过，需在 Docker 可用后按 `docs/deployment.md` 复验容器构建与服务网络。

## 已知限制

运行时演示装配目前采用内存仓储以支持无外部依赖演示；数据库模型与迁移存在，但全面 SQLAlchemy 仓储替换、生产对象存储、集中日志、HTTPS、真实模型供应商和异步任务队列属于后续生产化工作。详细延期范围见需求追踪矩阵。
