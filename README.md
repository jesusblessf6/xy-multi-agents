# XY Multi-Agents

多Agent协作的AI Native软件开发流水线。8个专职Agent在PM Agent协调下完成完整开发流程。

## 架构

```
客户需求 → 售前 → [需求审核] → [需求可行性评审] → 产品 → [PRD评审] → 设计 → [设计评审]
    → 架构 → [架构评审] → 前端+后端(并行) → 测试 → [用例评审] → 测试执行 → 交付
                                    ↖ PM Agent 全程协调 ↗
```

**前台(Portal)** — 需求提交 + 进度查看 (React :3000 → API :8001)
**后台(Console)** — 知识管理 + 评审审批 (Vue 3 :3001 → API :8002)
**核心引擎** — `src/xy_core/` 状态机、Agent注册、评审门
**CLI** — `xy-cli.py` 命令行操作

## 部署

### 方式一：本地开发

#### 1. 环境准备

```bash
# 需要 Python 3.12+ 和 Node.js 20+
python --version   # >= 3.12
node --version     # >= 20

# 创建 Python 虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装 Python 包 (核心引擎 + 开发依赖)
pip install -e ".[dev]"
```

#### 2. 初始化数据库

```bash
PYTHONPATH=. python -m console.server.seed
```

这会创建 SQLite 数据库 `console/data/console.db` 并写入种子用户。

#### 3. 安装前端依赖

```bash
cd portal/web && npm install
cd ../../console/web && npm install
```

#### 4. 启动服务

需要 4 个终端，每个终端先激活虚拟环境 (`source .venv/bin/activate`)：

```bash
# 终端 1: Portal API (:8001)
PYTHONPATH=. uvicorn portal.server.main:app --port 8001 --reload

# 终端 2: Console API (:8002)
PYTHONPATH=. uvicorn console.server.main:app --port 8002 --reload

# 终端 3: Portal 前端 (:3000)
cd portal/web && npx vite --port 3000

# 终端 4: Console 前端 (:3001)
cd console/web && npx vite --port 3001
```

> `--reload` 启用热重载，开发时代码修改自动生效。生产环境去掉 `--reload`。

#### 5. 访问

| 服务 | 地址 |
|------|------|
| Portal 前端 | http://localhost:3000 |
| Console 前端 | http://localhost:3001 |
| Portal API | http://localhost:8001 |
| Console API | http://localhost:8002 |
| API 文档 (Portal) | http://localhost:8001/docs |
| API 文档 (Console) | http://localhost:8002/docs |

#### 前端代理说明

开发模式下，Vite 开发服务器自动代理 API 请求，无需额外配置：
- Portal 前端 (`portal/web/vite.config.ts`) 将 `/requirements`、`/projects`、`/pipeline`、`/agents` 代理到 `:8001`
- Console 前端 (`console/web/vite.config.ts`) 将 `/auth`、`/agents`、`/reviews`、`/projects`、`/dashboard`、`/users` 代理到 `:8002`

### 方式二：Docker Compose

#### 1. 环境准备

只需安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)。

#### 2. 启动

```bash
docker compose up --build
```

首次启动会构建 4 个镜像，后续启动使用缓存。加 `-d` 后台运行：

```bash
docker compose up --build -d
```

#### 3. 初始化数据库

首次启动后需要初始化数据库：

```bash
docker compose exec console-api python -m console.server.seed
```

#### 4. 访问

| 服务 | 地址 |
|------|------|
| Portal 前端 | http://localhost:3000 |
| Console 前端 | http://localhost:3001 |
| Portal API | http://localhost:8001 |
| Console API | http://localhost:8002 |

#### 5. 常用命令

```bash
# 查看日志
docker compose logs -f

# 只看某个服务日志
docker compose logs -f portal-api
docker compose logs -f console-api

# 停止
docker compose down

# 停止并清除数据卷 (数据库会被删除)
docker compose down -v

# 重新构建某个服务
docker compose up --build portal-api
```

#### Docker Compose 服务说明

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| portal-api | Dockerfile.portal | 8001:8001 | 前台 API，无认证 |
| console-api | Dockerfile.console | 8002:8002 | 后台 API，JWT+RBAC |
| portal-web | portal/web/Dockerfile | 3000:80 | 前台前端，Nginx 托管 + API 代理 |
| console-web | console/web/Dockerfile | 3001:80 | 后台前端，Nginx 托管 + API 代理 |

> 前端 Docker 镜像使用多阶段构建：Node.js 编译 → Nginx 托管。Nginx 负责前端路由 (SPA fallback) 和 API 反向代理。

#### 数据持久化

- `console-data` Docker 卷：存储 SQLite 数据库
- 项目数据 (`projects/`)、Agent 配置 (`agents/`)、流水线配置 (`config/`) 通过卷挂载到容器内

### 方式三：生产部署

#### 架构建议

