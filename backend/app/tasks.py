import paramiko
import os
import time  # ✅ 新增：用于实时循环等待
from scp import SCPClient
from celery import Celery

def send_to_runpod(input_file: str, input_id: str, output_dir: str = "storage/outputs") -> str:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 🔧 使用环境变量设置 SSH 密钥路径（默认值为 root）
    key_path = os.getenv("SSH_KEY_PATH", "/root/.ssh/id_ed25519")
    ssh.connect("38.147.83.32", port=19158, username="root", key_filename=key_path)

    # 🔧 修改 remote_input 和 remote_output 路径，使其与 job_id 隔离
    remote_input = f"/workspace/colabfold/input/{input_id}.fasta"
    remote_output = f"/workspace/colabfold/output/{input_id}/"

    # 🔧 创建远程 input/output 子目录（隔离不同 job）
    ssh.exec_command(f"mkdir -p /workspace/colabfold/input /workspace/colabfold/output/{input_id}")

    # 🔧 上传输入文件到远程 input 子目录
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(input_file, remote_input)

        # ✅ 替换原来的 exec_command + read 为 invoke_shell 实时输出
    command = (
        f"cd /workspace/colabfold && "
        f"source colabfold-env/bin/activate && "
        f"export JAX_PLATFORM_NAME=cuda && "
        f"colabfold_batch input/{input_id}.fasta output/{input_id}"
    )

    #stdin, stdout, stderr = ssh.exec_command(command)
    #print(stdout.read().decode(), stderr.read().decode())  # 可选：可用于日志记录
    stdin, stdout, stderr = ssh.exec_command(command)
    channel = stdout.channel

    output_buffer = ""
    while True:
        if channel.recv_ready():
            chunk = channel.recv(1024).decode("utf-8")
            print(chunk, end="")
            output_buffer += chunk  # 👈 可选：用于后续分析日志
        if channel.exit_status_ready():
            # ✅ 等待所有输出读取完毕
            if not channel.recv_ready():
                break
        time.sleep(0.2)  # 👈 减少CPU占用

    exit_status = channel.recv_exit_status()  # ✅ 确保命令完成

    # ✅ 下载前再 Sleep 一下，确保文件写入完成
    time.sleep(1.0)


    # 🔧 本地 output 目录按 job_id 创建并下载远程结果
    local_output_path = os.path.join(output_dir, input_id)
    os.makedirs(local_output_path, exist_ok=True)

    with SCPClient(ssh.get_transport()) as scp:
        scp.get(remote_output, local_output_path, recursive=True)

    ssh.close()

    # 🔧 返回本地生成的预测结果路径
    return f"{local_output_path}/{input_id}/ExampleProtein.done.txt"  # 可根据实际文件命名修改



celery_app = Celery(
    "predict",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

@celery_app.task
def run_prediction(input_path: str, job_id: str):
    return send_to_runpod(input_path, job_id)