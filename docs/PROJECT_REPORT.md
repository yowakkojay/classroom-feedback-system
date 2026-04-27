# 课堂学情监控管理系统 — 项目技术报告

## 一、项目概述

本系统是一个面向高校课堂场景的**实时学情监控平台**。学生在课堂上通过发送表情（1-6 分）反馈对课程内容的理解程度，教师端可实时查看全班聚合统计（参与人数、分数分布、平均分、方差、柱状图、饼状图、趋势折线图）。系统还提供在线讨论区，支持师生之间文字和图片的实时交流，以及管理员对用户的增删改查管理。

**核心价值**：将传统课堂中难以量化的"学生听懂了多少"转化为实时、可视化的数据，帮助教师及时调整教学节奏。

---

## 二、技术栈

| 层次 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **后端框架** | Django + DRF | 4.2 / 3.15 | REST API 开发 |
| **实时通信** | Django Channels | 4.1 | WebSocket 双向通信 |
| **ASGI 服务器** | Daphne | 4.1.2 | 同时处理 HTTP 和 WebSocket |
| **认证** | SimpleJWT | 5.3 | JWT Token 认证 |
| **第三方登录** | GitHub OAuth | — | OAuth 2.0 授权码模式 |
| **数据库** | MySQL | 8.x | 生产数据存储（开发用 SQLite） |
| **前端框架** | Vue 3 | 3.5 | Composition API 风格 |
| **构建工具** | Vite | 8.0 | 开发服务器 + 生产构建 |
| **UI 组件库** | Element Plus | 2.13 | 表单、表格、弹窗等 |
| **图表库** | ECharts | 6.0 | 柱状图、饼状图、折线图 |
| **状态管理** | Pinia | 3.0 | 用户认证状态 |
| **HTTP 客户端** | Axios | 1.14 | API 请求 + JWT 拦截器 |
| **Excel 导出** | openpyxl | 3.1 | 服务端生成 .xlsx 文件 |
| **反向代理** | Nginx | 1.24 | 静态文件托管 + 请求转发 |
| **公网穿透** | Cloudflare Tunnel | — | 无需公网 IP 安全暴露服务 |
| **压力测试** | Locust | — | 模拟 200 并发用户 |

---

## 三、系统架构

```
                          ┌─────────────────────────┐
                          │   Cloudflare CDN + SSL   │
                          │   (HTTPS + WSS 加速)     │
                          └────────────┬────────────┘
                                       │
                          ┌────────────┴────────────┐
                          │   Cloudflare Tunnel      │
                          │   (安全隧道穿透内网)      │
                          └────────────┬────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                              Nginx (反向代理)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ /        │  │ /api/    │  │ /ws/     │  │ /static/ │  │ /media/  │      │
│  │ 前端静态  │  │ 后端 API │  │ WebSocket│  │ Django   │  │ 上传文件  │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘  └──────────┘      │
│       │             │             │                                          │
│  frontend/dist  ┌───┴─────────────┴───┐                                     │
│                 │   Daphne (ASGI)      │                                     │
│                 │   HTTP + WebSocket   │                                     │
│                 └──────────┬───────────┘                                     │
│                            │                                                 │
│                     ┌──────┴──────┐                                          │
│                     │   MySQL     │                                          │
│                     └─────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 前后端分离架构

```
前端 (Vue 3 SPA)                    后端 (Django + DRF + Channels)
┌─────────────────┐                 ┌─────────────────────────────┐
│ Vue Router      │  HTTP REST API  │ URL Router → ViewSet/View   │
│  (角色路由守卫)  │ ──────────────→ │  JWT 认证 → 序列化器 → 模型  │
│ Pinia Store     │  JSON 请求/响应  │                              │
│  (Token 管理)   │ ←────────────── │ Django ORM → MySQL          │
│ ECharts 图表    │                 │                              │
│  (数据可视化)   │  WebSocket      │ Django Channels → Consumer   │
│ Axios 拦截器    │ ←══════════════ │  (实时统计推送/聊天广播)       │
└─────────────────┘                 └─────────────────────────────┘
```

---

## 四、数据库设计

### ER 关系图

```
┌──────────┐ 1  ┌────────────────┐ 1  ┌────────────────┐
│   User   │───→│ StudentProfile │    │ TeacherProfile  │
│(Abstract)│    └────────────────┘    └────────────────┘
└────┬─────┘
     │ 1
     │        ┌──────────┐ 1  ┌──────────────┐ 1  ┌───────────────┐
     ├───────→│  Course  │───→│ ClassSession │───→│ EmojiReaction │
     │ teacher│ (课程)    │    │  (课堂时段)   │    │  (表情反馈)    │
     │        └──────────┘    └──────┬───────┘    └───────────────┘
     │                               │ 1
     │                               │
     │        ┌──────────┐           │
     └───────→│ Message  │←──────────┘
       sender │ (讨论消息)│  session
              └──────────┘
