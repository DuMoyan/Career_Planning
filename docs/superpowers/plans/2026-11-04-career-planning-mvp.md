# AI智能体大学生职业生涯规划系统 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个可通过 Docker Compose 部署、可在无大模型密钥时完整演示的大学生职业生涯规划全栈 MVP。

**Architecture:** 前端使用 Vue 3 单页应用，后端使用 FastAPI 分层架构，PostgreSQL 保存业务数据，Redis 保存限流和 AI 运行短期状态。核心业务规则实现为与 HTTP 和模型供应商解耦的领域服务；LangGraph 负责规划工作流，规则模板是强制降级路径。

**Tech Stack:** Vue 3.4+、Vite 5、TypeScript、Vue Router 4、Pinia、Element Plus、Axios、ECharts 5、Vitest；Python 3.11、FastAPI、Pydantic v2、SQLAlchemy 2.0 AsyncSession、Alembic、LangChain/LangGraph、PostgreSQL 14、Redis 7、pytest；Docker Compose、Nginx。

**Spec:** `docs/superpowers/specs/2026-11-04-career-planning-mvp-design.md`

## Global Constraints

- 后端运行于 Python 3.11；前端使用 Vue 3.4+ 与 Vite 5。
- 持久化使用 PostgreSQL 14，缓存与短期运行状态使用 Redis 7。
- 后端依赖方向固定为 `APIRouter -> Service -> Domain/Agent -> Repository/Model`；业务规则不得写入路由。
- 所有资源访问必须在服务端执行角色、数据归属和有效授权校验。
- 兴趣、价值观、行为倾向和能力分别存储与展示，不计算单一“职业适配总分”。
- AI 或规则输出只能创建草稿，未经学生确认不得激活计划或批量创建任务。
- 缺失能力证据的 Gap 状态为 `unknown`，不得按 0 分或“不适合”处理。
- 量表、计分规则、解释规则、计划、画像和 AI 输入快照必须版本化。
- 演示量表为项目原创教学题库：RIASEC 36 题；职业价值观 21 题；统一 1–5 级选项；MVP 无反向题。
- 单个简历文件最大 10 MB，仅允许 PDF、DOCX、TXT；解析草稿必须经学生确认才成为能力证据。
- 模型密钥缺失、超时、限流或 Schema 失败时必须使用确定性规则模板降级。
- 密码、令牌、完整答卷、简历原文和模型密钥不得写入普通日志。
- 每个生产函数或方法先有失败测试，再写最小实现；每个任务结束运行相关测试和全量测试。

## Review Focus

1. 同一幂等键的并发请求：计划激活与任务打卡最终只能各写入一次；Task 8 和 Task 9 必须覆盖 50 并发调用。
2. 撤回或过期导师授权：缓存存在时仍必须立即拒绝后续读取；Task 3 必须覆盖缓存失效和 403。
3. 不完整、损坏或伪造类型的简历文件：不得生成半写入证据或泄露解析堆栈；Task 5 必须覆盖 MIME/扩展名不一致和解析异常。
4. AI 流式连接中断、模型超时或返回非法结构：运行必须可查询并降级为有效草稿；Task 7 必须覆盖三种故障。
5. 跨时区和周边界打卡：自然周汇总以配置时区 `Asia/Shanghai` 为准且不重复统计；Task 10 必须覆盖周日到周一边界。

---

## File Structure

### Root and infrastructure

- `README.md`：开发、测试、部署、演示流程。
- `.env.example`：数据库、Redis、JWT、模型与文件存储配置。
- `compose.yaml`：frontend、backend、postgres、redis 四服务。
- `infra/nginx/default.conf`：静态资源、API 与 SSE 反向代理。
- `scripts/smoke.ps1`：Windows 下的部署后冒烟检查。

### Backend

- `backend/pyproject.toml`：运行、测试、格式化和覆盖率依赖。
- `backend/app/main.py`：FastAPI 应用工厂和路由装配。
- `backend/app/core/`：配置、数据库、Redis、安全、错误码、日志和依赖注入。
- `backend/app/api/v1/`：auth、profiles、consents、assessments、resumes、competencies、targets、plans、tasks、reports、mentor、admin 路由。
- `backend/app/domain/`：权限、测评计分、能力画像、Gap、计划、任务和周报纯业务规则。
- `backend/app/services/`：各用例的事务编排。
- `backend/app/agents/`：模型适配器、LangGraph 规划图、规则降级和输出校验。
- `backend/app/models/`：SQLAlchemy 模型。
- `backend/app/repositories/`：Repository Protocol 与 SQLAlchemy 实现。
- `backend/app/schemas/`：Pydantic 请求、响应和 Agent DTO。
- `backend/alembic/`：迁移环境和版本脚本。
- `backend/seed/`：演示用户、量表、能力字典和岗位种子数据。
- `backend/tests/unit/`：领域和服务单元测试。
- `backend/tests/integration/`：数据库、权限、事务、并发与 API 测试。

### Frontend

- `frontend/src/app/`：应用入口、路由、Pinia 和 HTTP/SSE 客户端。
- `frontend/src/layouts/`：学生、导师、管理员布局。
- `frontend/src/features/auth/`：登录和会话。
- `frontend/src/features/profile/`：档案、隐私和授权。
- `frontend/src/features/assessment/`：量表、答题和报告。
- `frontend/src/features/competency/`：简历、证据和画像。
- `frontend/src/features/targets/`：岗位检索、目标选择和 Gap 比较。
- `frontend/src/features/planning/`：规划生成、SSE、草稿和版本。
- `frontend/src/features/tasks/`：任务看板和打卡。
- `frontend/src/features/reports/`：周报和建议反馈。
- `frontend/src/features/mentor/`：授权学生和计划批注。
- `frontend/src/features/admin/`：岗位、量表和审计只读视图。
- `frontend/src/shared/`：通用组件、类型、格式化和错误状态。
- `frontend/src/**/*.spec.ts`：组件、Store 和路由测试。

