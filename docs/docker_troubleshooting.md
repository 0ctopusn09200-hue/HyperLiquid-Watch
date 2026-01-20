# Docker 故障排查指南

## 问题：pnpm-lock.yaml 过期错误

### 错误信息
```
ERR_PNPM_OUTDATED_LOCKFILE  Cannot install with "frozen-lockfile" because pnpm-lock.yaml is not up to date with package.json
```

### 解决方案

#### 方案1: 优先使用npm（推荐，已修复）

项目中有 `package-lock.json`，Dockerfile 已更新为优先使用 npm。直接重新构建即可：

```bash
cd app
docker-compose build frontend
docker-compose up -d
```

#### 方案2: 更新pnpm-lock.yaml

如果你想使用pnpm，需要在本地更新锁文件：

```bash
cd app/frontend

# 安装pnpm（如果没有）
npm install -g pnpm

# 更新锁文件
pnpm install

# 然后重新构建
cd ..
docker-compose build frontend
docker-compose up -d
```

#### 方案3: 删除pnpm-lock.yaml

如果项目实际使用的是npm，可以删除pnpm-lock.yaml：

```bash
cd app/frontend
rm pnpm-lock.yaml
git add .
git commit -m "Remove outdated pnpm-lock.yaml"

# 重新构建
cd ..
docker-compose build frontend
docker-compose up -d
```

---

## 其他常见问题

### 端口被占用

```bash
# 查看占用端口的进程
lsof -i :8080
lsof -i :3000
lsof -i :5432

# 停止进程
kill -9 <PID>
```

### 容器启动失败

```bash
# 查看详细日志
docker-compose logs frontend
docker-compose logs backend

# 重新构建（不缓存）
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### 数据库连接失败

```bash
# 确保postgres先启动
docker-compose up -d postgres

# 等待15-20秒
sleep 20

# 测试连接
docker-compose exec postgres psql -U postgres -d hyperliquid -c "SELECT 1"

# 然后启动backend
docker-compose up -d backend
```

### 内存不足

```bash
# 查看Docker资源使用
docker stats

# 在Docker Desktop中增加内存分配
# Settings → Resources → Memory (至少4GB)
```

### 清理Docker缓存

```bash
# 清理未使用的镜像
docker image prune -a

# 清理所有未使用的资源
docker system prune -a

# 清理构建缓存
docker builder prune
```

---

## 验证步骤

构建成功后，验证所有服务：

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 检查前端
curl http://localhost:3000

# 3. 检查后端
curl http://localhost:8080/health

# 4. 查看日志
docker-compose logs -f
```