```
                    ┌── Nginx/Caddy (反向代理 + TLS) ──┐
                    │                                   │
           :443/portal → portal-web (:80)              │
           :443/portal/api → portal-api (:8001)        │
           :443/console → console-web (:80)            │
           :443/console/api → console-api (:8002)      │
                    │                                   │
                    └───────────────────────────────────┘
```

#### 步骤

**1. 构建前端产物**

```bash
cd portal/web && npm install && npm run build    # 产物在 dist/
cd ../../console/web && npm install && npm run build  # 产物在 dist/
```

**2. 构建 API 镜像**

```bash
docker build -f Dockerfile.portal -t xy-portal-api .
docker build -f Dockerfile.console -t xy-console-api .
```

**3. 运行 API 容器**

```bash
docker run -d \
  --name portal-api \
  -p 8001:8001 \
  -v $(pwd)/projects:/app/projects \
  -v $(pwd)/agents:/app/agents \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/templates:/app/templates \
  -e XY_WORKSPACE=/app \
  xy-portal-api

docker run -d \
  --name console-api \
  -p 8002:8002 \
  -v $(pwd)/projects:/app/projects \
  -v $(pwd)/agents:/app/agents \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/templates:/app/templates \
  -v console-data:/app/data \
  -e XY_WORKSPACE=/app \
  xy-console-api
```

**4. 初始化数据库**

```bash
docker exec console-api python -m console.server.seed
```

**5. 配置反向代理**

Nginx 示例 (将两个前端和两个 API 统一入口)：

```nginx
server {
    listen 443 ssl;
    server_name xy.example.com;

    # Portal 前端
    location / {
        root /usr/share/nginx/portal;
        try_files $uri $uri/ /index.html;
    }

    # Portal API
    location /portal/api/ {
        rewrite ^/portal/api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:8001;
    }

    # Console 前端
    location /console/ {
        alias /usr/share/nginx/console/;
        try_files $uri $uri/ /console/index.html;
    }

    # Console API
    location /console/api/ {
        rewrite ^/console/api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:8002;
    }
}
```

> 生产部署时需要修改 Console API 的 JWT 密钥。设置环境变量 `JWT_SECRET_KEY` 或直接修改 `console/server/services/auth_service.py`。

#### 安全注意事项

- **JWT 密钥**：生产环境务必替换默认密钥，通过环境变量 `JWT_SECRET_KEY` 设置
- **CORS**：生产环境需修改 API 中的 CORS 配置，限制为实际域名
- **HTTPS**：强烈建议通过反向代理启用 TLS
- **Console 数据库**：SQLite 适合小团队，大规模使用建议迁移到 PostgreSQL

## 种子用户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| presales_user | 123456 | 售前顾问 |
| product_user | 123456 | 产品经理 |
| architect_user | 123456 | 架构师 |
| design_user | 123456 | 设计师 |
| qa_user | 123456 | 测试工程师 |
| dev_user | 123456 | 前端+后端 |

> 生产环境请务必修改默认密码。

## CLI 命令

```bash
xy create <name> [--client X] [--desc X] [--requirement TEXT]
xy status <name>
xy advance <name>
xy review <name> <gate> --approve/--reject --reviewer ROLE [--comments X]
xy run <name> <agent>          # 输出构建的Agent prompt
xy agents
xy pipeline
```

## 目录结构

```
xy-multi-agents/
├── src/xy_core/            # 核心引擎 (Python包)
├── portal/                 # 前台
│   ├── server/             #   FastAPI (:8001), 无认证
│   └── web/                #   React (:3000)
├── console/                # 后台
│   ├── server/             #   FastAPI (:8002), JWT+RBAC
│   └── web/                #   Vue 3 (:3001)
├── engine/                 # 参考原型 (不修改)
├── agents/                 # 8个Agent配置+Skills+RAG
├── projects/               # 项目实例 (共享工作区)
├── config/pipeline.yaml    # 流水线定义
├── templates/project/      # 项目模板
├── docs/                   # 规划文档
├── tests/                  # 单元测试
├── xy-cli.py               # CLI入口
└── docker-compose.yml
```

## API 概览

### Portal API (:8001) — 无认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /requirements | 提交需求，创建项目 |
| GET | /projects | 项目列表 |
| GET | /projects/{name} | 项目详情 |
| GET | /pipeline | 流水线定义 |
| GET | /agents | Agent列表 |

### Console API (:8002) — JWT + RBAC
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 登录 |
| GET | /auth/me | 当前用户+角色 |
| GET/PUT/DELETE | /agents/{name}/skills/{skill} | Skill CRUD |
| GET/PUT/DELETE | /agents/{name}/rag/{doc} | RAG CRUD |
| GET | /reviews/pending | 待审列表 |
| POST | /reviews/{project}/{gate} | 提交审批 |
| GET | /dashboard | 聚合视图 |
| GET/POST/PUT/DELETE | /users/... | 用户管理(admin) |

## 测试

```bash
pytest tests/ -v
```
