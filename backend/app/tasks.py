import paramiko
import os
from scp import SCPClient

def send_to_runpod(input_file: str, input_id: str, output_dir: str = "storage/outputs") -> str:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 🔧 使用环境变量设置 SSH 密钥路径（默认值为 root）
    key_path = os.getenv("SSH_KEY_PATH", "/root/.ssh/id_ed25519")
    ssh.connect("38.147.83.32", port=32964, username="root", key_filename=key_path)

    # 🔧 修改 remote_input 和 remote_output 路径，使其与 job_id 隔离
    remote_input = f"/workspace/colabfold/input/{input_id}.fasta"
    remote_output = f"/workspace/colabfold/output/{input_id}/"

    # 🔧 创建远程 input/output 子目录（隔离不同 job）
    ssh.exec_command(f"mkdir -p /workspace/colabfold/input /workspace/colabfold/output/{input_id}")

    # 🔧 上传输入文件到远程 input 子目录
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(input_file, remote_input)

    # 🔧 执行预测脚本，并使用 job_id 对应的输入输出路径
    command = (
        f"cd /workspace/colabfold && "
        f"source colabfold-env/bin/activate && "
        f"export JAX_PLATFORM_NAME=cuda && "
        f"colabfold_batch input/{input_id}.fasta output/{input_id}"
    )
    stdin, stdout, stderr = ssh.exec_command(command)
    print(stdout.read().decode(), stderr.read().decode())  # 可选：可用于日志记录

    # 🔧 本地 output 目录按 job_id 创建并下载远程结果
    local_output_path = os.path.join(output_dir, input_id)
    os.makedirs(local_output_path, exist_ok=True)

    with SCPClient(ssh.get_transport()) as scp:
        scp.get(remote_output, local_output_path, recursive=True)

    ssh.close()

    # 🔧 返回本地生成的预测结果路径
    return f"{local_output_path}/ranked_0.pdb"  # 可根据实际文件命名修改


