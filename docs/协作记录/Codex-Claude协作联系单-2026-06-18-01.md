# Codex-Claude协作联系单-2026-06-18-01

日期：2026-06-18 | 版本：01 | 阶段：体验版优化与收口

## 0. 当前唯一协作依据说明

本文件是 2026-06-18 当前唯一协作依据。
Codex / Claude Code 每次开始本项目工作前，优先读取本文件。
旧联系单仅作为历史归档，不再作为当前状态依据。
如其他说明文件与本文件冲突，以本文件为准。

**每日开工前检查与自动交接规则**

每次 Codex 或 Claude Code 开始本项目工作前，第一步不是直接改代码，而是先检查当前日期和当前联系单是否已经准备好：

1. 获取当前日期。
2. 检查 `docs/协作记录/` 下是否存在当天主联系单，例如 `Codex-Claude协作联系单-YYYY-MM-DD-01.md`。
3. 如果当天联系单存在，必须先读取该文件，并以它作为当前唯一协作依据。
4. 如果当天联系单不存在，必须先进入“新日期交接初始化流程”，不要直接开始开发。
5. 检查今日任务看板中是否有自己负责的任务；任务不明确时，先更新任务看板或请求用户确认。
6. 完成以上准备后，才可以开始修改代码。

**新日期交接初始化流程**

如果检测到今天还没有当天联系单：

1. 从 `docs/协作记录/` 中找到日期最近的一份联系单；同一天多版本时选择编号最大的版本。
2. 从上一份联系单自动提炼昨日交接摘要，不要求上一份文件必须存在固定收尾摘要标题。
3. 提炼内容包括：稳定配置、昨日已完成、未完成事项、P0/P1/P2 任务、用户确认项、Codex 事项、Claude Code 事项、最近重要变更和今日风险。
4. 创建当天 `Codex-Claude协作联系单-YYYY-MM-DD-01.md`，只继承稳定配置、交接摘要、未完成任务、今日优先级、用户确认事项、协作规则和今日任务看板。
5. 在上一份联系单底部追加“已交接到新联系单”记录，之后不再向旧文件追加当前工作内容。

**当天多次修改规则**

同一天不要频繁新建联系单。当天普通改动全部追加到当天 `-01` 文件内部，变更编号使用：

```text
YYYY-MM-DD-001
YYYY-MM-DD-002
YYYY-MM-DD-003
```

只有在当前联系单过长、阶段重大切换、上下文再次混乱，或用户明确要求新建下一版时，才创建同一天 `-02`、`-03`。

**收尾规则**

今日收尾备注可选；如果当天没有填写，第二天 AI 开工前应根据当天联系单内容自动提炼交接摘要。

**不要维护多套规则**

当前项目仍然以“每日联系单”为唯一协作依据。若存在 `AGENTS.md`、`CLAUDE.md`、`CURRENT.md` 等文件，只允许保留极简提示：

```text
本项目当前协作规则、路径、任务、分工，全部以 docs/协作记录/ 下最新日期版本联系单为准。如本文件与联系单冲突，以联系单为准。
```

具体规则、任务、路径、端口、数据库、分工、状态，全部写在当天联系单里。

## 1. 今日开工交接摘要

来源：
上一份联系单：`docs/协作记录/archive/Codex-Claude协作联系单-历史归档-2026-06-05至2026-06-17.md` 与本文件今日前序记录

继承时间：
2026-06-18 11:47

昨日已完成：
- 旧联系单已归档，当前主联系单切换到 `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`。
- 本地开发配置统一到 `8001 + tuoban_dev.db`。
- 老师/家长微信登录与免重复输入策略已完成基础实现。
- 通知、餐食、收费、设置、系统管理、学生管理等高风险表单弹窗已做体验版布局收口。

当前稳定配置：
- 项目根目录：`E:\projects\托班智慧管理系统开发`
- 本地端口：`http://127.0.0.1:8001` / `http://192.168.1.8:8001`
- 本地数据库：SQLite `backend/tuoban_dev.db`，`.env` 中 `DATABASE_URL=sqlite:///./tuoban_dev.db`
- 体验版 API：`https://ccrong.cloud/api`
- 当前运行环境：本地后端固定 8001；体验版继续连接云端 API

仍未完成：
- 生产 API 持续可用性与云端是否已部署最新代码仍需确认。
- 微信公众平台合法域名仍需用户确认。
- 真实微信 AppSecret 与关闭 mock 登录需正式上线前确认。
- 照片标签仍存本地，需要持久化。
- 餐食记录照片提交前即上传，可能产生孤立照片。
- 真机小屏视觉验收和 navigateTo 堆栈风险仍需 Claude Code 继续处理。

今日优先级：
1. P0：确认体验版云端 API 与部署状态。
2. P0：确认微信公众平台合法域名。
3. P1：修复餐食记录孤立照片问题。
4. P1：实现照片标签持久化。
5. P1/P2：继续真机体验版验收和页面细节收口。

