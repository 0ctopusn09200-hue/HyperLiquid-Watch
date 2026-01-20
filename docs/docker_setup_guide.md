# Mac上使用Docker运行项目详细指南

本文档提供在Mac上使用Docker运行Hyperliquid数据分析项目的完整步骤。

## 📋 前置要求

### 1. 安装Docker Desktop for Mac

1. **下载Docker Desktop**
   - 访问: https://www.docker.com/products/docker-desktop/
   - 选择 "Download for Mac"
   - 根据你的Mac芯片类型选择：
     - **Apple Silicon (M1/M2/M3)**: 下载 Apple Chip 版本
     - **Intel**: 下载 Intel Chip 版本

2. **安装Docker Desktop**
   - 双击下载的 `.dmg` 文件
   - 将Docker图标拖到Applications文件夹
   - 打开Applications中的Docker应用
   - 完成初始设置（需要输入管理员密码）

3. **验证安装**
   打开终端（Terminal），运行：
   ```bash
   docker --version
   docker-compose --version
   ```
   
   应该看到类似输出：
   ```
   Docker version 24.x.x
   Docker Compose version v2.x.x
   ```

4. **启动Docker Desktop**
   - 确保Docker Desktop应用正在运行
   - 菜单栏应该显示Docker图标（鲸鱼图标）
   - 点击图标确认状态为 "Docker Desktop is running"

---

## 🚀 快速开始

### 步骤1: 检查项目文件

确保项目文件完整，进入项目目录：
```bash
cd /Users/zhangyunan/Downloads/ave_internship_course_hyperliquid-main/app
```

检查关键文件是否存在：
```bash
ls -la docker-compose.yml
ls -la backend/Dockerfile
ls -la frontend/Dockerfile
```

### 步骤2: 初始化数据库（首次运行）

如果数据库是空的，需要初始化schema。有两种方式：

**方式1: 使用Docker执行初始化（推荐）**
```bash
# 先启动postgres服务
docker-compose up -d postgres

# 等待postgres完全启动（约10-15秒）
sleep 15

# 初始化数据库schema
docker-compose run --rm backend python init_db.py
```

**方式2: 手动执行（如果方式1不工作）**
```bash
# 启动postgres
docker-compose up -d postgres

# 等待启动后，进入postgres容器
docker-compose exec postgres psql -U postgres -d hyperliquid

# 在psql中执行（复制docs/database_schema.sql的内容）
\i /path/to/database_schema.sql
```

或者直接从文件执行：
```bash
docker-compose exec -T postgres psql -U postgres -d hyperliquid < ../docs/database_schema.sql
```

### 步骤3: 启动所有服务

```bash
# 在app目录下执行
docker-compose up -d
```

这会启动以下服务：
- ✅ PostgreSQL (端口 5432)
- ✅ Zookeeper (端口 2181)
- ✅ Kafka (端口 9092)
- ✅ Flink JobManager (端口 8081)
- ✅ Flink TaskManager
- ✅ Backend API (端口 8080)
- ✅ Frontend (端口 3000)

### 步骤4: 查看服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 应该看到所有服务状态为 "Up"
```

### 步骤5: 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只看某个服务的日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 步骤6: 验证服务

**验证Backend API:**
```bash
# 健康检查
curl http://localhost:8080/health

# 查看API文档
# 在浏览器打开: http://localhost:8080/docs
```

**验证Frontend:**
```bash
# 在浏览器打开: http://localhost:3000
```

**验证PostgreSQL:**
```bash
docker-compose exec postgres psql -U postgres -d hyperliquid -c "\dt"
```

**验证Kafka:**
```bash
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

---

## 🛠️ 常用操作

### 停止所有服务
```bash
docker-compose down
```

### 停止并删除数据卷（清除数据）
```bash
docker-compose down -v
```

### 重启某个服务
```bash
docker-compose restart backend
docker-compose restart frontend
```

### 查看资源使用情况
```bash
docker stats
```

### 进入容器内部调试
```bash
# 进入backend容器
docker-compose exec backend bash

# 进入postgres容器
docker-compose exec postgres psql -U postgres -d hyperliquid

# 进入kafka容器
docker-compose exec kafka bash
```

---

## 🔧 常见问题排查

### 问题1: 端口被占用

**错误信息:**
```
Error: bind: address already in use
```

**解决方法:**
```bash
# 查看端口占用
lsof -i :8080  # Backend端口
lsof -i :3000  # Frontend端口
lsof -i :5432  # PostgreSQL端口

# 停止占用端口的进程
kill -9 <PID>

# 或者修改docker-compose.yml中的端口映射
```

### 问题2: 容器启动失败

**查看详细错误:**
```bash
# 查看特定服务的日志
docker-compose logs backend
docker-compose logs frontend

# 查看所有失败的容器
docker-compose ps
```

**常见原因和解决:**
- **数据库连接失败**: 等待postgres完全启动后再启动backend
- **内存不足**: 增加Docker Desktop的内存分配（Settings → Resources）
- **磁盘空间不足**: 清理Docker镜像和容器

### 问题3: Backend无法连接数据库

