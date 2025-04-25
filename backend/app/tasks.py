import paramiko
import os
from scp import SCPClient


def send_to_runpod(input_file: str, output_dir: str =  "storage/outputs") -> str:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key_path = os.getenv("SSH_KEY_PATH", "/root/.ssh/id_ed25519")
    ssh.connect("38.147.83.32", port=41883, username="root", key_filename=key_path)
  

    remote_input = f"/workspace/colabfold/input.fasta"
    remote_output = f"/workspace/colabfold/output/"

    # 上传文件
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(input_file, remote_input)

    # 执行预测脚本
    stdin, stdout, stderr = ssh.exec_command(
        f"cd /workspace/colabfold && source colabfold-env/bin/activate && export JAX_PLATFORM_NAME=cuda && colabfold_batch input.fasta output/"
    )
    print(stdout.read().decode(), stderr.read().decode())

    # 下载结果
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(remote_output, output_dir, recursive=True)

    ssh.close()
    return f"{output_dir}/result_model_1.pdb"

