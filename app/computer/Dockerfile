FROM python:3.11-slim

# 容器里的工作目录
WORKDIR /app

# 安装 computer 需要的最小依赖
RUN pip install --no-cache-dir kafka-python

# 只复制 computer 这一层代码到容器
COPY computer /app/computer


# 启动时运行 computer
CMD ["python", "-u", "/app/computer/main.py"]