```

### 核心模型字段

**User（用户）** — 继承 Django AbstractUser

| 字段 | 类型 | 说明 |
|------|------|------|
| role | CharField | 角色：student / teacher / admin |
| phone | CharField | 联系方式 |
| github_id | BigIntegerField | GitHub OAuth 关联 ID |

**ClassSession（课堂时段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| course | ForeignKey(Course) | 所属课程 |
| start_time | DateTimeField | 开始时间 |
| end_time | DateTimeField | 结束时间（可为空） |
| refresh_interval | PositiveIntegerField | 时段长度（分钟），默认 5 |
| is_active | BooleanField | 是否正在进行 |

**EmojiReaction（表情反馈）** — 联合唯一约束 [student, session, time_slot]

| 字段 | 类型 | 说明 |
|------|------|------|
| student | ForeignKey(User) | 反馈学生 |
| session | ForeignKey(ClassSession) | 课堂时段 |
| score | PositiveIntegerField | 分数 1-6（含校验器） |
| time_slot | PositiveIntegerField | 时段编号 |

**Message（讨论消息）**

| 字段 | 类型 | 说明 |
|------|------|------|
| session | ForeignKey(ClassSession) | 所属课堂 |
| sender | ForeignKey(User) | 发送者 |
| content | TextField | 文字内容 |
| image | ImageField | 图片附件 |

---

## 五、核心功能实现

### 5.1 实时表情反馈与统计

这是系统最核心的功能，数据流如下：

```
学生点击表情 → POST /api/feedback/submit/ → 数据库 update_or_create
                                                  │
                                                  ↓
教师端 WebSocket ← ws/feedback/{session_id}/ ← Django Channels 广播
       │                                          │
       ↓                                          ↓
  ECharts 实时更新                            统计计算（聚合查询）
  柱状图 / 饼状图 / 折线图                    Count / Avg / Variance
```

**关键设计：**
- **`update_or_create`**：同一学生在同一时段内重复提交会覆盖旧分数，保证每人每时段只有一个反馈
- **双重保障机制**：WebSocket 实时推送 + HTTP 30 秒轮询，确保数据不丢失
- **时段自动计算**：`time_slot = floor((当前时间 - 开始时间) / (刷新间隔 × 60))`，将课堂划分为多个等长时段

**六种表情对应表：**

| 分数 | 表情 | 含义 | 图表颜色 |
|------|------|------|---------|
| 1 | 😫 | 完全不懂 | 红色 |
| 2 | 😟 | 不太懂 | 橙色 |
| 3 | 😐 | 一般 | 灰色 |
| 4 | 🙂 | 基本理解 | 绿色 |
| 5 | 😊 | 理解 | 蓝色 |
| 6 | 🤩 | 完全理解 | 紫色 |

**统计 API 返回格式：**
```json
{
  "total_students": 42,
  "distribution": {"1": 5, "2": 3, "3": 8, "4": 12, "5": 10, "6": 4},
  "average": 3.81,
  "variance": 2.14
}
```

### 5.2 在线讨论区

讨论区支持**双通道消息发送**，兼顾实时性和可靠性：

```
                    ┌──────────────────────────┐
                    │      ChatConsumer        │
                    │  (Django Channels)       │
                    │                          │
文字消息 ──WebSocket──→│ receive() → save to DB │──group_send──→ 所有客户端
                    │                          │
图片消息 ──REST API────→│ send_message() → DB   │──group_send──→ 所有客户端
                    └──────────────────────────┘