---

### Task 1: Workspace, application factories, and health checks

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/api/v1/router.py`
- Create: `backend/app/api/v1/health.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/unit/test_config.py`
- Create: `backend/tests/integration/test_health.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/App.spec.ts`

**Interfaces:**
- Produces: `Settings` from `app.core.config`; `create_app(settings: Settings | None = None) -> FastAPI`; `GET /api/v1/health -> {"status":"ok"}`.

- [ ] **Step 1: Create project manifests and install development dependencies**

Declare the exact libraries named in the Tech Stack plus pytest/pytest-asyncio/httpx/testcontainers/coverage for backend tests and Vitest/Vue Test Utils/jsdom for frontend tests.

Run: `cd backend; python -m pip install -e ".[dev]"`

Run: `cd frontend; pnpm install`

Expected: both dependency installations exit 0 and lockfiles are created.

- [ ] **Step 2: Write failing backend configuration and health tests**

```python
def test_settings_rejects_missing_jwt_secret(monkeypatch): ...
def test_health_returns_ok(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}
```

- [ ] **Step 3: Run the backend tests and verify RED**

Run: `cd backend; pytest tests/unit/test_config.py tests/integration/test_health.py -v`
Expected: FAIL because `app.core.config` and `create_app` do not exist.

- [ ] **Step 4: Implement the backend factory and typed settings**

Implement `Settings` with database URL, Redis URL, JWT secret, timezone `Asia/Shanghai`, upload limit `10_485_760`, optional model settings, and `create_app()` with `/api/v1/health`.

- [ ] **Step 5: Run backend tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_config.py tests/integration/test_health.py -v`
Expected: PASS.

- [ ] **Step 6: Write the failing Vue application smoke test**

```ts
it('renders the application title', () => {
  expect(mount(App).text()).toContain('AI智能体大学生职业生涯规划系统')
})
```

- [ ] **Step 7: Run the frontend test and verify RED**

Run: `cd frontend; pnpm test --run src/App.spec.ts`
Expected: FAIL because the Vue application is not configured.

- [ ] **Step 8: Implement the minimal Vue application shell**

Create the Vite/Vue/TypeScript entry point and render the exact application title.

- [ ] **Step 9: Run frontend tests and build**

Run: `cd frontend; pnpm test --run; pnpm build`
Expected: tests PASS and Vite build exits 0.

- [ ] **Step 10: Initialize version control and commit**

```powershell
git init
git add .gitignore .env.example backend frontend
git commit -m "构建：初始化职业生涯规划MVP工程"
```

### Task 2: Database foundation, authentication, RBAC, and audit logging

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/redis.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/errors.py`
- Create: `backend/app/domain/access.py`
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/audit.py`
- Create: `backend/app/repositories/users.py`
- Create: `backend/app/repositories/audits.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_users_and_audits.py`
- Create: `backend/tests/unit/test_security.py`
- Create: `backend/tests/unit/test_access.py`
- Create: `backend/tests/integration/test_auth_api.py`

**Interfaces:**
- Consumes: `Settings`, `create_app` from Task 1.
- Produces: `Role = student|mentor|admin`; `AccessContext(user_id: UUID, role: Role)`; `hash_password()`, `verify_password()`, `create_access_token()`; `AuthService.login(identifier: str, password: str) -> TokenPair`; `require_role(*roles)` dependency; `AuditRepository.append(event: AuditEvent) -> None`.

- [ ] **Step 1: Write failing password, expired-token, and role tests**

Test that hashes differ from plaintext, valid password verifies, expired JWT is rejected, and `student` cannot satisfy `require_role(Role.admin)`.

- [ ] **Step 2: Run unit tests and verify RED**

Run: `cd backend; pytest tests/unit/test_security.py tests/unit/test_access.py -v`
Expected: FAIL on missing security and access modules.

- [ ] **Step 3: Implement security primitives and access context**

Use Argon2 or bcrypt, short-lived access tokens, rotating refresh token records, and role enum values exactly as specified.

- [ ] **Step 4: Run unit tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_security.py tests/unit/test_access.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing authentication API tests**

Cover valid login, generic invalid-credential response, disabled account, five consecutive failures causing temporary lock, refresh rotation, logout revocation, and an audit row for successful login.

- [ ] **Step 6: Run authentication API tests and verify RED**

Run: `cd backend; pytest tests/integration/test_auth_api.py -v`
Expected: FAIL because models, migrations, service, and routes are missing.

- [ ] **Step 7: Implement user models, repositories, migrations, service, and routes**

Expose `POST /api/v1/auth/login`, `/refresh`, `/logout`; never reveal whether an identifier exists.

- [ ] **Step 8: Run migrations and the full backend suite**

Run: `cd backend; alembic upgrade head; pytest -v`
Expected: migration succeeds and all tests PASS.

- [ ] **Step 9: Commit authentication and authorization**

```powershell
git add backend
git commit -m "功能：新增身份认证、权限控制与审计基础"
```

### Task 3: Student profiles, privacy consents, and mentor grants