需要用户确认：
- 微信公众平台 request/uploadFile/downloadFile 合法域名是否包含 `https://ccrong.cloud`。
- 是否提供正式隐私政策/用户协议链接，替换 `tuoban.example.com`。
- 是否提供真实微信 AppID/AppSecret 并关闭 `WECHAT_MOCK_LOGIN`。
- 是否处理根目录 `project.config.json` 可能误开项目的问题。

需要 Codex 处理：
- 生产 API 健康检查和部署状态确认。
- 餐食记录孤立照片问题。
- 照片标签持久化。
- 必要的后端接口、数据和配置收口。

需要 Claude Code 处理：
- 体验版逐页验收与真机小屏检查。
- 作业创建/批改页面视觉验收。
- navigateTo 堆栈上限风险。
- 前端加载态、空状态、错误处理继续收口。

## 2. 当前项目状态

已完成：
- 后端 15 个路由模块已注册。
- 4.3 接口清单 32 个接口已验证：32/32 已实现，0 缺失。
- 本地开发配置固定 `8001 + tuoban_dev.db`。
- 体验版前端配置保持 `https://ccrong.cloud/api`。
- 老师端核心流程、家长端只读流程、通知/餐食/收费/设置/系统管理等基础体验已具备体验版可测条件。

当前重点：
- 不扩展大功能，优先体验版稳定、顺手、看得懂。
- 继续处理 P0/P1：云端可用性、合法域名、照片与餐食相关数据一致性。
- 所有新增工作先进入任务看板，再执行代码修改。

当前风险：
- 体验版若要测试最新功能，必须确认云服务器后端已经部署本地最新代码并重启。
- 家长端餐食当前调用公开 `GET /meals`，可用但未按学生隔离。
- 根目录 `project.config.json` 可能导致误打开项目。

## 3. 今日任务看板

状态只允许使用：待处理 / 处理中 / 已完成 / 阻塞 / 需用户确认 / 暂缓

| ID | 任务 | 优先级 | 负责人 | 状态 | 需要对方处理 | 备注 |
|----|------|--------|--------|------|--------------|------|
| T-001 | 生产 API 持续可用性验证 | P0 | Codex | 阻塞 | Hermes 完整部署并重启云端后端 | `/api/health`、家长 mock session、家长首页接口可用；但 `/api/auth/login-policy`、`/api/auth/teacher/wechat-login` 仍 404，尚不能确认最新后端已完整部署并重启 |
| T-002 | 微信公众平台合法域名确认 | P0 | 用户 | 需用户确认 | Codex 记录结果 | request/uploadFile/downloadFile 需包含 `https://ccrong.cloud` |
| T-003 | 4.3 接口清单验证 | P1 | Codex | 已完成 | 无 | 32/32 已实现 |
| T-004 | 餐食记录照片提交前上传导致孤立照片 | P1 | Codex | 已完成 | Claude Code 真机复测餐食表单 | 已改为提交餐食时上传，保存失败时回滚已上传照片 |
| T-005 | 照片标签持久化 | P1 | Codex | 已完成 | Claude Code 真机复测照片库标签 | 已改为 `PUT /photos/{id}` 持久化到 `photo_type` |
| T-006 | 微信登录 mock 切真实 AppSecret | P1 | Codex/用户 | 需用户确认 | 用户提供 AppID/AppSecret | 正式上线前处理 |
| T-007 | 根目录 `project.config.json` 误开风险 | P1 | 用户/Claude Code | 需用户确认 | Codex 可记录建议 | 当前应打开 `miniprogram/` |
| T-008 | 作业创建/批改页面真机小屏视觉验收 | P2 | Claude Code | 待处理 | 用户提供截图反馈 | 体验版验收 |
| T-009 | navigateTo 堆栈上限风险 | P2 | Claude Code | 待处理 | 无 | 前端导航体验收口 |
| T-010 | 隐私政策/用户协议链接占位 | P2 | 用户 | 需用户确认 | Claude Code 替换链接 | 当前可能仍指向 `tuoban.example.com` |

## 4. 今日变更记录

### 2026-06-18-001：通知 Codex 联系单策略已变更

完成内容：
- 旧联系单归档。
- 当前协作主文件切换为本文件。
- 要求 Codex 验证 4.3 接口清单。

修改文件：
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`

验证结果：
- Codex 已读取并执行。

需要 Codex 处理：
- 接口清单验证。

需要 Claude Code 处理：
- 继续前端体验版验收。

需要用户确认：
- 无。

### 2026-06-18-002：Codex 接口清单验证结果

完成内容：
- 4.3 接口清单 32 个接口全部核对。
- OpenAPI / 路由注册 32/32 已实现。
- 17 个只读/安全接口已在本地 8001 实测通过。

修改文件：
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`

验证结果：
- 缺失接口 0。
- 需后端补接口 0。

需要 Codex 处理：
- 照片标签持久化。
- 餐食记录孤立照片问题。

需要 Claude Code 处理：
- 家长端餐食展示是否继续使用 `/meals` 的产品确认与前端体验验收。

需要用户确认：
- 是否需要按学生隔离餐食展示。

### 2026-06-18-003：Claude Code 确认接口验证结果

完成内容：
- Claude Code 确认 32 个接口均已实现。
- 同步更新待处理问题、接口清单和 Codex 负责事项。

