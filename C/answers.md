# Xero 集成评审

假设这是一个服务端 OAuth 2.0 集成，使用 Accounting API。每个内部租户都显式绑定一个已授权的 Xero connection；后台任务不会直接信任任务载荷里的 tenant ID，而是先查询该映射。

## C1 — 连接验证

1. 必要时刷新已保存的 Token；刷新失败则将连接标记为 `reauthorisation_required`，要求客户重新授权。
2. 用 access token 调用 `GET /connections`。成功响应说明 Token 可访问 Xero，并返回当前已连接的 tenant 列表。
3. 校验选定 `tenantId` 在该列表中，且等于内部组织保存的 tenant ID，避免后台任务读取其他客户的组织数据。
4. 携带 `Authorization: Bearer …` 和 `xero-tenant-id`，发起最小只读 Accounting API 请求，例如读取一页发票。返回 200 才能同时证明 Token、scope、tenant 请求头和会计权限都可用。日志仅记录 ID 与状态码。

## C2 — 故障诊断

- **401：** access token 过期时只刷新一次；刷新失败或新 Token 仍被拒绝，则标记连接断开并要求重新授权。错误 client secret 或已撤销 Token 不可无限重试。
- **403：** Token 有效但授权用户缺少会计 scope 或组织权限，也可能是应用申请了错误 scope。需要核对已授予 scope、授权用户与接口所需权限，再引导修复或重新授权。
- **404：** 先检查环境 base URL 与资源 ID。若 `/connections` 中不存在保存的 tenant ID，按连接已断开处理；若连接仍在，则检查接口是否可在当前 API/环境使用，不能静默当作“没有发票”。

## C3 — 可恢复的增量同步

每个内部组织保存独立同步记录：connection ID、Xero tenant ID、`last_successful_modified_at`、重叠时间窗、当前页/游标、run ID 和状态。同步从 `last_successful_modified_at - 5 minutes` 开始，按确定顺序分页读取，并在数据库事务中以 `(internal_tenant_id, xero_invoice_id)` 为唯一键 upsert 发票。

重叠时间窗可降低边界时刻写入、分页中断的风险；唯一键使重放不会重复插入。只有所有分页都持久化成功后，才推进 high-water mark。某页失败则保留原游标/high-water mark，让队列重试同一任务。下一次可能再次读到旧数据，但会变成更新而非重复插入。优先使用 Xero 分页和 `If-Modified-Since`，仍保留重叠窗口作为防御。

## C4 — 限流

收到 429 时，优先严格遵守 `Retry-After`；之后使用带 full jitter 的指数退避重新调度该租户任务。每个租户最多 5 个进行中的请求，持续出现 429 时继续降低并发。重试次数有预算，耗尽后将任务标记为“可重试/需要关注”，而非无限空转。

只对超时、连接重置、429 和部分 5xx 重试，且仅在操作可安全重放时执行。参数校验失败的 400、错误请求、未支持接口，以及权限未变更前的 401/403 都不应重试。记录剩余限额请求头，在触线前主动降低后台同步速率。

## C5 — 数据完整性

创建发票使用稳定的本地 operation ID，并作为 Xero 的 `Idempotency-Key`。完全相同的 method、URL 和 body 重试时安全。发生响应丢失或超时时，重试前要通过保存的 Xero invoice ID，或唯一的内部 reference 查询核对；获得远端 ID 后，在事务中写入本地与 Xero 的映射。定时对账任务报告远端/本地不一致，交由人工修复，而不是盲目创建第二张发票。

## C6 — 可观测性与安全

每个请求生成并携带 `run_id`、`job_id`、内部 tenant ID、connection ID（不包含 Token）、operation ID；Xero 返回时还记录 correlation ID。日志记录接口、状态码、重试次数、耗时、页码、游标范围和脱敏后的资源 ID。指标包括同步延迟、成功/失败记录数、重试/429 次数、Token 刷新失败、队列深度、单租户并发和对账差异；对持续同步延迟、鉴权失败、重试耗尽、异常 4xx/5xx 建告警。

不得记录 access/refresh token、client secret、`Authorization` 请求头、完整发票内容、客户 PII 或未脱敏错误响应。Token 通过 KMS/信封加密保存，按租户隔离，仅由后台 worker 身份读取；客户断开连接时及时撤销/删除。密钥来自 Secrets Manager，不能写入源代码或输出到环境变量日志。