**Files:**
- Create: `backend/app/models/profile.py`
- Create: `backend/app/models/consent.py`
- Create: `backend/app/models/mentor.py`
- Create: `backend/app/schemas/profile.py`
- Create: `backend/app/schemas/consent.py`
- Create: `backend/app/repositories/profiles.py`
- Create: `backend/app/repositories/grants.py`
- Create: `backend/app/services/profiles.py`
- Create: `backend/app/services/grants.py`
- Create: `backend/app/api/v1/profiles.py`
- Create: `backend/app/api/v1/consents.py`
- Create: `backend/alembic/versions/0002_profiles_consents_grants.py`
- Create: `backend/tests/unit/test_grant_policy.py`
- Create: `backend/tests/integration/test_profile_and_grants_api.py`

**Interfaces:**
- Consumes: `AccessContext`, audit append from Task 2.
- Produces: `ProfileService.get/update_own_profile`; `GrantScope = profile_summary|goals|plan_progress`; `GrantService.create(student_id, mentor_id, scopes, expires_at)`; `GrantService.revoke(grant_id, student_id)`; `GrantPolicy.can_read(mentor_id, student_id, scope, now) -> bool`.

- [ ] **Step 1: Write failing grant policy tests**

Assert active in-scope grants allow access; missing, revoked, expired, or out-of-scope grants deny access; raw assessment answers are never a valid scope.

- [ ] **Step 2: Run policy tests and verify RED**

Run: `cd backend; pytest tests/unit/test_grant_policy.py -v`
Expected: FAIL because `GrantPolicy` is missing.

- [ ] **Step 3: Implement the grant domain policy**

Keep it pure and accept `now` explicitly for deterministic expiry tests.

- [ ] **Step 4: Run policy tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_grant_policy.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing profile and grant API tests**

Cover own-profile CRUD, cross-student 403, default 90-day grant, explicit expiry, audit events, Redis authorization cache, and immediate denial after revoke despite a warmed cache.

- [ ] **Step 6: Run API tests and verify RED**

Run: `cd backend; pytest tests/integration/test_profile_and_grants_api.py -v`
Expected: FAIL on missing persistence and endpoints.

- [ ] **Step 7: Implement persistence, services, routes, and cache invalidation**

Expose `/profiles/me` and `/consents/mentor-grants`; enforce student ownership in queries, not only response filtering.

- [ ] **Step 8: Run migrations and backend suite**

Run: `cd backend; alembic upgrade head; pytest -v`
Expected: PASS.

- [ ] **Step 9: Commit profiles and grants**

```powershell
git add backend
git commit -m "功能：新增学生档案与导师授权控制"
```

### Task 4: Versioned assessments and self-exploration reports

**Files:**
- Create: `backend/app/domain/assessment.py`
- Create: `backend/app/models/assessment.py`
- Create: `backend/app/models/preference.py`
- Create: `backend/app/schemas/assessment.py`
- Create: `backend/app/repositories/assessments.py`
- Create: `backend/app/services/assessments.py`
- Create: `backend/app/api/v1/assessments.py`
- Create: `backend/alembic/versions/0003_assessments.py`
- Create: `backend/seed/assessments.json`
- Create: `backend/tests/unit/test_assessment_scoring.py`
- Create: `backend/tests/integration/test_assessment_api.py`

**Interfaces:**
- Consumes: profile ownership and audit infrastructure.
- Produces: `score_scale(scale: ScaleDefinition, answers: dict[UUID, int]) -> ScoreResult`; `AssessmentService.save_progress`, `submit(idempotency_key)`, `get_report`; `ScoreResult.dimension_scores` normalized to 0–100.

- [ ] **Step 1: Write failing scoring tests**

Use a small fixture to assert 1 maps to 0, 3 maps to 50, 5 maps to 100; incomplete answers raise `IncompleteAssessment`; identical answers and scale version yield identical scores.

- [ ] **Step 2: Run scoring tests and verify RED**

Run: `cd backend; pytest tests/unit/test_assessment_scoring.py -v`
Expected: FAIL because the scoring domain is missing.

- [ ] **Step 3: Implement versioned deterministic scoring**

Return every dimension, top-three relative preferences, scale version, scoring version, interpretation version, and the non-diagnostic disclaimer.

- [ ] **Step 4: Run scoring tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_assessment_scoring.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing assessment API tests**

Cover scale listing, 36/21 seed counts, progress resume, answer editing before submit, idempotent duplicate submission, history retention, private raw answers, and separate interest/value reports.

- [ ] **Step 6: Run API tests and verify RED**

Run: `cd backend; pytest tests/integration/test_assessment_api.py -v`
Expected: FAIL on missing models and routes.

- [ ] **Step 7: Implement models, seed data, repositories, service, and endpoints**

Expose scale list/detail, progress save, submit, records, reports, work-environment preferences, and reflection endpoints.

- [ ] **Step 8: Run seed validation and backend suite**

Run: `cd backend; pytest -v`
Expected: all tests PASS and seed validation confirms exactly 36 RIASEC and 21 value items.

- [ ] **Step 9: Commit assessments**

```powershell
git add backend
git commit -m "功能：新增版本化职业测评"
```

### Task 5: Resume parsing, competency evidence, and profile versions

**Files:**
- Create: `backend/app/core/files.py`
- Create: `backend/app/domain/competency.py`
- Create: `backend/app/services/resumes.py`
- Create: `backend/app/services/competencies.py`
- Create: `backend/app/models/resume.py`
- Create: `backend/app/models/competency.py`
- Create: `backend/app/schemas/competency.py`
- Create: `backend/app/repositories/competencies.py`
- Create: `backend/app/api/v1/resumes.py`
- Create: `backend/app/api/v1/competencies.py`
- Create: `backend/alembic/versions/0004_competencies.py`
- Create: `backend/seed/competencies.json`
- Create: `backend/tests/unit/test_competency_profile.py`
- Create: `backend/tests/integration/test_resume_api.py`