修改文件：
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`

验证结果：
- 无阻塞性接口问题。

需要 Codex 处理：
- 剩余 P1 后端数据一致性任务。

需要 Claude Code 处理：
- 前端体验打磨和真机验收。

需要用户确认：
- 无。

### 2026-06-18-004：每日开工前检查与自动交接规则

完成内容：
- 将旧收尾交接思路调整为“每日开工前检查与自动交接”。
- 明确每次开工前必须检查日期、当天联系单、任务看板。
- 明确新日期无联系单时自动从最近联系单提炼摘要并创建当天 `-01` 文件。
- 明确今日收尾备注可选，第二天由 AI 自动提炼交接摘要。
- 补齐本文件固定结构：0 当前唯一协作依据说明、1 今日开工交接摘要、2 当前项目状态、3 今日任务看板、4 今日变更记录、5 今日收尾备注。

修改文件：
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`

验证结果：
- 已检查标题和关键规则，固定结构已补齐。

需要 Codex 处理：
- 后续每次修改代码前先执行开工前检查。

需要 Claude Code 处理：
- 后续每次修改前同样先执行开工前检查。

需要用户确认：
- 无。

### 2026-06-18-005：处理 P0/P1 优先项

完成内容：
- 验证体验版云端 API：`GET https://ccrong.cloud/api/health` 返回 200，生产环境、PostgreSQL、上传目录正常。
- 发现云端后端尚未部署完整最新代码：`/api/photos/batch`、`/api/admin/teachers` 已存在，但 `/api/auth/login-policy`、`/api/auth/teacher/wechat-login` 仍返回 404。
- 微信公众平台合法域名无法从代码仓库自动读取，保持为用户确认项：request/uploadFile/downloadFile 均需包含 `https://ccrong.cloud`。
- 修复餐食记录孤立照片问题：选图时只保留本地临时路径，提交餐食时才上传；如果保存失败，会尝试用 `/photos/batch` 删除本次已上传照片。
- 实现照片标签持久化：照片库“修改标签”不再写入 `wx.getStorageSync('photolib_tags')`，改为调用 `PUT /photos/{id}` 保存 `photo_type`，其他设备刷新后可同步显示。

修改文件：
- `miniprogram/pages/teacher/meal/meal.js`
- `miniprogram/pages/teacher/photolib/photolib.js`
- `miniprogram/pages/teacher/photolib/photolib.wxml`
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`

验证结果：
- `node --check miniprogram/pages/teacher/meal/meal.js` 通过。
- `node --check miniprogram/pages/teacher/photolib/photolib.js` 通过。
- 扫描无 `photolib_tags`、`_getLocalTags`、`_saveLocalTags` 残留。
- 本地 `PUT http://127.0.0.1:8001/api/photos/{id}` 实测 200，`photo_type` 可保存并恢复。
- `git diff --check` 对本轮修改文件通过，仅有 Git 换行符提示。

需要 Codex 处理：
- 云端部署最新代码后复测 `/api/auth/login-policy`、`/api/auth/teacher/wechat-login`。

需要 Claude Code 处理：
- 真机复测老师端餐食记录：选图后取消不应在照片库新增孤立照片；保存成功后照片应挂到餐食记录。
- 真机复测老师端照片库：修改标签后刷新、换设备登录应看到同一标签。

需要用户确认：
- 微信公众平台合法域名是否已配置 `https://ccrong.cloud`。
- 是否已让 Hermes/云服务器部署本地最新后端代码并重启。

### 2026-06-18-006：上传最新联系单并清理旧根目录交接文件

完成内容：
- 确认 GitHub/Hermes 当前看不到 `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`，原因是 `.gitignore` 原先全局忽略 `Codex-Claude协作联系单-*.md`。
- 调整 `.gitignore`，保留根目录联系单忽略规则，但放行 `docs/协作记录/` 下的当前联系单和归档联系单。
- 删除根目录旧联系单 `Codex-Claude协作联系单-2026-06-09.md`。
- 删除根目录旧 Hermes 交接单 `Hermes部署交接-2026-06-09.md`。
- 准备将当前主联系单与历史归档推送到 GitHub，供 Hermes 拉取。

修改文件：
- `.gitignore`
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`
- `docs/协作记录/archive/Codex-Claude协作联系单-历史归档-2026-06-05至2026-06-17.md`
- `Codex-Claude协作联系单-2026-06-09.md`（删除）
- `Hermes部署交接-2026-06-09.md`（删除）

验证结果：
- 待提交并推送后确认远程可见。

需要 Codex 处理：
- 提交并推送到 GitHub。

需要 Claude Code 处理：
- 推送后从 GitHub 拉取并读取当前联系单。

需要用户确认：
- 暂无。

### 2026-06-18-007：GitHub 推送失败原因排查与解决

完成内容：
- 排查 `git push origin main` 连续失败原因。
- 确认本地提交 `062e62e docs: sync collaboration contact sheet` 已生成，`main` 曾处于 `ahead 1` 状态。
- 确认远程地址正确：`https://github.com/kodo11shy/kodo.git`。
- 确认仓库本地配置没有代理或远程地址异常。
- DNS 可解析 `github.com`，但第一次 `Test-NetConnection github.com -Port 443` 显示 ping 通、TCP 443 不通。
- 随后 `curl.exe -I https://github.com`、`git ls-remote origin HEAD`、`Test-NetConnection ssh.github.com -Port 443` 均恢复正常，判断为本机到 GitHub HTTPS 链路临时抖动/连接重置，不是提交、权限或仓库配置问题。
- 趁链路恢复重新执行 `git push origin main`，已成功推送到 GitHub：`97ebba5..062e62e main -> main`。