```

**为什么用双通道？**
- 文字消息走 WebSocket：延迟低，体验像即时聊天
- 图片消息走 REST API：需要 `multipart/form-data` 上传文件，WebSocket 不适合传二进制大文件

### 5.3 认证系统

#### JWT 认证流程

```
登录请求 → 后端验证用户名密码 → 签发 Access Token (12h) + Refresh Token (7天)
                                     │
              前端存储到 sessionStorage ←┘
                                     │
              每次请求 Axios 拦截器自动添加 Header: Authorization: Bearer xxx
                                     │
              WebSocket 连接通过 query string 传递: ?token=xxx
                                     │
              后端 JWTAuthMiddleware 解析 token → 注入 scope['user']
```

#### GitHub OAuth 流程

```
用户点击"GitHub登录"
    │
    ↓
重定向到 GitHub 授权页 (client_id + scope=user:email)
    │
    ↓
用户同意授权，GitHub 回调到前端 /auth/callback/github?code=xxx
    │
    ↓
前端将 code 发送到 POST /api/auth/github/
    │
    ↓
后端用 code 向 GitHub 换取 access_token
    │
    ↓
后端用 access_token 调用 GitHub API 获取用户信息
    │
    ├──→ 已关联用户 → 直接签发 JWT
    ├──→ 邮箱匹配 → 自动关联 github_id → 签发 JWT
    └──→ 新用户   → 返回 need_bind → 前端展示绑定表单
                    → 用户输入系统账号密码 → POST /api/auth/github/bind/
