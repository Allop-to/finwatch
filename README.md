# FinWatch — 个人财务行为数据挖掘与异常消费预测系统

本地优先的个人财务分析平台，支持消费数据导入、行为模式挖掘、多维度异常检测，以及实时告警推送。前端通过 Capacitor 打包为 Android APK。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 批量分析引擎 | DuckDB + Polars |
| 异常检测 | PyOD (Isolation Forest) + Scikit-learn (IQR/Z-Score) |
| 数据库 | SQLite（本地）→ PostgreSQL（容器化） |
| 任务调度 | APScheduler（定时检测 + 预算检查） |
| 实时推送 | WebSockets |
| 前端框架 | Vite + React 18 + TypeScript |
| UI 组件 | Tailwind CSS 3 + Shadcn UI |
| 可视化 | Recharts |
| 状态管理 | TanStack Query + Zustand |
| 移动打包 | Capacitor → Android APK |

## 环境要求

- **Python** >= 3.8（推荐 3.11+）
- **Node.js** >= 18
- **Android Studio**（仅 APK 打包需要）

## 快速启动

### 1. 克隆项目

```bash
git clone <repo-url>
cd finwatch
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境并安装依赖
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt

# 启动服务（默认端口 8000）
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/health 确认后端启动成功：
```json
{"status":"ok","app":"FinWatch"}
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认端口 5173）
npm run dev
```

访问 http://localhost:5173 进入应用。

> 前端通过 Vite 代理将 `/api` 请求转发到 `http://localhost:8000`，无需额外配置。

## 功能说明

### 仪表盘（Dashboard）

- 本月支出总额、预算剩余、未读异常数
- 近 30 天支出趋势折线图
- 支出分类占比饼图

### 交易记录（Transactions）

- 查看所有交易，支持搜索商户/备注
- 筛选条件：日期范围、分类、金额区间
- 分页浏览，支持手动添加交易

### 导入数据（Import）

1. 选择数据来源（支付宝 / 微信）
2. 上传 CSV 账单文件（拖拽或点击选择）
3. 系统自动解析、去重，显示导入结果

**支付宝 CSV 格式示例：**
```csv
交易时间,收/支,交易对方,商品说明,金额
2026-07-20 12:30:00,支出,星巴克,拿铁咖啡,42.00
2026-07-19 18:00:00,支出,滴滴出行,打车,28.50
```

**微信 CSV 格式示例：**
```csv
交易时间,交易类型,交易对方,商品,金额(元)
2026-07-20 12:30:00,商户消费,美团外卖,午餐,35.00
```

> 重复导入同一文件时，系统通过幂等哈希自动跳过已存在的交易。

### 异常检测（Detection）

- 点击「立即检测」运行检测引擎
- 系统自动定时检测（每 30 分钟增量 + 每日凌晨 2 点全量）
- 三种检测器并行打分：

| 检测器 | 方法 | 检测内容 |
|--------|------|---------|
| StatisticalDetector | Isolation Forest + IQR | 金额离群、分类占比突变 |
| RuleDetector | 硬规则 + 软规则 | 单笔大额（>¥10,000）、深夜消费（23:00-05:00） |

- 混合融合算法：硬规则有否决权，直接穿透加权平均
- 严重度分级：🔴 高危（≥0.8）/ 🟡 中危（≥0.5）/ 🟢 低危
- 高危异常通过 WebSocket 实时推送到前端弹窗

### 预算管理（Budget）

- 设置月度总预算或分类预算
- 实时显示已用金额和进度百分比
- 超过 80% 时触发预警

### 设置（Settings）

- **分类管理**：查看系统预置的 24 个分类，添加自定义分类
- **检测规则**：查看当前生效的检测规则（Phase 2 支持自定义）
- **数据管理**：手动触发全量检测

## 生成 Android APK

```bash
cd frontend

# 确保前端已构建
npm run build

# 同步 Capacitor
npx cap sync

# 打开 Android Studio 构建
npx cap open android
```

