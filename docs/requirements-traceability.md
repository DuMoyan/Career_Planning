# 需求追踪矩阵

| 能力 | API/页面 | 自动化证据 | 状态 |
|---|---|---|---|
| 认证、RBAC、审计 | `/auth`、角色路由 | `test_auth_api.py`、`LoginPage.spec.ts` | 已实现 |
| 档案、隐私授权、测评 | `/profiles`、`/consents`、`/assessments` | Task 3–4 后端与 Task 11 前端测试 | 已实现 |
| 能力证据、目标与 Gap | `/competencies`、`/targets` | Task 5–6、`competency.spec.ts`、`targets.spec.ts` | 已实现 |
| 可降级规划与版本 | `/plans/generations`、`/plans/versions` | Task 7–8、`planning.spec.ts` | 已实现 |
| 任务、打卡、周报 | `/tasks`、`/reports/weekly` | 50 并发测试、Task 9–10、前端测试 | 已实现 |
| 导师与管理员 | `/mentor`、`/admin` | `test_mentor_admin_api.py`、角色页面测试 | 已实现 |
| 四服务容器与冒烟 | `compose.yaml`、`scripts/smoke.ps1` | Docker 构建成功，四服务健康；容器入口真实 HTTP 冒烟 8/8 PASS | 已实现并验证 |
| 生产数据持久化 | SQLAlchemy 仓储、PostgreSQL、上传命名卷 | `test_persistent_runtime.py`；容器写入、重启、重读验证 | 已实现并验证 |
| 模型配置与异步恢复 | OpenAI 兼容适配器、后台运行、轮询/SSE | `test_openai_compatible_model.py`、`test_ai_run_api.py`、`planning.spec.ts` | 已实现并验证 |

延期范围（M8–M10）：真实招聘平台同步、学校统一身份认证、生产模型供应商运维配置、分布式任务队列、移动端原生应用、高级运营分析。
