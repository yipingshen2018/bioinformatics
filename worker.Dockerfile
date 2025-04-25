FROM ghcr.io/sokrypton/colabfold:1.5.5-cuda12.2.2

WORKDIR /app

# 拷贝整个 app（包括 tasks.py、utils.py、predict.py 等等）
COPY ./backend/app /app

# 安装 Celery + Redis client
RUN pip install celery redis scp paramiko

# 设置默认的 Celery 启动命令
# 注意 -A 应该指向含有 celery_app 的模块（即 tasks）
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
