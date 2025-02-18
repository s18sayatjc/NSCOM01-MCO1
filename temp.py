# currently working with bin and png
# change server address to tftp address do not use 127...


import os
import socket

# create a function that handles the error codes or prints it in the terminal
def handle_error(errorcode):
    error_dict = {
        0: "Not defined, see error message (if any).",
        1: "File not found.",
        2: "Access violation.",
        3: "Disk full or allocation exceeded.",
        4: "Illegal TFTP operation.",
        5: "Unknown transfer ID.",
        6: "File already exists.",
        7: "No such user.",
     }

def tftp_download(server_ip, remote_filename, local_filename, timeout=5):
    server_address = (server_ip, 69)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    if remote_filename.endswith(".txt"):
        mode = "netascii"
    else:
        mode = "octet"

    rrq = b'\x00\x01' + remote_filename.encode('ascii') + b'\x00' + mode.encode('ascii') + b'\x00'

    sock.sendto(rrq, server_address)
    print(f"Sent RRQ for '{remote_filename}' to {server_address}")
    
    expected_block = 1
    with open(local_filename, 'wb') as f:
        while True:
            try:
                data, addr = sock.recvfrom(516)
                print(f"Received data from {addr}")
            except socket.timeout:
                print("Timeout waiting for response from the server.")
                break
            
            opcode = int.from_bytes(data[:2], byteorder='big')
            print(f"Received opcode: {opcode}")
            if opcode == 3:
                block_num = int.from_bytes(data[2:4], byteorder='big')
                print(f"Received DATA packet, block #{block_num} from {addr}")
                
                if block_num == expected_block:
                    f.write(data[4:])
                    ack = b'\x00\x04' + data[2:4]
                    sock.sendto(ack, addr)
                    print(f"Sent ACK for block #{block_num} to {addr}")
                    
                    expected_block += 1
                    
                    if len(data[4:]) < 512:
                        print("Received final data block.")
                        break
                else:
                    print(f"Unexpected block number: {block_num}. Expected: {expected_block}")
                    break
                    
            elif opcode == 5:
                error_code = int.from_bytes(data[2:4], byteorder='big')
                error_msg = data[4:-1].decode('ascii')
                print(f"Server returned error {error_code}: {error_msg}")
                break
            else:
                print(f"Unknown opcode: {opcode}")
                break

    sock.close()
    print("Download completed.")

if __name__ == "__main__":
    server_ip = "192.168.0.10"
    remote_filename = "test.txt"
    local_filename = "test3.txt"
    
    tftp_download(server_ip, remote_filename, local_filename)