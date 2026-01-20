# 🚀 快速启动指南 (Mac)

## 第一步：安装Docker Desktop

1. 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. 启动Docker Desktop应用
3. 验证安装：
   ```bash
   docker --version
   docker-compose --version
   ```

## 第二步：启动项目

```bash
# 1. 进入项目目录
cd /Users/zhangyunan/Downloads/ave_internship_course_hyperliquid-main/app

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志（可选）
docker-compose logs -f
```

## 第三步：初始化数据库（首次运行）

```bash
# 等待PostgreSQL启动（约15秒）
sleep 15

# 初始化数据库schema
docker-compose run --rm backend python init_db.py
```

## 第四步：访问应用

- **前端界面**: http://localhost:3000
- **后端API文档**: http://localhost:8080/docs
- **健康检查**: http://localhost:8080/health

## 常用命令

```bash
# 停止所有服务
docker-compose down

# 重启某个服务
docker-compose restart backend

# 查看日志
docker-compose logs -f backend

# 完全重置（删除所有数据）
docker-compose down -v
```

## 遇到问题？

详细文档请查看: `docs/docker_setup_guide.md`
