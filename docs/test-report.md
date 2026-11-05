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
- Alembic PostgreSQL 迁移 `0001`–`0011`：容器启动时执行成功，数据库处于 `0011_plan_activation_requests (head)`。
- `ruff check app tests`：通过，无错误。
- `pytest --cov=app --cov-report=term -q`：92 项通过，总覆盖率 89%。
- 前端 `pnpm test -- --run`：25 项通过（12 个测试文件）。
- 前端 `vue-tsc -b && vite build`：通过，生产包成功生成。
- 生产重启集成测试：档案、目标、计划、任务、打卡、测评进度与结果、简历元数据与文件、能力证据和周报均通过跨应用重启验证。

## 并发一致性

- 50 次同键计划激活：通过，仅一个激活版本及一套任务。
- 50 次同键任务打卡：通过，仅一条打卡记录及一次状态变化。
- 精确选择器复验结果：2 passed。

## 容器与冒烟

PostgreSQL、Redis、FastAPI、Nginx 四服务镜像已完成真实构建和启动，四个容器的健康检查均为 `healthy`。Alembic 在后端启动前从 `DATABASE_URL` 读取容器数据库地址并成功执行 `0001`–`0011` 迁移。

通过 Nginx 容器入口 `http://localhost:8080` 执行真实 HTTP 验证：8 步学生闭环冒烟通过；档案写入、异步规则规划从 `running` 收敛到 `completed`、后端容器重启、档案和规划运行记录重读也全部成功。为避免删除现有数据卷，另在 PostgreSQL 容器中创建专用临时空库，完整执行 `0001`–`0011` 后确认处于 head，并清理该临时库。

## 已知限制

生产装配使用 SQLAlchemy/PostgreSQL 与磁盘命名卷；开发和测试装配保留内存实现。生产对象存储、集中日志、HTTPS、真实模型供应商配置以及分布式异步任务队列属于后续生产化工作。详细延期范围见需求追踪矩阵。