**Interfaces:**
- Produces: `FileStore.save/delete`; `ResumeParser.parse(path, media_type) -> ResumeDraft`; `calculate_profile(evidence: Sequence[ConfirmedEvidence]) -> CompetencyProfileSnapshot`; `CompetencyService.confirm_evidence`, `create_profile_version`.

- [ ] **Step 1: Write failing competency calculation tests**

Assert highest confirmed demonstrated level wins, unconfirmed/deleted evidence is ignored, evidence counts do not inflate levels, and profile snapshots retain source evidence IDs.

- [ ] **Step 2: Run domain tests and verify RED**

Run: `cd backend; pytest tests/unit/test_competency_profile.py -v`
Expected: FAIL because the competency domain is missing.

- [ ] **Step 3: Implement the deterministic competency profile calculation**

Use the controlled dictionary and levels 0–4; require an explicit “update profile” command to create a new immutable snapshot.

- [ ] **Step 4: Run domain tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_competency_profile.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing resume and evidence API tests**

Cover valid TXT/PDF/DOCX upload, 10 MB rejection, disallowed extension, MIME/extension mismatch, corrupt parser input, no evidence before confirmation, manual evidence, file deletion removing drafts but retaining confirmed evidence with deleted-source marker, and no partial writes on failure.

- [ ] **Step 6: Run API tests and verify RED**

Run: `cd backend; pytest tests/integration/test_resume_api.py -v`
Expected: FAIL on missing upload, parser, persistence, and routes.

- [ ] **Step 7: Implement local-volume FileStore and rule-based parsing**

Extract text, identify common sections and controlled competency keywords, and return editable candidates only; never assign a final evidence level without student confirmation.

- [ ] **Step 8: Implement evidence and profile version endpoints**

Expose resume upload/draft/delete, evidence CRUD/confirm, profile generation, current profile, and version comparison.

- [ ] **Step 9: Run migrations and backend suite**

Run: `cd backend; alembic upgrade head; pytest -v`
Expected: PASS.

- [ ] **Step 10: Commit competency functionality**

```powershell
git add backend
git commit -m "功能：新增简历证据与能力画像"
```

### Task 6: Target catalog, goal selection, and explainable Gap analysis

**Files:**
- Create: `backend/app/domain/gap.py`
- Create: `backend/app/models/target.py`
- Create: `backend/app/models/goal.py`
- Create: `backend/app/schemas/target.py`
- Create: `backend/app/repositories/targets.py`
- Create: `backend/app/services/targets.py`
- Create: `backend/app/api/v1/targets.py`
- Create: `backend/alembic/versions/0005_targets_and_goals.py`
- Create: `backend/seed/targets.json`
- Create: `backend/tests/unit/test_gap_analysis.py`
- Create: `backend/tests/integration/test_target_api.py`

**Interfaces:**
- Consumes: current `CompetencyProfileSnapshot`, preferences from Tasks 4–5.
- Produces: `GapStatus = met|developable_gap|unknown|hard_unmet`; `analyze_gap(requirements, profile) -> list[GapItem]`; `TargetService.compare(student_id, target_ids: list[UUID]) -> TargetComparison`; `GoalService.set_primary`.

- [ ] **Step 1: Write failing Gap classification tests**

Assert the exact precedence: no evidence -> unknown; current >= required -> met; insufficient hard requirement -> hard_unmet; insufficient non-hard requirement -> developable_gap. Assert each item contains requirement source and evidence references.

- [ ] **Step 2: Run Gap tests and verify RED**

Run: `cd backend; pytest tests/unit/test_gap_analysis.py -v`
Expected: FAIL because Gap types and algorithm are missing.

- [ ] **Step 3: Implement the pure Gap analysis domain**

Do not use interest or values to alter ability status; return them as separate comparison sections.

- [ ] **Step 4: Run Gap tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_gap_analysis.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing catalog and goal API tests**

Cover keyword/category search, source and verification dates, stale target marker, comparison requiring 2–3 targets, primary goal deadline required, one primary goal, and cross-student denial.

- [ ] **Step 6: Run API tests and verify RED**

Run: `cd backend; pytest tests/integration/test_target_api.py -v`
Expected: FAIL on missing models and endpoints.

- [ ] **Step 7: Implement target persistence, seeds, comparison, and goals**

Seed software development, data analysis, product manager, and algorithm engineer targets with controlled requirements and explicit sample-data sources.

- [ ] **Step 8: Run migrations and backend suite**

Run: `cd backend; alembic upgrade head; pytest -v`
Expected: PASS.

- [ ] **Step 9: Commit targets and Gap analysis**

```powershell
git add backend
git commit -m "功能：新增目标比较与差距分析"
```

### Task 7: Planning agent, structured output, SSE, and rule fallback

**Files:**
- Create: `backend/app/schemas/planning.py`
- Create: `backend/app/agents/model.py`
- Create: `backend/app/agents/fallback.py`
- Create: `backend/app/agents/validation.py`
- Create: `backend/app/agents/planning_graph.py`
- Create: `backend/app/models/ai_run.py`
- Create: `backend/app/repositories/ai_runs.py`
- Create: `backend/app/services/ai_runs.py`
- Create: `backend/app/api/v1/ai_runs.py`
- Create: `backend/alembic/versions/0006_ai_runs.py`
- Create: `backend/tests/unit/test_plan_fallback.py`
- Create: `backend/tests/unit/test_plan_validation.py`
- Create: `backend/tests/integration/test_ai_run_api.py`

