# 课堂学情监控管理系统

> 面向高校课堂的实时学情监控平台 — 学生发送表情反馈，教师实时查看聚合统计

![](https://img.shields.io/badge/Python-3.12+-blue.svg)
![](https://img.shields.io/badge/Django-4.2-green.svg)
![](https://img.shields.io/badge/Vue-3.5-42b883.svg)
![](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 功能特性

### 学生端
- 查看当前进行中的课堂
- 选择 6 种表情（😫😟😐🙂😊🤩）反馈对课程内容的理解程度
- 实时讨论区（文字 + 图片）

### 教师端
- 课程管理（创建/编辑/删除）
- 开始/结束课堂时段
- **实时统计看板**：参与人数、平均分、方差、柱状图、饼状图、折线图
- 历史查询与 Excel 导出
- 实时讨论区

### 管理员端
- 用户 CRUD（学生/教师/管理员）
- 角色筛选 + 关键字搜索
- GitHub OAuth 绑定状态展示

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Django 4.2 + Django REST Framework + Django Channels |
| 前端 | Vue 3 + Vite + Element Plus + ECharts + Pinia |
| 认证 | JWT (SimpleJWT) + GitHub OAuth 2.0 |
| 数据库 | MySQL / SQLite |
| 实时通信 | WebSocket (Django Channels) |
| 部署 | Nginx + Daphne + Cloudflare Tunnel |

详细技术报告：[docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md)

---

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 18+
- MySQL 8.x（可选，开发用 SQLite）

### 1. 克隆项目

```bash
git clone https://github.com/yowakkojay/classroom-feedback-system.git
cd classroom-feedback-system
```

### 2. 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env           # 编辑 .env 填入真实密钥

# 数据库迁移
python manage.py migrate
python manage.py createsuperuser

# 启动开发服务器（仅 HTTP）
python manage.py runserver

# 或启动 ASGI 服务器（支持 WebSocket）
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 3. 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 4. 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |
| 教师 | `ywj` | `ywj123` |

---

## API 接口

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login/` | 密码登录 |
| POST | `/api/auth/github/` | GitHub OAuth |
| GET | `/api/auth/me/` | 当前用户信息 |
| CRUD | `/api/auth/users/` | 用户管理（管理员） |

### 反馈

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/feedback/submit/` | 提交表情反馈 |
| GET | `/api/feedback/statistics/{id}/` | 获取统计数据 |
| GET | `/api/feedback/history/` | 历史查询 |
| GET | `/api/feedback/export/{id}/` | 导出 Excel |

### 讨论

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/discussion/messages/{id}/` | 消息列表 |
| POST | `/api/discussion/send/` | 发送消息 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `ws/feedback/{session_id}/` | 实时统计推送 |
| `ws/chat/{session_id}/` | 实时聊天 |

---

## 项目结构

```
backend/
├── config/               # Django 项目配置
│   ├── settings.py       # 环境变量配置
│   ├── asgi.py          # ASGI 入口
│   ├── routing.py        # WebSocket 路由
│   └── middleware.py     # WebSocket JWT 中间件
├── apps/
│   ├── users/           # 用户、认证、GitHub OAuth
│   ├── feedback/        # 课程、课堂、表情反馈、统计
│   └── discussion/      # 讨论区、聊天
├── locustfile.py        # 压力测试脚本
├── .env                 # 环境变量（不入库）
└── .env.example         # 环境变量模板

frontend/src/
├── api/                 # Axios 实例 + JWT 拦截器
├── stores/             # Pinia 用户状态
├── utils/              # WebSocket 工具（自动重连）
├── router/             # Vue Router + 角色守卫
└── views/
    ├── student/        # 学生仪表盘、讨论区
    ├── teacher/        # 课堂管理、统计、历史、讨论区
    └── admin/          # 用户管理
```

---

## 压力测试

使用 Locust 模拟 200 并发用户：

```bash
cd backend
source venv/bin/activate
pip install locust
locust --host=http://127.0.0.1 --web-port=8089
```

结果：**0% 失败率**，中位响应时间 ~1.5s，能稳定支撑 200 并发用户。

---

## 部署

项目已配置 Cloudflare Tunnel + Nginx + Daphne 生产架构，详见 [PROJECT_REPORT.md](docs/PROJECT_REPORT.md#七部署方案)。

---

## License

MIT