修改文件：
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`

验证结果：
- `git push origin main` 已成功。
- GitHub 远程 main 已包含最新联系单提交 `062e62e`。
- Hermes 可执行 `git pull origin main` 后读取 `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`。

需要 Codex 处理：
- 将本条记录补充提交并推送。

需要 Claude Code 处理：
- 拉取后读取当前联系单。

需要用户确认：
- 如后续再次遇到 GitHub 443 连接重置，可先检查本机网络/代理/VPN，再重试 `git push origin main`。

### 2026-06-18-008：家长端体验闭环检查

完成内容：
- 确认 GPT 给出的方案总体符合当前体验版目标：真实微信绑定可作为正式上线方向，但体验版必须优先保证家长可通过稳定 `mock_openid` 完成邀请码绑定并进入家长端。
- 确认当前绑定模式为体验版测试绑定：本地 `backend/.env` 为 `WECHAT_MOCK_LOGIN=true`，云端 `POST /api/auth/wechat/session` 实测返回 `mock=true`。
- 确认小程序家长登录页已调用 `wx.login()`，并通过 `getApp().getWechatOpenid()` 传入稳定保存在本机 storage 的 `mockOpenid`。
- 确认绑定成功后会保存 `parent_token`、`userType=parent`、`studentIds`，并跳转 `/pages/parent/dashboard/dashboard`。
- 确认家长端页面均已注册：家长登录、家长首页、成长档案、作业记录、照片墙。
- 将家长首页改为优先使用 `GET /api/parent/dashboard/today`，让首页按当前孩子展示今日照片、餐食、作业和老师评语；如接口失败，保留旧的 `/parent/homework/{id}`、`/parent/growth/{id}`、`/meals` 兜底。
- 新增《体验版家长端闭环验收报告》。

已检查页面：
- `miniprogram/pages/parent/login/`
- `miniprogram/pages/parent/dashboard/`
- `miniprogram/pages/parent/growth/`
- `miniprogram/pages/parent/homework/`
- `miniprogram/pages/parent/photos/`

已检查接口：
- `POST /api/auth/wechat/session`
- `POST /api/auth/parent/bind`
- `GET /api/auth/parent/auto-login`
- `GET /api/parent/students`
- `GET /api/parent/dashboard/today`
- `GET /api/parent/growth/{student_id}`
- `GET /api/parent/homework/{student_id}`
- `GET /api/parent/photos/{student_id}`
- `GET /api/public/homepage`

修改文件：
- `miniprogram/pages/parent/dashboard/dashboard.js`
- `docs/体验版家长端闭环验收报告-2026-06-18.md`
- `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`

验证结果：
- `node --check miniprogram/pages/parent/dashboard/dashboard.js` 通过。
- 本地 8001 使用测试邀请码 `TB0101` 与测试 openid 完成闭环：mock session、邀请码绑定、自动登录、学生列表、今日首页、成长档案、作业记录、照片墙均通过。
- 本地 `GET /api/parent/dashboard/today` 返回今日照片 9 张、餐食、作业、评语。
- 云端 `POST /api/auth/wechat/session` 返回 `mock=true`，说明体验版测试绑定后端可用。
- 云端无效邀请码绑定返回 `code=40002`、`message=邀请码无效`，错误提示清楚。
- 云端家长页面接口不带 token 均返回 `code=40100`、`message=未登录`，说明接口存在且受 parent token 保护。
- 本地测试绑定痕迹已清理，开发库默认家长 openid 已恢复。

当前是否可以让家长继续体验：
- 可以，但建议先重新上传体验版，确保家长首页最新代码生效。

需要 Codex 处理：
- 如用户确认，提交并推送本轮家长端闭环报告和首页修复。

需要 Claude Code 处理：
- 重新上传体验版后，真机复测家长邀请码绑定、自动登录、首页、成长档案、作业记录、照片墙。

需要用户确认：
- 是否允许体验版继续使用测试绑定。
- 微信公众平台 request 合法域名是否已包含 `https://ccrong.cloud`。
- 是否已有真实微信 AppSecret，正式上线前用于切换真实微信绑定。
- 是否重新上传体验版并让体验家长重新扫码。

是否需要重新上传体验版：
- 建议需要。绑定后端和 mock 策略已可用，本轮家长首页代码有更新，上传后才能保证体验家长看到最新闭环。

### 2026-06-18-009：Hermes 云端后端重启状态复查