**Interfaces:**
- Consumes: primary goal, target comparison, active profile, preferences, weekly hours.
- Produces: `PlanningContext`; `PlanDraft(milestones, tasks, sources, unknowns, risks, generation_mode)`; `ModelAdapter.generate(context) -> PlanDraft`; `build_fallback_plan(context) -> PlanDraft`; `validate_plan(draft, context) -> ValidationResult`; `PlanningGraph.run(context) -> PlanDraft`; AI run create/status/events endpoints.

- [ ] **Step 1: Write failing fallback plan tests**

Assert hard gaps precede developable gaps, unknowns create verification tasks, every milestone has acceptance criteria, total weekly hours never exceed the configured limit, and `generation_mode == "rules"`.

- [ ] **Step 2: Run fallback tests and verify RED**

Run: `cd backend; pytest tests/unit/test_plan_fallback.py -v`
Expected: FAIL because fallback generation is missing.

- [ ] **Step 3: Implement deterministic fallback generation**

Use only structured Gap items, deadline, weekly hours, and fixed task templates; make output stable for identical inputs.

- [ ] **Step 4: Run fallback tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_plan_fallback.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing plan validation tests**

Reject missing acceptance criteria, tasks beyond goal deadline, weekly overload, missing source/unknown markers, or prohibited diagnostic/guaranteed-outcome wording.

- [ ] **Step 6: Implement Pydantic plan schemas and validation**

Return field-level validation errors suitable for one model repair attempt and audit logging.

- [ ] **Step 7: Write failing AI run integration tests**

Cover missing key, model timeout, rate limit, invalid model JSON, one repair failure, SSE disconnect, status polling after disconnect, one running job per student returning 409, and retry creating a new immutable snapshot.

- [ ] **Step 8: Run AI integration tests and verify RED**

Run: `cd backend; pytest tests/integration/test_ai_run_api.py -v`
Expected: FAIL because graph, Redis state, persistence, and endpoints are missing.

- [ ] **Step 9: Implement the model adapter, planning graph, run service, and SSE endpoints**

Expose `POST /plans/generations`, `GET /plans/generations/{run_id}`, and `/events`; persist service/model/prompt versions, input references, validation result, sources, and confirmation status without full sensitive source text.

- [ ] **Step 10: Run backend suite**

Run: `cd backend; pytest -v`
Expected: PASS.

- [ ] **Step 11: Commit the planning agent**

```powershell
git add backend
git commit -m "功能：新增可降级的规划智能体工作流"
```

### Task 8: Plan activation, immutable versions, and replanning migration

**Files:**
- Create: `backend/app/domain/plans.py`
- Create: `backend/app/models/plan.py`
- Create: `backend/app/models/task.py`
- Create: `backend/app/repositories/tasks.py`
- Create: `backend/app/repositories/plans.py`
- Create: `backend/app/services/plans.py`
- Create: `backend/app/api/v1/plans.py`
- Create: `backend/alembic/versions/0007_plans.py`
- Create: `backend/tests/unit/test_plan_state.py`
- Create: `backend/tests/integration/test_plan_activation.py`

**Interfaces:**
- Consumes: valid `PlanDraft` and AI run from Task 7.
- Produces: `PlanStatus = draft|active|archived|discarded`; `PlanService.create_draft`, `activate(plan_version_id, idempotency_key)`, `create_replan`, `activate_replan(migrations)`; tasks carry `source_task_id` when continued.

- [ ] **Step 1: Write failing plan state tests**

Assert only draft can activate, one active version per career plan, archived versions are immutable, and regeneration never overwrites active data.

- [ ] **Step 2: Run state tests and verify RED**

Run: `cd backend; pytest tests/unit/test_plan_state.py -v`
Expected: FAIL because state rules are missing.

- [ ] **Step 3: Implement plan state transitions**

Keep transition validation in `domain/plans.py` and expose typed domain errors.

- [ ] **Step 4: Run state tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_plan_state.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing activation and replanning integration tests**

Cover transactional task creation, exactly one active version, old version archival, completed tasks retained only in history, continue/replace/cancel migration choices, `source_task_id`, and 50 concurrent activations with the same idempotency key producing one version/task set.

- [ ] **Step 6: Run integration tests and verify RED**

Run: `cd backend; pytest tests/integration/test_plan_activation.py -v`
Expected: FAIL on missing persistence and transaction service.

- [ ] **Step 7: Implement plan models, repositories, service transactions, and API**

Expose draft edit/discard, activate, history, version detail, replan preview, and replan activation endpoints.

- [ ] **Step 8: Run migrations and backend suite**

Run: `cd backend; alembic upgrade head; pytest -v`
Expected: PASS.

- [ ] **Step 9: Commit plan versioning**

```powershell
git add backend
git commit -m "功能：新增计划激活与版本化重规划"
```

### Task 9: Growth tasks, check-ins, and evidence links

**Files:**
- Create: `backend/app/domain/tasks.py`
- Modify: `backend/app/models/task.py`
- Create: `backend/app/schemas/task.py`
- Modify: `backend/app/repositories/tasks.py`
- Create: `backend/app/services/tasks.py`
- Create: `backend/app/api/v1/tasks.py`
- Create: `backend/alembic/versions/0008_tasks.py`
- Create: `backend/tests/unit/test_task_state.py`
- Create: `backend/tests/integration/test_task_checkin.py`