**错误信息:**
```
psycopg2.OperationalError: could not connect to server
```

**解决方法:**
```bash
# 1. 确保postgres已启动
docker-compose ps postgres

# 2. 等待postgres完全就绪
docker-compose up -d postgres
sleep 15

# 3. 测试数据库连接
docker-compose exec postgres psql -U postgres -d hyperliquid -c "SELECT 1"

# 4. 重启backend
docker-compose restart backend
```

### 问题4: Frontend无法连接Backend API

**检查环境变量:**
```bash
# 检查frontend容器的环境变量
docker-compose exec frontend env | grep NEXT_PUBLIC

# 应该是:
# NEXT_PUBLIC_API_URL=http://localhost:8080
# NEXT_PUBLIC_WS_URL=ws://localhost:8080/api/v1/ws
```

**解决方法:**
```bash
# 重新构建frontend（如果环境变量改变了）
docker-compose build frontend
docker-compose up -d frontend
```

### 问题5: WebSocket连接失败

**检查Backend WebSocket端点:**
```bash
# 在浏览器控制台测试
# 打开浏览器开发者工具，运行:
const ws = new WebSocket('ws://localhost:8080/api/v1/ws');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
```

**解决方法:**
- 确认backend服务正常运行
- 检查防火墙设置
- 确认WebSocket路径正确: `/api/v1/ws`

### 问题6: Kafka连接失败

**检查Kafka状态:**
```bash
docker-compose logs kafka
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

**解决方法:**
```bash
# 重启kafka和zookeeper
docker-compose restart zookeeper kafka
```

### 问题7: Docker Desktop启动慢或卡住

**解决方法:**
1. 重启Docker Desktop
2. 检查系统资源使用情况
3. 在Docker Desktop设置中增加资源分配：
   - 打开Docker Desktop
   - Settings → Resources
   - 增加Memory到至少4GB
   - 增加CPU核心数

---

## 📊 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| Frontend | http://localhost:3000 | Web界面 |
| Backend API | http://localhost:8080 | REST API |
| API文档 | http://localhost:8080/docs | Swagger UI |
| WebSocket | ws://localhost:8080/api/v1/ws | 实时数据流 |
| Flink UI | http://localhost:8081 | Flink管理界面 |
| PostgreSQL | localhost:5432 | 数据库（需要客户端） |
| Kafka | localhost:9092 | Kafka broker |

---

## 🔄 开发模式

### 修改代码后重新构建

**Backend代码修改:**
```bash
# Backend使用volume挂载，修改代码后自动生效
# 只需重启服务
docker-compose restart backend
```

**Frontend代码修改:**
```bash
# 需要重新构建
docker-compose build frontend
docker-compose up -d frontend

# 或者使用开发模式（需要修改docker-compose.yml）
```

### 查看实时日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 只看错误日志
docker-compose logs --tail=100 | grep -i error
```

---

## 🗑️ 清理和维护

### 清理未使用的容器和镜像
```bash
# 清理停止的容器
docker container prune

# 清理未使用的镜像
docker image prune

# 清理所有未使用的资源
docker system prune -a
```

### 完全重置项目
```bash
# 停止所有服务并删除数据
docker-compose down -v

# 清理所有相关镜像
docker-compose down --rmi all

# 重新构建并启动
docker-compose build
docker-compose up -d
```

---

## ✅ 验证清单

启动后，确认以下项目：

- [ ] Docker Desktop正在运行
- [ ] 所有容器状态为 "Up"
- [ ] Frontend可访问: http://localhost:3000
- [ ] Backend API可访问: http://localhost:8080/health
- [ ] API文档可访问: http://localhost:8080/docs
- [ ] 数据库连接正常
- [ ] Kafka服务正常
- [ ] WebSocket连接正常

---

## 📝 完整启动流程总结

```bash
# 1. 进入项目目录
cd /Users/zhangyunan/Downloads/ave_internship_course_hyperliquid-main/app

# 2. 启动基础服务（PostgreSQL, Kafka等）
docker-compose up -d postgres zookeeper kafka

# 3. 等待基础服务启动（约20秒）
sleep 20

# 4. 初始化数据库（首次运行）
docker-compose run --rm backend python init_db.py

# 5. 启动所有服务
docker-compose up -d

# 6. 查看服务状态
docker-compose ps

# 7. 查看日志
docker-compose logs -f

# 8. 在浏览器访问
# Frontend: http://localhost:3000
# Backend API: http://localhost:8080/docs
```

---

## 💡 提示

1. **首次启动较慢**: 第一次运行需要下载镜像和构建，可能需要5-10分钟
2. **资源要求**: 建议Mac至少有8GB内存和10GB可用磁盘空间
3. **网络问题**: 如果下载镜像慢，可以配置Docker镜像加速器
4. **数据持久化**: PostgreSQL数据存储在Docker volume中，删除容器不会丢失数据（除非使用`-v`参数）

---

## 🆘 需要帮助？

如果遇到问题：
1. 检查服务日志: `docker-compose logs <service-name>`
2. 查看容器状态: `docker-compose ps`
3. 查看Docker Desktop日志
4. 参考本文档的"常见问题排查"部分
