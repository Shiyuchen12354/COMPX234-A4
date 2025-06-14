import socket
import base64
import sys
import time

def send_and_receive(sock, address, message, timeout=1):
    sock.settimeout(timeout)
    try:
        sock.sendto(message.encode(), address)
        response, _ = sock.recvfrom(4096)
        return response.decode()
    except socket.timeout:
        return None

def download_file(server_address, port, filename):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (server_address, port)
    
    # 发送下载请求
    download_request = f"DOWNLOAD {filename}"
    response = send_and_receive(client_socket, server_address, download_request)
    
    if response is None:
        print("Request timed out")
        return
    
    # 解析响应
    parts = response.split()
    if parts[0] == "OK":
        file_size = int(parts[3])
        data_port = int(parts[5])
        print(f"File size: {file_size}, Data port: {data_port}")
        
        # 创建文件用于写入
        with open(filename, "wb") as file:
            start = 0
            while start < file_size:
                # 发送数据请求
                end = min(start + 1000, file_size - 1)
                data_request = f"FILE {filename} GET START {start} END {end}"
                response = send_and_receive(client_socket, (server_address[0], data_port), data_request)
                
                if response is None:
                    print("Data request timed out")
                    return
                
                # 解析数据响应
                parts = response.split()
                if parts[0] == "FILE" and parts[2] == "OK":
                    encoded_data = parts[6]
                    decoded_data = base64.b64decode(encoded_data)
                    file.seek(start)
                    file.write(decoded_data)
                    start = end + 1
                    print("*", end="", flush=True)
        
        # 发送关闭请求
        close_request = f"FILE {filename} CLOSE"
        response = send_and_receive(client_socket, (server_address[0], data_port), close_request)
        
        if response and response.split()[2] == "CLOSE_OK":
            print(f"\nFile {filename} downloaded successfully")
        else:
            print(f"Failed to close file {filename}")
    elif parts[0] == "ERR":
        print(f"Error: {response}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 UDPclient.py <hostname> <port> <files.txt>")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    file_list_path = sys.argv[3]
    
    with open(file_list_path, "r") as file_list:
        filenames = file_list.read().splitlines()
    
    for filename in filenames:
        download_file(server_host, server_port, filename)