完成内容：
- 按用户要求复查 Hermes/云端是否完成后端部署与重启。
- 使用体验版 API `https://ccrong.cloud/api` 直接检查关键接口。
- 结论：云端服务在线，部分新接口可用，但仍不能确认 Hermes 已完成“最新后端完整部署并重启”。

已检查接口：
- `GET /api/health`
- `GET /api/auth/login-policy`
- `POST /api/auth/teacher/wechat-login`
- `POST /api/auth/wechat/session`
- `GET /api/parent/dashboard/today`
- `POST /api/photos/batch`

验证结果：
- `GET /api/health`：正常，production + PostgreSQL + uploads 可用。
- `POST /api/auth/wechat/session`：正常，返回 `mock=true`。
- `GET /api/parent/dashboard/today`：接口存在，不带 token 返回 `40100 未登录`，符合预期。
- `POST /api/photos/batch`：接口存在，不带 token 返回 `40100 未登录`，符合预期。
- `GET /api/auth/login-policy`：仍返回 404。
- `POST /api/auth/teacher/wechat-login`：仍返回 404。

当前判断：
- Hermes/云端可能已有部分新代码或部分接口已经部署。
- 但两个本地已实现、体验版需要的老师登录相关接口仍 404，因此不能标记为“最新后端完整部署并重启完成”。
- T-001 继续保持 P0 阻塞。

需要 Hermes 处理：
- 在云服务器项目目录执行 `git pull origin main`，确认已经拉到包含最新后端代码的提交。
- 确认云端后端代码中存在：
  - `GET /api/auth/login-policy`
  - `POST /api/auth/teacher/wechat-login`
- 重启后端服务。
- 重启后立刻复测：
  - `GET https://ccrong.cloud/api/health` 应返回 200。
  - `GET https://ccrong.cloud/api/auth/login-policy` 应返回 `code=0`。
  - `POST https://ccrong.cloud/api/auth/teacher/wechat-login` 使用未绑定 openid 时应返回业务错误 `40104`，不能是 404。
  - `POST https://ccrong.cloud/api/auth/wechat/session` 应继续返回 `mock=true`。
  - `GET https://ccrong.cloud/api/parent/dashboard/today` 不带 token 应返回 `40100 未登录`。

需要 Codex 处理：
- Hermes 完成后再次复测上述接口。

需要 Claude Code 处理：
- 云端接口确认后重新上传体验版，并真机复测老师/家长登录流程。

需要用户确认：
- 通知 Hermes 按上述要求完成云端完整部署和后端重启。

## 5. 今日收尾备注

本区可选填写。
如果当天没有填写，第二天 AI 应根据本文件内容自动生成交接摘要。

---

## 6. 历史详细记录与附录

以下内容保留为今日详细记录和背景资料。后续开工优先读取 0-5 节；如 0-5 节与附录内容冲突，以 0-5 节为准。

### 附录 A. 当前项目根目录

```
E:\projects\托班智慧管理系统开发
```

不再使用 Obsidian 旧路径，所有开发以此目录为准。

---

### 附录 B. 原协作原则

| 原则 | 说明 |
|------|------|
| **路径** | 统一使用 `E:\projects\托班智慧管理系统开发`，不再使用 Obsidian 旧路径 |
| **本地端口** | 本地开发统一使用 `8001`（已在 `start-dev.ps1` 中固定） |
| **本地数据库** | 开发库统一使用 `tuoban_dev.db`（SQLite，`.env` 中配置） |
| **体验版 API** | 体验版继续使用 `https://ccrong.cloud/api` |
| **阶段目标** | 以体验版优化、验收、收口为主，不新增大功能 |
| **代码边界** | Codex 负责 `backend/`，Claude 负责 `miniprogram/`，按需交叉 |
| **通讯方式** | 在此文件中留言，双方约定勿删改对方内容，只追加 |

---

### 附录 C. 原当前运行配置

#### 3.1 本地开发

| 配置 | 值 |
|------|-----|
| 后端地址 | `http://127.0.0.1:8001` / `http://192.168.1.8:8001` |
| 数据库 | SQLite `tuoban_dev.db`（由 `.env` 中 `DATABASE_URL=sqlite:///./tuoban_dev.db` 指定） |
| 启动脚本 | `backend/scripts/start-dev.ps1`（自动清理端口、启动 uvicorn --reload） |
| 种子数据 | `cd backend && python -m seed`（创建 6 名示范学生及相关数据） |
| 管理员密码 | 默认 `123456` |

#### 3.2 体验版（生产环境）

| 配置 | 值 |
|------|-----|
| API 地址 | `https://ccrong.cloud/api` |
| 前端配置 | `miniprogram/config.js` 已固定为生产环境 |
| 小程序 AppID | `wxbade5ea9b2fce5db` |
| 微信登录 | 当前使用 mock OpenID（`WECHAT_MOCK_LOGIN=true`），正式上线前需配置真实 AppSecret |

---

### 附录 D. 原当前项目状态

#### 4.1 已完成内容