**Interfaces:**
- Consumes: active plan/version from Task 8.
- Produces: `TaskStatus = todo|in_progress|completed|delayed|abandoned`; `TaskService.transition`, `check_in(task_id, content, actual_hours, proof_url, idempotency_key)`.

- [ ] **Step 1: Write failing task transition tests**

Assert allowed transitions, delayed/abandoned reason requirement, archived-version tasks reject mutation, and completed tasks retain check-ins.

- [ ] **Step 2: Run state tests and verify RED**

Run: `cd backend; pytest tests/unit/test_task_state.py -v`
Expected: FAIL because task state rules are missing.

- [ ] **Step 3: Implement task state domain logic**

Use explicit transition maps and typed errors.

- [ ] **Step 4: Run task state tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_task_state.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing task API and concurrency tests**

Cover task list by week/status, start/complete, check-in content/hours/proof URL, ownership, no mutation on archived versions, and 50 same-key concurrent check-ins producing one row and one status change.

- [ ] **Step 6: Run integration tests and verify RED**

Run: `cd backend; pytest tests/integration/test_task_checkin.py -v`
Expected: FAIL on missing models and service.

- [ ] **Step 7: Implement task persistence, transaction service, and endpoints**

Expose active-plan task list, transition, and check-in endpoints; record all check-ins as append-only rows.

- [ ] **Step 8: Run migrations and backend suite**

Run: `cd backend; alembic upgrade head; pytest -v`
Expected: PASS.

- [ ] **Step 9: Commit task tracking**

```powershell
git add backend
git commit -m "功能：新增成长任务与幂等打卡"
```

### Task 10: Weekly aggregation, deviation rules, and adjustment feedback

**Files:**
- Create: `backend/app/domain/reports.py`
- Create: `backend/app/models/report.py`
- Create: `backend/app/schemas/report.py`
- Create: `backend/app/repositories/reports.py`
- Create: `backend/app/services/reports.py`
- Create: `backend/app/api/v1/reports.py`
- Create: `backend/alembic/versions/0009_weekly_reports.py`
- Create: `backend/tests/unit/test_weekly_aggregation.py`
- Create: `backend/tests/integration/test_weekly_report_api.py`

**Interfaces:**
- Consumes: tasks and check-ins from Task 9, planning runs from Task 7.
- Produces: `aggregate_week(tasks, checkins, week_start, timezone) -> WeeklyMetrics`; `ReportService.generate`; `respond_to_suggestion(report_id, action: accept|modify|reject, text)`.

- [ ] **Step 1: Write failing aggregation and deviation tests**

Assert completed count, completion rate, estimated/actual hours, zero-task week behavior, delayed-task prompt, and Asia/Shanghai Sunday 23:59 versus Monday 00:00 assignment.

- [ ] **Step 2: Run report domain tests and verify RED**

Run: `cd backend; pytest tests/unit/test_weekly_aggregation.py -v`
Expected: FAIL because report rules are missing.

- [ ] **Step 3: Implement deterministic weekly aggregation and deviation rules**

Use natural weeks Monday 00:00 through next Monday 00:00 in the configured timezone.

- [ ] **Step 4: Run report domain tests and verify GREEN**

Run: `cd backend; pytest tests/unit/test_weekly_aggregation.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing report API tests**

Cover idempotent report generation, optional AI advice with fallback, accept creating a replan run without changing active plan, modify preserving edited text, reject recording optional reason, and ownership.

- [ ] **Step 6: Run report API tests and verify RED**

Run: `cd backend; pytest tests/integration/test_weekly_report_api.py -v`
Expected: FAIL on missing persistence and workflow.

- [ ] **Step 7: Implement report persistence, service, and routes**

Expose report list/detail/generate and suggestion response endpoints; reuse Task 7 run creation for accept/modify.

- [ ] **Step 8: Run migrations and backend suite with coverage**

Run: `cd backend; alembic upgrade head; pytest --cov=app --cov-report=term-missing`
Expected: PASS and core domain/service coverage is at least 65%.

- [ ] **Step 9: Commit weekly reports**

```powershell
git add backend
git commit -m "功能：新增成长周报与进度复盘"
```

### Task 11: Frontend session, role layouts, profile, privacy, and assessments

**Files:**
- Create: `frontend/src/app/router.ts`
- Create: `frontend/src/app/http.ts`
- Create: `frontend/src/app/session.ts`
- Create: `frontend/src/layouts/StudentLayout.vue`
- Create: `frontend/src/layouts/MentorLayout.vue`
- Create: `frontend/src/layouts/AdminLayout.vue`
- Create: `frontend/src/features/auth/LoginPage.vue`
- Create: `frontend/src/features/auth/LoginPage.spec.ts`
- Create: `frontend/src/features/profile/DashboardPage.vue`
- Create: `frontend/src/features/profile/ProfilePage.vue`
- Create: `frontend/src/features/profile/PrivacyPage.vue`
- Create: `frontend/src/features/profile/profile.spec.ts`
- Create: `frontend/src/features/assessment/AssessmentCenterPage.vue`
- Create: `frontend/src/features/assessment/AssessmentRunnerPage.vue`
- Create: `frontend/src/features/assessment/AssessmentReportPage.vue`
- Create: `frontend/src/features/assessment/assessment.spec.ts`
- Create: `frontend/src/shared/AsyncState.vue`

**Interfaces:**
- Consumes: auth, profiles, grants, assessments APIs from Tasks 2–4.
- Produces: authenticated role-aware router; session store; reusable loading/empty/error/retry component; student dashboard, profile/privacy, assessment flow.

- [ ] **Step 1: Write failing login and role-route tests**

Assert login posts credentials, generic error display, token refresh once on 401, student cannot open admin route, and logout clears session.

- [ ] **Step 2: Run frontend tests and verify RED**

Run: `cd frontend; pnpm test --run src/features/auth/LoginPage.spec.ts`
Expected: FAIL because session and routes are missing.

- [ ] **Step 3: Implement HTTP client, session store, routes, and layouts**

Use route metadata for UX routing only; retain server enforcement as authority.

- [ ] **Step 4: Run auth tests and verify GREEN**

Run: `cd frontend; pnpm test --run src/features/auth/LoginPage.spec.ts`
Expected: PASS.

- [ ] **Step 5: Write failing profile/privacy and assessment component tests**

Cover profile save, weekly-hour validation, grant create/revoke, segmented answer progress, resume after reload, submit confirmation, separate interest/value charts, version/date/disclaimer, and network retry state.

- [ ] **Step 6: Run feature tests and verify RED**

Run: `cd frontend; pnpm test --run src/features/profile/profile.spec.ts src/features/assessment/assessment.spec.ts`
Expected: FAIL because pages are missing.

- [ ] **Step 7: Implement profile, privacy, dashboard, and assessment pages**

Use deep blue `#1E3A8A`, teal `#0D9488`, warm orange `#F59E0B`; never combine ability and preference charts.

