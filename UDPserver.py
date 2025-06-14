import socket
import base64
import threading
import os
import random
import hashlib

def get_available_port(start, end):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        port = random.randint(start, end)
        try:
            sock.bind(("", port))
            sock.close()
            return port
        except socket.error:
            continue

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def handle_client(client_socket, client_address, filename, data_port):
    try:
        # 检查文件是否存在
        if not os.path.exists(filename):
            response = f"ERR {filename} NOT_FOUND"
            client_socket.sendto(response.encode(), client_address)
            return

        # 获取文件大小
        file_size = os.path.getsize(filename)
        response = f"OK {filename} SIZE {file_size} PORT {data_port}"
        client_socket.sendto(response.encode(), client_address)

        # 创建新的UDP套接字用于数据传输
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data_socket.bind(("", data_port))

        print(f"Client {client_address} requested {filename} (Size: {file_size} bytes). Sending data on port {data_port}.")

        # 打开文件并逐块发送数据
        with open(filename, "rb") as file:
            while True:
                data = file.read(1000)  # 读取1000字节
                if not data:
                    break
                encoded_data = base64.b64encode(data).decode()
                response = f"FILE {filename} OK START {file.tell() - len(data)} END {file.tell() - 1} DATA {encoded_data}"
                data_socket.sendto(response.encode(), client_address)

        # 等待客户端关闭请求
        close_request, _ = data_socket.recvfrom(1024)
        if close_request.decode().startswith(f"FILE {filename} CLOSE"):
            # 计算文件的MD5校验和
            file_md5 = calculate_md5(filename)
            response = f"FILE {filename} CLOSE_OK {file_md5}"
            data_socket.sendto(response.encode(), client_address)
            print(f"File {filename} transfer completed for client {client_address}.")
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        data_socket.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 UDPserver.py <port>")
        return

    server_port = int(sys.argv[1])
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", server_port))

    print(f"Server is listening on port {server_port}")

    while True:
        message, client_address = server_socket.recvfrom(1024)
        client_request = message.decode().strip()

        if client_request.startswith("DOWNLOAD"):
            filename = client_request.split()[1]
            data_port = get_available_port(50000, 51000)  # 获取可用端口
            client_thread = threading.Thread(target=handle_client, args=(server_socket, client_address, filename, data_port))
            client_thread.start()

if __name__ == "__main__":
    import sys
    main()