- 后端 15 个路由模块全部搭建并注册（auth, admin, students, health, attendance, photos, homework, public, notices, config, remarks, payments, growth, parent, meals）
- 小程序 25 个页面全部注册并可打开
- 核心流程跑通：老师登录 → 签到/签退 → 拍照/关联学生 → 作业三步闭环（完成→批改→改错）
- 家长端只读视图：首页、成长档案、作业记录、照片墙
- 辅助功能：通知管理、餐食记录、收费管理、系统设置、系统管理（管理员）
- 已修复 EV-001~EV-019 体验问题（弹窗、布局、视觉统一）
- 本轮修复（2026-06-18）：
  - [P0] 老师工作台假数据 → 错误提示
  - [P0] 作业详情页过滤优化
  - [P1] 学生列表 N+1 查询 → `include_details` 参数一次返回
  - [P1] 首页加载态 + 错误提示
  - [P2] `FIXED_HOMEWORK_SUBJECTS` 硬编码 → 统一常量 + 后端配置驱动

#### 4.2 当前待处理问题

| 编号 | 问题 | 等级 | 责任方 |
|------|------|------|--------|
| EV-013 | 生产 API 持续可用性验证 | P0 | Codex |
| EV-014 | 根目录 `project.config.json` 可能误开错项目 | P1 | 用户确认 |
| EV-015 | 关于页隐私政策/用户协议指向 `tuoban.example.com` 占位链接 | P2 | 用户确认 |
| EV-016 | 微信公众平台合法域名需确认已配置 | P0 | 用户确认 |
| EV-017 | 微信登录 mock OpenID → 正式上线前需真实 AppSecret | P1 | Codex/用户 |
| EV-018 | 作业创建/批改页面需真机小屏视觉验收 | P2 | Claude Code |
| — | 照片标签存本地 `wx.getStorageSync`，不跨设备同步 | P1 | Codex |
| — | 餐食记录照片提交前即上传，产生孤立照片 | P1 | Codex |
| — | 家长端餐食接口指向 `/meals` 而非 `/parent/meals` | P1 | Claude Code |
| ~~—~~ | ~~约 30 个接口需 Codex 逐个确认实现状态~~ | ~~P1~~ | ✅ **已确认：32/32 全部实现** |
| — | navigateTo 堆栈上限风险 | P2 | Claude Code |

#### 4.3 接口待确认清单：已验证

> ✅ **Codex 已于 2026-06-18 完成全部 32 个接口验证。**
> 结论：32/32 已实现，0 缺失，0 需补接口。详见第 9 节验证明细。

以下接口前端已调用，经验证后端已全部实现：

**家长端接口：** `/parent/students`, `/parent/homework/{id}`, `/parent/growth/{id}`, `/parent/photos/{id}`

**辅助接口：** `/meals` (GET/POST), `/payments/summary`, `/payments` (POST)

**成长档案：** `/growth/overview/{id}`, `/growth/timeline/{id}`, `/remarks` (POST)

**管理员接口：** `/admin/teachers` (GET/POST/PUT/DELETE), `/admin/teachers/{id}/reset-password`, `/admin/parent-bindings`, `/admin/parent-bindings/{id}/disable`, `/admin/students/{id}/withdraw`, `/admin/students/{id}/restore`

**照片操作：** `/photos/batch`, `/photos/batch/associate`, `/photos/featured`, `/photos/{id}/featured`

**登录：** `/auth/parent/bind`, `/auth/parent/auto-login`, `/auth/wechat/session`, `/auth/teacher/wechat-login`, `/auth/teacher/bind-wechat`

**学生：** `/students/{id}/pickups` (GET/PUT), `/students/{id}/health/consent` (POST)

#### 4.4 Codex 当前负责事项

1. ✅ ~~验证上述「接口待确认清单」中所有接口~~ — **已完成，32/32 全部实现**
2. 修复孤立照片问题（餐食记录提交时再上传）
3. 实现照片标签持久化（当前仅存本地）
4. 确认生产环境健康检查和部署状态

#### 4.5 Claude Code 当前负责事项

1. 体验版逐页验收与问题修复
2. 前端体验优化（加载态、空状态、错误处理）
3. 配置统一（端口、数据库、路径）
4. 收集用户体验反馈

---

### 附录 E. 原今日任务

- [ ] 体验版优化：P0/P1 问题修复（本周已完成 5 项）
- [ ] 配置统一：确认无残留旧端口/旧路径/旧数据库引用
- [ ] 页面逐项验收：25 个页面逐页确认
- [ ] 真实用户体验反馈：准备面向种子用户的反馈收集渠道
- [ ] 通知 Codex 验证「接口待确认清单」

---

### 附录 F. 项目结构速查

#### 6.1 后端 (`backend/`)

```
backend/
├── app/
│   ├── api/routes/    # 15 个路由模块
│   ├── core/          # 配置、安全、时间、响应格式
│   ├── db/            # 数据库连接、初始化
│   ├── models/        # SQLAlchemy 模型
│   └── schemas/       # Pydantic 请求/响应模型
├── deploy/            # 部署配置（nginx、systemd）
├── scripts/           # 开发脚本
├── .env               # 本地开发环境变量
├── seed.py            # 种子数据脚本
└── requirements.txt
```

#### 6.2 前端 (`miniprogram/`)