- [ ] **Step 8: Run frontend suite and build**

Run: `cd frontend; pnpm test --run; pnpm build`
Expected: PASS and build exits 0.

- [ ] **Step 9: Commit the first student UI slice**

```powershell
git add frontend
git commit -m "功能：新增学生档案、隐私与测评界面"
```

### Task 12: Frontend competency, targets, planning, tasks, and reports

**Files:**
- Create: `frontend/src/features/competency/CompetencyPage.vue`
- Create: `frontend/src/features/competency/competency.spec.ts`
- Create: `frontend/src/features/targets/TargetExplorerPage.vue`
- Create: `frontend/src/features/targets/TargetComparePage.vue`
- Create: `frontend/src/features/targets/targets.spec.ts`
- Create: `frontend/src/features/planning/PlanningPage.vue`
- Create: `frontend/src/features/planning/PlanHistoryPage.vue`
- Create: `frontend/src/features/planning/planning.spec.ts`
- Create: `frontend/src/features/tasks/TaskBoardPage.vue`
- Create: `frontend/src/features/tasks/CheckinDialog.vue`
- Create: `frontend/src/features/tasks/tasks.spec.ts`
- Create: `frontend/src/features/reports/WeeklyReportsPage.vue`
- Create: `frontend/src/features/reports/reports.spec.ts`
- Create: `frontend/src/shared/charts/CompetencyChart.vue`
- Create: `frontend/src/shared/charts/PreferenceChart.vue`

**Interfaces:**
- Consumes: APIs from Tasks 5–10 and session/router from Task 11.
- Produces: complete student MVP workflow from resume upload through weekly adjustment response.

- [ ] **Step 1: Write failing competency and target tests**

Cover file type/size UI validation, editable parse draft, explicit evidence confirmation, update-profile action, profile version comparison, 2–3 target selection, separate preference/ability sections, and unknown Gap rendering.

- [ ] **Step 2: Run tests and verify RED**

Run: `cd frontend; pnpm test --run src/features/competency/competency.spec.ts src/features/targets/targets.spec.ts`
Expected: FAIL because pages are missing.

- [ ] **Step 3: Implement competency and target pages**

Show every profile/Gap item’s source; use distinct visuals for ability and preference.

- [ ] **Step 4: Run competency and target tests and verify GREEN**

Run: same command as Step 2.
Expected: PASS.

- [ ] **Step 5: Write failing planning tests**

Cover primary target/deadline requirement, SSE progress, stream disconnect followed by polling, rule-fallback badge, editable draft, source/unknown/risk display, activation confirmation, history, and replan migration choices.

- [ ] **Step 6: Implement planning pages and SSE client**

Do not create tasks until the explicit activation confirmation succeeds.

- [ ] **Step 7: Write failing task and weekly report tests**

Cover status transitions, three-step-or-fewer check-in flow, actual hours, delayed/abandoned reasons, empty states, weekly metrics, and accept/modify/reject behavior.

- [ ] **Step 8: Implement task and report pages**

Provide clear loading, empty, error and retry states for every async view.

- [ ] **Step 9: Run the full frontend suite and build**

Run: `cd frontend; pnpm test --run; pnpm build`
Expected: PASS and build exits 0.

- [ ] **Step 10: Commit the complete student workflow**

```powershell
git add frontend
git commit -m "功能：完成学生职业规划核心流程"
```

### Task 13: Minimal mentor and administrator validation interfaces

**Files:**
- Create: `backend/app/services/mentor.py`
- Create: `backend/app/services/admin.py`
- Create: `backend/app/api/v1/mentor.py`
- Create: `backend/app/api/v1/admin.py`
- Create: `backend/app/models/mentor_comment.py`
- Create: `backend/alembic/versions/0010_mentor_comments.py`
- Create: `backend/tests/integration/test_mentor_admin_api.py`
- Create: `frontend/src/features/mentor/MentorStudentsPage.vue`
- Create: `frontend/src/features/mentor/mentor.spec.ts`
- Create: `frontend/src/features/admin/AdminOverviewPage.vue`
- Create: `frontend/src/features/admin/admin.spec.ts`

