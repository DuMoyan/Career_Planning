# MVP 发布验证报告

验证日期：2026-11-05（Asia/Shanghai）
分支：`feature/career-planning-mvp`

## 环境

- Windows / PowerShell
- 主机 Python 3.13.5；部署镜像目标 Python 3.11
- Node.js 24.10.0、pnpm 10.30.3
- Docker Desktop 4.98.0、Docker Engine 29.9.2、Compose 5.6.1

## 自动化结果

- `ruff check app tests`：通过。
- Alembic PostgreSQL 离线迁移 `0001`–`0010`：生成成功。
- `pytest --cov=app --cov-report=term`：79 项通过，总覆盖率 89%。
- 前端 `pnpm test --run`：21 项通过。
- 前端 `vue-tsc -b && vite build`：通过，生产包成功生成。
- 幂等种子：重复执行后用户 3、量表 2、题目 57（36/21）、能力项 9、岗位 4，数量稳定。

## 并发一致性

- 50 次同键计划激活：通过，仅一个激活版本及一套任务。
- 50 次同键任务打卡：通过，仅一条打卡记录及一次状态变化。
- 精确选择器复验结果：2 passed。

## 容器与冒烟

PostgreSQL、Redis、FastAPI、Nginx 四服务镜像已完成真实构建和启动，四个容器的健康检查均为 `healthy`。Alembic 在后端启动前从 `DATABASE_URL` 读取容器数据库地址并成功执行 `0001`–`0010` 迁移。

通过 Nginx 容器入口 `http://localhost:8080` 执行真实 HTTP 冒烟，全部 8 步通过：学生登录、读取档案、读取两套量表、比较两个岗位、规则模式生成规划、激活计划、任务打卡、获取周报。空数据卷重建验收涉及删除本地 PostgreSQL 与上传演示卷，等待明确的数据删除授权后执行。

## 已知限制

运行时演示装配目前采用内存仓储以支持无外部依赖演示；数据库模型与迁移存在，但全面 SQLAlchemy 仓储替换、生产对象存储、集中日志、HTTPS、真实模型供应商和异步任务队列属于后续生产化工作。详细延期范围见需求追踪矩阵。
