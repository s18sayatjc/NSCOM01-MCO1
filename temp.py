import socket

def tftp_download(server_ip, remote_filename, local_filename, timeout=5):
    # TFTP server uses UDP port 69 for initial requests.
    server_address = (server_ip, 69)
    
    # Create a UDP socket.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    # Build the TFTP Read Request (RRQ) packet.
    # Format: | Opcode (2 bytes) | Filename (string) | 0 | Mode (string) | 0 |
    mode = "octet"  # Binary mode
    rrq = b'\x00\x01' + remote_filename.encode('ascii') + b'\x00' + mode.encode('ascii') + b'\x00'
    
    # Send the RRQ to the server.
    sock.sendto(rrq, server_address)
    print(f"Sent RRQ for '{remote_filename}' to {server_address}")
    
    expected_block = 1  # TFTP data blocks start at 1
    with open(local_filename, 'wb') as f:
        while True:
            try:
                # TFTP data packets are at most 516 bytes (2 opcode + 2 block number + 512 data)
                data, addr = sock.recvfrom(516)
            except socket.timeout:
                print("Timeout waiting for response from the server.")
                break
            
            # Parse the received packet.
            opcode = int.from_bytes(data[:2], byteorder='big')
            
            if opcode == 3:  # DATA packet
                block_num = int.from_bytes(data[2:4], byteorder='big')
                print(f"Received DATA packet, block #{block_num} from {addr}")
                
                if block_num == expected_block:
                    # Write the data part (after the first 4 bytes) to file.
                    f.write(data[4:])
                    
                    # Send an ACK for this block.
                    ack = b'\x00\x04' + data[2:4]  # Opcode 4 for ACK.
                    sock.sendto(ack, addr)
                    print(f"Sent ACK for block #{block_num} to {addr}")
                    
                    expected_block += 1
                    
                    # The final data packet is less than 512 bytes.
                    if len(data[4:]) < 512:
                        print("Received final data block.")
                        break
                else:
                    print(f"Unexpected block number: {block_num}. Expected: {expected_block}")
                    break
                    
            elif opcode == 5:  # ERROR packet
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
    # Replace these values with your server IP and file details.
    server_ip = "127.0.0.1"  # TFTPD64 server IP
    remote_filename = "example.txt"  # File to download from the server
    local_filename = "downloaded_example.txt"  # Local filename to save the data
    
    tftp_download(server_ip, remote_filename, local_filename)