**Interfaces:**
- Consumes: GrantPolicy, plan versions, target/scales/audit repositories.
- Produces: mentor authorized-student list and plan-version comments; admin read-only target, scale-version, and audit views.

- [ ] **Step 1: Write failing mentor/admin API tests**

Cover active-scope access, revoked/expired 403, no raw assessment/resume fields, comment attached to plan version and visible to student, admin-only audit access, and operator-like users not inheriting student data access.

- [ ] **Step 2: Run API tests and verify RED**

Run: `cd backend; pytest tests/integration/test_mentor_admin_api.py -v`
Expected: FAIL because services and routes are missing.

- [ ] **Step 3: Implement mentor/admin backend slices**

Keep admin operations read-only for MVP except existing seed/config workflows.

- [ ] **Step 4: Run backend suite**

Run: `cd backend; pytest -v`
Expected: PASS.

- [ ] **Step 5: Write failing mentor/admin page tests**

Assert authorized list and comment submission, revoked access error, target/scale/audit tabs, and role navigation isolation.

- [ ] **Step 6: Implement minimal mentor and admin pages**

Reuse role layouts and async state components from Task 11.

- [ ] **Step 7: Run frontend suite and build**

Run: `cd frontend; pnpm test --run; pnpm build`
Expected: PASS.

- [ ] **Step 8: Commit role validation interfaces**

```powershell
git add backend frontend
git commit -m "功能：新增导师与管理员验证界面"
```

### Task 14: Containers, seed command, end-to-end smoke test, and documentation

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `compose.yaml`
- Create: `infra/nginx/default.conf`
- Create: `backend/app/cli/seed.py`
- Create: `backend/tests/integration/test_seed_idempotency.py`
- Create: `scripts/smoke.ps1`
- Create: `README.md`
- Create: `docs/deployment.md`
- Create: `docs/demo-script.md`
- Create: `docs/requirements-traceability.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: repeatable four-service deployment, idempotent demo data, documented demo accounts, smoke script, and requirement/test traceability.

- [ ] **Step 1: Write the failing idempotent seed test**

Run seed twice and assert stable counts, unique identifiers, valid password hashes, exactly 36/21 assessment items, controlled competency codes, and four target records.

- [ ] **Step 2: Run seed test and verify RED**

Run: `cd backend; pytest tests/integration/test_seed_idempotency.py -v`
Expected: FAIL because the seed command is missing.

- [ ] **Step 3: Implement the idempotent seed command**

Create one student, mentor, and admin demo account; never include real personal information.

- [ ] **Step 4: Run seed test and backend suite**

Run: `cd backend; pytest -v`
Expected: PASS.

- [ ] **Step 5: Create Dockerfiles, Compose, Nginx, and environment sample**

Configure persistent PostgreSQL and upload volumes, Redis healthcheck, backend migration-before-start, frontend SPA fallback, and unbuffered SSE proxying.

- [ ] **Step 6: Build and start the clean deployment**

Run: `docker compose build; docker compose up -d; docker compose ps`
Expected: all four services become healthy.

- [ ] **Step 7: Write and run the end-to-end smoke script**

The script must log in as the demo student, read the profile, list both scales, compare two targets, generate a rule-mode plan without a model key, activate it, check in once, and fetch the weekly report.

Run: `powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1`
Expected: every step prints `PASS` and exits 0.

- [ ] **Step 8: Verify the frontend build and all automated tests fresh**

Run: `cd backend; pytest --cov=app --cov-report=term-missing`
Expected: PASS with core coverage at least 65%.

Run: `cd frontend; pnpm test --run; pnpm build`
Expected: PASS and build exits 0.

- [ ] **Step 9: Write deployment, demo, and traceability documentation**

Map each included design capability and acceptance scenario to its route, page, and test; explicitly list deferred M8–M10 features.

- [ ] **Step 10: Commit deployment and documentation**

```powershell
git add .
git commit -m "文档：新增部署与MVP验证流程"
```

### Task 15: Final requirements verification and release evidence

**Files:**
- Modify: `README.md`
- Modify: `docs/requirements-traceability.md`
- Create: `docs/test-report.md`

**Interfaces:**
- Consumes: complete system and all verification commands.
- Produces: release-ready verification evidence and explicit known limitations.

- [ ] **Step 1: Run backend formatting, static checks, migrations, and tests**

Run the commands declared in `backend/pyproject.toml`, followed by `alembic upgrade head` and the full pytest coverage command.
Expected: all commands exit 0; record exact counts and coverage.

- [ ] **Step 2: Run frontend formatting, type checks, tests, and production build**

Run the scripts declared in `frontend/package.json`.
Expected: all commands exit 0; record exact test and build results.

- [ ] **Step 3: Recreate containers from a clean project state and run smoke test**

Run: `docker compose down -v`, then build/up, seed, and `scripts/smoke.ps1`.
Expected: clean initialization and complete smoke flow PASS.

- [ ] **Step 4: Execute the two 50-concurrency consistency tests**

Run the exact Task 8 activation and Task 9 check-in test selectors with `-v`.
Expected: one activation/task set and one check-in row respectively, with no unhandled 5xx.

- [ ] **Step 5: Review every design section against the traceability matrix**

Mark each MVP requirement implemented and tested or list it as an explicit limitation; no blank status is allowed.

- [ ] **Step 6: Write the test report**

Include environment, commands, test counts, coverage, smoke output summary, concurrency results, known limitations, and deferred scope.

- [ ] **Step 7: Commit release evidence**

```powershell
git add README.md docs/requirements-traceability.md docs/test-report.md
git commit -m "测试：记录MVP发布验证结果"
```

