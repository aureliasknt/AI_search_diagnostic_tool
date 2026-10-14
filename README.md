# AI 搜索诊断工具 (AI Search Diagnostic Tool) — MVP

面向 GEO 营销代理商的品牌 AI 可见度诊断系统：运营人员在后台发起诊断，系统对**豆包（火山方舟）**进行多轮采样，生成品牌得分、竞品对比、舆情分析与优化建议；客户端通过 H5 链接查看报告，填写手机号 + 短信验证码后解锁完整内容并留资，后台实时沉淀线索并支持 Excel 导出。

> 依据《AI Search Diagnostic Tool Requirements Document V1.0》实现。V1.0 仅覆盖豆包单一平台，报告内不含信源（来源）分析模块。

## 目录结构

```
├── backend/          FastAPI + SQLAlchemy（引擎 / 管理 API / 公共报告 API / PDF）
├── frontend-h5/      Vue 3 + Vite + ECharts — 客户端报告页 (/r/:code)
├── frontend-admin/   Vue 3 + Element Plus — 运营后台
├── docker-compose.yml  Postgres + Redis（仅生产环境需要）
└── README.md
```

## 快速开始（本地开发，无需 API Key）

要求：Python ≥ 3.10，Node ≥ 18。

```bash
# 1) 后端
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env                            # 默认 mock 模式即可跑通全流程
python -m scripts.seed                            # 建表 + 账号 + 1 份示例诊断
uvicorn app.main:app --port 8000                  # http://localhost:8000

# 2) 客户端 H5（新终端）
cd frontend-h5
npm install
npx vite --port 5173                              # http://localhost:5173

# 3) 运营后台（新终端）
cd frontend-admin
npm install
npx vite --port 5174                              # http://localhost:5174
```

打开后台 → 用 `admin / admin123` 登录 → 「诊断管理」中查看种子示例诊断（已完成）→ 点「分享」复制 H5 链接 / 二维码。

### 种子账号

| 账号 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | 管理员（全部功能 + 配置中心） |
| `sales01` | `sales123` | 销售（仅自己创建的诊断与线索） |

> 仅用于开发，部署前务必修改。

## 演示全流程（UAT）

> **局域网演示**：先双击 `start-demo.bat`，然后用它打印的 IP 链接。
> **公网演示（任意网络/微信外网）**：只双击 `start-tunnel.bat`——它会自动建立
> Cloudflare tunnel、检测公共 URL、重启后端并打印可直接发到微信的完整链接
> （格式 `https://xxx.trycloudflare.com/r/<分享码>`）。停止用 `stop-all.bat`。
> 注意：该 URL 每次运行都会变化，且 trycloudflare 在国内可达性不稳定、链接仅
> 在脚本运行时有效——正式对客户请使用备案域名部署（见下）。

### 客户端自助诊断流程（H5 首页 `/`）

1. 客户端打开 H5 首页，输入**企业名称** → 点「✨ AI推测行业」：由豆包API推测
   行业/主营产品/搜索关键词/竞品并自动填入（mock 模式为本地规则推测），**全部可手动修改**。
2. 点「开始诊断」→ 后端生成 **100+ 个提问**（每个关键词按完整模板轮次均分，
   实际约 100–110 条），并行查询豆包 → 自动跳转报告页 `/r/<分享码>`
   （生成中显示进度，完成自动刷新）。
3. 报告新增 **查询详情** tab（数据总览之后）：100 条提问列表，20 条/页，
   点击任意一条弹出完整问答弹窗，**品牌名在回答中自动标红**（含别名匹配）。
   该 tab 与竞品/舆情/总结一样需解锁后查看；PDF 导出会附带全部问答。
4. 自助诊断的线索（手机号）同样进入后台「线索管理」，归属 `h5_guest` 占位账号。

### 后台运营流程（管理面板 `/`）

1. 后台「新建诊断」→ 填企业名 + 关键词（可填竞品）→ 提交。默认 `provider=mock`，数秒内完成。
2. 诊断完成后点「分享」→ 复制 H5 链接（微信可直接打开）。
3. H5 页可见：得分仪表盘、KPI、结论；**竞品分析 / 舆情分析 / 报告总结**处于锁定模糊态。
4. 点击锁定区 → 输入手机号 → 「获取验证码」。`SMS_PROVIDER=mock` 时验证码直接显示在页面提示与后端响应 `dev_code` 中。
5. 填写验证码（+ 可选姓名/公司，勾选隐私政策）→ 解锁全部内容 → 顶部/底部「导出 PDF」。
6. 后台「线索管理」→ 新线索实时出现（手机号已掩码 `138****8000`）→ 可改跟进状态 → 「导出 Excel」。
7. 管理员「配置中心」：调整评分权重（默认 提及率40 / 位置30 / 情感30）、提问模板、企业别名、问题推荐规则、豆包 API、报告有效期与结论模板。

## 环境变量（backend/.env）

| 变量 | 默认 | 说明 |
|---|---|---|
| `SECRET_KEY` | — | JWT / 手机号加密的根密钥，**生产必须修改** |
| `DATABASE_URL` | `sqlite:///./aidiag.db` | 生产换 `postgresql+psycopg://…` 或 MySQL |
| `WORKER_BACKEND` | `local` | `local`（进程内异步）/ `celery`（需 Redis） |
| `DOUBAO_API_KEY` | 空 | 火山方舟 API Key；为空时平台配置 `provider=mock` 可演示 |
| `DOUBAO_BASE_URL` | `https://ark.cn-beijing.volces.com/api/v3` | OpenAI 兼容端点 |
| `DOUBAO_MODEL` | `doubao-seed-1-6-250615` | 模型 ID |
| `SMS_PROVIDER` | `mock` | `mock`（验证码回显）/ `aliyun` / `tencent`（需配置签名与模板） |
| `H5_BASE_URL` | `http://localhost:5173` | 分享链接 / 二维码的前缀 |
| `CORS_ORIGINS` | `*` | 生产收紧为 H5/后台域名 |

## 生产部署要点

- 依赖：`docker-compose.yml` 提供 Postgres + Redis；`WORKER_BACKEND=celery`，worker 用
  `celery -A app.engine.celery_app worker` 启动。
- 短信：`SMS_PROVIDER=aliyun|tencent` 并在「配置中心 → 平台配置」或环境变量中配置签名/模板码；遵守各云 60s 频控。
- PDF：后端需安装 Playwright 浏览器（`playwright install chromium`）。
- 合规：手机号 Fernet 加密存储、展示层仅掩码；隐私政策勾选为解锁前置条件（PIPL）。

## 测试

```bash
cd backend
pytest                      # 17 项：parser / scoring / security / API 冒烟
```

## 设计说明

- **评分**：`综合得分 = 提及率×40% + 提及位置×30% + 情感倾向×30%`（权重可调）；≥80 良好 / 60–79 一般 / <60 较差。
- **采样**：每关键词取 3–5 个提问模板变体 × 2–3 轮，并发请求豆包；答案按品牌全称+别名解析提及与位置，二次 LLM 调用做情感判定（mock 模式用语料规则替代）。
- **反枚举**：分享码 12 位随机；报告默认 90 天过期。
- **防重复留资**：同一报告 + 同一手机号仅需验证一次（数据库唯一约束 + 重复验证直接续发解锁令牌）。