```

### 5.4 角色权限控制

系统设计了三级角色，贯穿前后端：

| 角色 | 前端路由 | 后端权限 | 功能范围 |
|------|---------|---------|---------|
| **student** | `/student/*` | IsAuthenticated | 提交反馈、讨论交流 |
| **teacher** | `/teacher/*` | IsAuthenticated | 创建课堂、查看统计、历史查询、导出 |
| **admin** | `/admin/*` | IsAdmin | 用户增删改查、搜索筛选 |

**前端守卫**：Vue Router `beforeEach` 钩子，根据 `meta.role` 和当前用户角色决定是否放行。

**后端守卫**：DRF `permission_classes` 装饰器，在视图层校验用户角色。

---

## 六、API 接口一览

### 认证接口 `/api/auth/`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/login/` | 公开 | 密码登录，返回 JWT |
| POST | `/github/` | 公开 | GitHub OAuth 登录 |
| POST | `/github/bind/` | 公开 | 绑定 GitHub 账号 |
| GET | `/me/` | 登录 | 获取当前用户信息 |
| CRUD | `/users/` | 管理员 | 用户管理 |

### 反馈接口 `/api/feedback/`

| 方法 | 路径 | 说明 |
|------|------|------|
| CRUD | `/courses/` | 课程管理 |
| CRUD | `/sessions/` | 课堂时段管理 |
| POST | `/sessions/{id}/end/` | 结束课堂 |
| POST | `/submit/` | 学生提交反馈 |
| GET | `/statistics/{id}/` | 当前统计数据 |
| GET | `/statistics/{id}/slots/` | 所有时段统计 |
| GET | `/history/` | 历史查询 |
| GET | `/export/{id}/` | 导出 Excel |

### 讨论接口 `/api/discussion/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/messages/{id}/` | 获取消息列表 |
| POST | `/send/` | 发送消息（文字/图片） |

### WebSocket 端点

| 路径 | 用途 |
|------|------|
| `ws/feedback/{session_id}/` | 实时统计推送 |
| `ws/chat/{session_id}/` | 实时聊天 |

---

## 七、部署方案

### 生产环境架构

```
用户浏览器
    │ HTTPS / WSS
    ↓
Cloudflare 边缘节点（全球 CDN + 自动 SSL 证书）
    │ Cloudflare Tunnel（加密隧道）
    ↓
本地机器
    │
    ├── Nginx (端口 80)
    │   ├── / → frontend/dist/          （Vue 静态文件）
    │   ├── /api/ → Daphne (端口 8000)   （REST API）
    │   ├── /ws/ → Daphne               （WebSocket 升级）
    │   ├── /static/ → staticfiles/      （Django 静态文件）
    │   └── /media/ → media/             （上传文件）
    │
    ├── Daphne (端口 8000) — ASGI 服务器
    │   └── 同时处理 HTTP 请求和 WebSocket 连接
    │
    └── MySQL (端口 3306) — 数据库
```

### 服务管理

所有服务通过 **systemd** 管理，开机自启：

| 服务 | 说明 | 命令 |
|------|------|------|
| `nginx` | 反向代理 + 静态文件 | `sudo systemctl start nginx` |
| `classroom-backend` | Daphne 后端 | `sudo systemctl start classroom-backend` |
| `cloudflared` | Cloudflare Tunnel | `sudo systemctl start cloudflared` |

### 安全措施

- 所有敏感配置（SECRET_KEY、数据库密码、OAuth Secret）通过 `.env` 环境变量管理，不提交到代码仓库
- 使用 `git-filter-repo` 清理了历史提交中的敏感信息
- Cloudflare 提供 DDoS 防护和 WAF
- JWT Token 有效期限制（Access 12h / Refresh 7d）

---

## 八、压力测试

使用 **Locust** 模拟 200 个并发用户（190 学生 + 10 教师），测试结果：

### 本地直连测试（绕过 Cloudflare）

| 指标 | 数值 |
|------|------|
| 并发用户 | 200 |
| RPS | 43.86 |
| 失败率 | **0%** |
| 中位响应时间 | 1500ms |
| 95% 响应时间 | 6000ms |

### 经 Cloudflare Tunnel 测试

| 指标 | 数值 |
|------|------|
| 并发用户 | 200 |
| RPS | 39.5 |
| 失败率 | 36%（Tunnel 瓶颈） |
| 中位响应时间 | 180ms |

**结论**：后端本身能稳定支撑 200 并发用户（0% 失败率）。公网 36% 失败率来自 Cloudflare 免费版 Tunnel 的并发连接限制，非代码问题。课堂场景（30-50 人）完全够用。

---

## 九、项目亮点总结

1. **前后端分离 + 实时通信**：Django REST Framework 提供 RESTful API，Django Channels 实现 WebSocket 双向通信，技术栈选型合理

2. **双重数据更新机制**：WebSocket 实时推送 + HTTP 轮询兜底，保证统计数据不丢失

3. **三种 ECharts 可视化图表**：柱状图展示分布、饼状图展示比例、折线图展示趋势，全方位呈现课堂学情

4. **完善的认证体系**：JWT Token + GitHub OAuth 2.0 授权码模式，支持第三方登录和账号绑定

5. **三级角色权限**：学生/教师/管理员，前后端双重校验，路由守卫 + DRF permission_classes

6. **安全部署**：敏感信息环境变量管理、Git 历史清理、Cloudflare Tunnel 无需暴露服务器端口

7. **工程化实践**：压力测试（Locust）、.env 环境变量、systemd 服务管理、.env.example 模板

---

## 十、项目目录结构

```
first_team_work/
├── backend/                     # 后端 Django 项目
│   ├── config/                  # 项目配置
│   │   ├── settings.py          # 全局配置（环境变量）
│   │   ├── urls.py              # URL 根路由
│   │   ├── asgi.py              # ASGI 入口
│   │   ├── routing.py           # WebSocket 路由
│   │   └── middleware.py        # WebSocket JWT 中间件
│   ├── apps/
│   │   ├── users/               # 用户模块（模型、视图、序列化器、权限）
│   │   ├── feedback/            # 反馈模块（模型、视图、Consumer）
│   │   └── discussion/          # 讨论模块（模型、视图、Consumer）
│   ├── .env                     # 环境变量（不入库）
│   ├── .env.example             # 环境变量模板
│   ├── locustfile.py            # 压力测试脚本
│   └── requirements.txt         # Python 依赖
├── frontend/                    # 前端 Vue 3 项目
│   ├── src/
│   │   ├── api/                 # Axios 实例 + JWT 拦截器
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── utils/               # WebSocket 工具（自动重连）
│   │   ├── router/              # Vue Router（角色守卫）
│   │   └── views/               # 页面组件
│   │       ├── Login.vue        # 登录页
│   │       ├── AuthCallback.vue # GitHub OAuth 回调
│   │       ├── student/         # 学生端（仪表盘、讨论）
│   │       ├── teacher/         # 教师端（课堂管理、统计、历史、讨论）
│   │       └── admin/           # 管理端（用户管理）
│   └── vite.config.js           # Vite 配置 + 开发代理
├── docs/                        # 文档
└── .gitignore
```