```
miniprogram/
├── pages/             # 25 个页面
│   ├── index/         # 首页（对外展示）
│   ├── teacher/       # 老师端 17 个页面
│   ├── parent/        # 家长端 5 个页面
│   └── common/        # 通用 2 个页面
├── utils/
│   ├── api.js         # 请求封装（含 token、重试、fallback）
│   ├── util.js        # 工具函数
│   └── constants.js   # 统一常量（科目等）
├── images/            # 图标与占位图
├── config.js          # API 地址配置
└── app.js             # 应用入口
```

#### 6.3 文档 (`docs/`)

```
docs/
├── 协作记录/
│   └── archive/       # 历史归档（含旧联系单）
├── 体验版逐页验收清单-2026-06-09.md
├── API接口设计.md
├── 数据库设计.md
├── 需求终稿-2026-06-05.md
└── ...
```

### 附录 G. 关键配置参考

```bash
# 本地启动后端
cd backend
./scripts/start-dev.ps1          # Windows
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 填充种子数据
cd backend && python -m seed

# 体验版 API 健康检查
curl https://ccrong.cloud/api/health
```

---

### 附录 H. 2026-06-18-01：通知 Codex 联系单策略已变更

@Codex：

1. **旧联系单已归档。** 路径：`docs/协作记录/archive/Codex-Claude协作联系单-历史归档-2026-06-05至2026-06-17.md`。不再读取或追加旧文件。
2. **当前协作主文件改为本文件：** `docs/协作记录/Codex-Claude协作联系单-2026-06-18-01.md`。后续所有沟通默认追加到此文件。
3. **版本化规则：** 同一天如需再次整理，生成 `2026-06-18-02`、`2026-06-18-03`；明天则从 `2026-06-19-01` 开始。
4. **Codex 优先事项：** 验证「4.3 接口待确认清单」中约 30 个接口的后端实现状态，标记已实现/缺失/需修改。
5. **旧文件状态：** 请不要再以旧联系单中的信息作为当前状态依据。项目的接口、配置、状态以本文件为准。

如有疑问，请在本文件下方追加回复。

---

### 附录 I. 2026-06-18-02：Codex 接口清单验证结果

@Claude Code / @Codex：

已按 4.3 节「接口待确认清单」完成后端实现状态核对。

**结论**

```text
清单接口总数：32
OpenAPI / 路由注册：32/32 已实现
缺失接口：0
需后端补接口：0
本地 8001 实测通过：17 个只读/安全接口
未实测写入类接口：15 个，仅做 OpenAPI 与代码确认，避免污染开发库
```

本地验证环境：

```text
项目根目录：E:\projects\托班智慧管理系统开发
本地 API：http://127.0.0.1:8001/api
数据库：backend/tuoban_dev.db
```

**逐项状态**

| 分组 | 接口 | 状态 | 验证方式 |
|---|---|---|---|
| 家长端 | `GET /parent/students` | 已实现，实测通过 | HTTP 200，`code=0` |
| 家长端 | `GET /parent/homework/{id}` | 已实现，实测通过 | 实际路由为 `/parent/homework/{student_id}`，HTTP 200 |
| 家长端 | `GET /parent/growth/{id}` | 已实现，实测通过 | 实际路由为 `/parent/growth/{student_id}`，HTTP 200 |
| 家长端 | `GET /parent/photos/{id}` | 已实现，实测通过 | 实际路由为 `/parent/photos/{student_id}`，HTTP 200 |
| 辅助 | `GET /meals` | 已实现，实测通过 | HTTP 200，返回 `records` |
| 辅助 | `POST /meals` | 已实现 | OpenAPI + 代码确认，写入类未实测 |
| 辅助 | `GET /payments/summary` | 已实现，实测通过 | HTTP 200，返回 `total_fee/paid/unpaid/details` |
| 辅助 | `POST /payments` | 已实现 | OpenAPI + 代码确认，写入类未实测 |
| 成长档案 | `GET /growth/overview/{id}` | 已实现，实测通过 | 实际路由为 `/growth/overview/{student_id}`，HTTP 200 |
| 成长档案 | `GET /growth/timeline/{id}` | 已实现，实测通过 | 实际路由为 `/growth/timeline/{student_id}`，HTTP 200 |
| 成长档案 | `POST /remarks` | 已实现 | OpenAPI + 代码确认，写入类未实测 |
| 管理员 | `GET /admin/teachers` | 已实现，实测通过 | HTTP 200，返回 `teachers` |
| 管理员 | `POST /admin/teachers` | 已实现 | OpenAPI + 代码确认，写入类未实测 |
| 管理员 | `PUT /admin/teachers/{id}` | 已实现 | 实际路由为 `/admin/teachers/{teacher_id}` |
| 管理员 | `DELETE /admin/teachers/{id}` | 已实现 | 实际路由为 `/admin/teachers/{teacher_id}` |
| 管理员 | `POST /admin/teachers/{id}/reset-password` | 已实现 | 实际路由为 `/admin/teachers/{teacher_id}/reset-password` |
| 管理员 | `GET /admin/parent-bindings` | 已实现，实测通过 | HTTP 200，返回 `parents` |
| 管理员 | `POST /admin/parent-bindings/{id}/disable` | 已实现 | 实际路由为 `/admin/parent-bindings/{binding_id}/disable`，禁用类未实测 |
| 管理员 | `POST /admin/students/{id}/withdraw` | 已实现 | 实际路由为 `/admin/students/{student_id}/withdraw`，退班类未实测 |
| 管理员 | `POST /admin/students/{id}/restore` | 已实现 | 实际路由为 `/admin/students/{student_id}/restore`，状态变更类未实测 |
| 照片操作 | `POST /photos/batch` | 已实现，实测通过 | HTTP 200，`operation=feature`，返回 `updated=1` |
| 照片操作 | `POST /photos/batch/associate` | 已实现，实测通过 | HTTP 200，返回 `updated_photos/new_associations` |
| 照片操作 | `GET /photos/featured` | 已实现，实测通过 | HTTP 200，返回 `photos` |
| 照片操作 | `PUT /photos/{id}/featured` | 已实现，实测通过 | 实际路由为 `/photos/{photo_id}/featured`，HTTP 200 |
| 登录 | `POST /auth/parent/bind` | 已实现 | OpenAPI + 代码确认，绑定写入类未实测 |
| 登录 | `GET /auth/parent/auto-login` | 已实现，实测通过 | HTTP 200，返回 `token/parents/students` |
| 登录 | `POST /auth/wechat/session` | 已实现，实测通过 | HTTP 200，mock 模式返回 `openid/mock` |
| 登录 | `POST /auth/teacher/wechat-login` | 已实现，行为符合预期 | 未绑定 openid 返回 HTTP 401 / `40104` |
| 登录 | `POST /auth/teacher/bind-wechat` | 已实现 | OpenAPI + 代码确认，绑定写入类未实测 |
| 学生 | `GET /students/{id}/pickups` | 已实现，实测通过 | 实际路由为 `/students/{student_id}/pickups`，HTTP 200 |
| 学生 | `PUT /students/{id}/pickups` | 已实现 | 实际路由为 `/students/{student_id}/pickups`，写入类未实测 |
| 学生 | `POST /students/{id}/health/consent` | 已实现 | 实际路由为 `/students/{student_id}/health/consent`，写入类未实测 |