在 Android Studio 中：**Build → Build Bundle(s) / APK(s) → Build APK(s)**

APK 输出路径：`frontend/android/app/build/outputs/apk/debug/app-debug.apk`

## API 接口

所有接口前缀：`/api/v1`

### 交易

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/transactions` | 创建交易（自动去重） |
| GET | `/transactions` | 查询交易列表（分页+筛选） |
| GET | `/transactions/:id` | 获取交易详情 |
| PUT | `/transactions/:id` | 更新交易 |
| DELETE | `/transactions/:id` | 删除交易 |

### 分类

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/categories` | 获取分类树（系统+自定义） |
| POST | `/categories` | 创建自定义分类 |
| DELETE | `/categories/:id` | 删除自定义分类（系统分类不可删） |

### 导入

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/imports/upload` | 上传 CSV 文件导入 |
| GET | `/imports` | 查看导入历史 |

### 检测

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/detection/run` | 手动触发检测 |
| GET | `/detection` | 查看检测结果（按严重度筛选） |
| GET | `/detection/:id` | 查看单条检测详情 |
| PATCH | `/detection/:id/read` | 标记为已读 |

### 预算

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/budgets` | 创建预算 |
| GET | `/budgets` | 查看预算列表（含进度） |
| DELETE | `/budgets/:id` | 删除预算 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `ws://localhost:8000/api/v1/ws` | 实时推送连接 |

事件类型：`detection.alert`（高危异常）、`budget.warning`（预算预警）、`system.health`（心跳）

## 项目结构

```
finwatch/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库引擎
│   │   ├── api/v1/              # API 路由
│   │   │   ├── transactions.py  # 交易 CRUD
│   │   │   ├── categories.py    # 分类管理
│   │   │   ├── imports.py       # 文件导入
│   │   │   ├── detection.py     # 异常检测
│   │   │   ├── budget.py        # 预算管理
│   │   │   └── websocket.py     # WebSocket
│   │   ├── services/            # 业务逻辑层
│   │   ├── engine/              # 核心挖掘引擎
│   │   │   ├── features.py      # 特征工程（含冷启动防护）
│   │   │   ├── detectors/       # 检测器插件
│   │   │   │   ├── statistical.py  # 统计检测器
│   │   │   │   └── rule.py         # 规则检测器
│   │   │   └── parsers/         # 文件解析器
│   │   │       ├── alipay.py    # 支付宝 CSV
│   │   │       └── wechat.py    # 微信 CSV
│   │   ├── models/              # ORM 模型（7 张表）
│   │   ├── schemas/             # Pydantic 类型
│   │   └── seeds/               # 种子数据（24 个分类）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # 6 个页面组件
│   │   ├── components/          # UI 组件
│   │   ├── api/                 # API 请求封装
│   │   ├── store/               # Zustand 状态管理
│   │   └── hooks/               # 自定义 Hooks
│   └── capacitor.config.ts      # Capacitor 配置
└── docs/
    ├── spec.md                  # 设计文档
    └── phase-1-plan.md          # 实现计划
```

## 数据库

系统使用 SQLite，数据库文件 `finwatch.db` 首次启动时自动创建。包含 7 张表：

| 表 | 说明 |
|----|------|
| users | 用户（预留多用户） |
| categories | 分类（24 个系统预置 + 自定义） |
| transactions | 交易记录（含 idempotency_hash 防重） |
| budgets | 预算设置 |
| detection_results | 异常检测结果（reasons JSON 结构化） |
| detection_rules | 自定义检测规则 |
| import_records | 导入历史 |
| llm_conversations | LLM 对话记录（Phase 2） |

## 后续计划

- **Phase 2**：PatternDetector（行为模式检测）、DeepSeek LLM 智能解读、数据脱敏引擎、对话分析页面
- **Phase 3**：PostgreSQL 容器化、Docker Compose 一键部署、多用户支持、GitHub Actions CI/CD