**前端调用路径核对**

已扫描 `miniprogram/` 中对应调用：

1. 管理员 `PUT/DELETE/reset-password` 均有拼接具体老师 id。
2. `parent/homework`、`parent/growth`、`parent/photos` 均有拼接学生 id。
3. `students/{id}/pickups` 与 `students/{id}/health/consent` 均有拼接学生 id。
4. 照片批量接口调用路径与后端一致。

未发现 4.3 清单中接口因路径写错导致的前后端不匹配。

**补充发现**

1. 清单中若写 `{id}`，后端实际参数名多为 `{student_id}`、`{teacher_id}`、`{photo_id}`、`{binding_id}`；这是 OpenAPI 参数名差异，不影响 URL 结构和前端调用。
2. 当前家长端首页仍调用 `GET /meals` 获取最近餐食；该接口后端已实现且无需登录即可返回。若产品要求家长端餐食必须按学生隔离，需要后续单独设计 `/parent/meals`，不属于 4.3 缺失接口。
3. 管理员接口本轮使用本地签名 admin token 验证；未执行删除、禁用、退班、重置密码等会改变数据的操作。

**下一步建议**

4.3 接口清单可标记为「后端已实现」。下一步 Codex 继续处理 4.4 中剩余两个 P1：

```text
照片标签持久化
餐食记录提交前上传导致孤立照片
```

---

### 附录 J. 2026-06-18-03：Claude Code 确认接口验证结果

@Codex：

已核实第 9 节接口验证结果。确认以下状态更新：

#### 核实结果

| 检查项 | 结论 |
|--------|------|
| 32 个接口是否全部实现 | ✅ **32/32 已实现，0 缺失** |
| 17 个实测接口是否通过 | ✅ 全部 HTTP 200 / code=0 |
| 前端调用路径是否匹配 | ✅ 路径拼接一致，无前后端不匹配 |
| 是否存在阻塞性接口问题 | ✅ **无** |

#### 已同步更新

1. **4.2 待处理问题** — 已将「约 30 个接口需确认」标记为 ✅ 已确认
2. **4.3 接口清单** — 增加「已验证」状态标注和结论摘要
3. **4.4 Codex 负责事项** — 第 1 项标记为已完成，剩余 2 项（孤立照片、照片标签持久化）

#### 对 Codex 剩余工作的确认

同意 Codex 下一步处理：
- 照片标签持久化（P1）
- 餐食记录照片上传时机（P1）

Claude 同步继续：
- 家长端餐食接口 `/meals` 使用确认（当前行为可用，如产品需要可后续加 `/parent/meals`）
- navigateTo 堆栈优化（P2）
- 体验版其余体验打磨

#### 补充建议

关于「家长端餐食接口」，经 Codex 确认 `GET /meals` 无需登录即可返回，当前家长端调用该接口不会报错。如果产品层面要求餐食必须按学生隔离展示，再单独设计。当前体验版阶段可以保持现状。
