# @author: DreiZzzzz
# last updated: Feb 18, 2025 

import socket

# ask user to input server address and validate if the input is valid
def ask_address():
    while True:
        try:
            host = input("ENTER SERVER ADDRESS: ")  # ask user to input server address
            # checks if the input is valid
            if host.count('.') != 3 or host.endswith('.'):
                raise ValueError("Invalid IP address format")
            port = 69  # default port number for TFTP
            return (host, port)  # return the host and port number
        except Exception as e:
            print("Error:", e)  # print error message

# display the operations a client can do
def display_menu() -> int:
    while True:
        print("-- TFTP CLIENT --")
        print("1. Read file")
        print("2. Write file")
        print("3. Exit Program")
        choice = input("Enter choice: ")
        
        if choice not in ['1', '2', '3']:
            print("Invalid choice. Please try again.")
        else:
            break

    return int(choice)

# display the appropriate error message
def display_error(errorcode: int) -> str:
    tftp_errors = {
        0: "Not defined, see error message (if any).",
        1: "File not found.",
        2: "Access violation.",
        3: "Disk full or allocation exceeded.",
        4: "Illegal TFTP operation.",
        5: "Unknown transfer ID.",
        6: "File already exists.",
        7: "No such user."
    }
    return f"Error code {errorcode}: {tftp_errors[errorcode]}"  # return the error message

# WRQ(2)
def tftp_upload(sock, server_address): 
    print("-- UPLOAD FILE (WRQ) --")
    upload_file_name = input("NAME OF FILE TO UPLOAD: ")
    custom_file_name = input("CUSTOM FILE NAME WHEN UPLOADED IN THE SERVER: ")

    print("NEGOTIATION OPTIONS")

    wrq = ""
    sock.sendto(wrq, server_address)
    # t-size
    # block size
    #etc


# implement this first
# RRQ(1)
def tftp_download(sock, server_address):
    print("-- DOWNLOAD FILE (RRQ) --")
    download_file_name = input("NAME OF FILE TO DOWNLOAD: ")
    print("Note: ./ => retain original name")
    custom_file_name = input("CUSTOM FILE NAME WHEN DOWNLOADED LOCALLY: ")
    file_name = "" # name of the file when downloaded locally

    if custom_file_name.startswith("./"):
        file_name = download_file_name  # Keep original name
    else:
        file_name = custom_file_name  # Use custom name (even if it's the same)

    
    print(f"File will be saved as '{file_name}'")

    print("-- NEGOTIATION OPTIONS --") 
    # custom options return b'' if no custom option is selected
    rrq = construct_rrq_packet(download_file_name)

    sock.sendto(rrq, server_address)

    print(f"Sent RRQ for '{download_file_name}' to {server_address}")

    # add implementation here later 
    expected_block = 1
    options_negotiated = False


    with open(file_name, 'wb') as f:
        while True:
            try:
                data, addr = sock.recvfrom(516)
                print(f"Received data from {addr}")
            except socket.timeout:
                print("Timeout waiting for response from the server.")
                break # exit loop if timeout occurs
            
            opcode = int.from_bytes(data[:2], byteorder='big')
            print(f"Received opcode: {opcode}") # remove this after testing

            # start testing of oack handling
            if opcode == 6:  # OACK packet
                print("Received OACK from server. Negotiating options...")
                # Parse options (key-value pairs)
                options = {}
                # Data after the first 2 bytes is a series of null-terminated strings.
                # Splitting on b'\x00' gives us a list; note that the last element may be empty.
                parts = data[2:].split(b'\x00')
                parts = [p for p in parts if p]  # remove empty parts
                for i in range(0, len(parts), 2):
                    key = parts[i].decode('ascii')
                    value = parts[i+1].decode('ascii') if i+1 < len(parts) else None
                    options[key] = value
                print("Negotiated options:", options)

                # Update local settings based on options (e.g., block size)
                if "blksize" in options:
                    negotiated_blksize = int(options["blksize"])
                    print(f"Negotiated block size: {negotiated_blksize}")
                    # If needed, adjust the size of the recvfrom buffer
                    # For simplicity, we'll assume 516 still works if block size isn't too high.
                
                # Acknowledge the OACK by sending an ACK with block number 0.
                ack = b'\x00\x04' + (0).to_bytes(2, byteorder='big')
                sock.sendto(ack, addr)
                print("Sent ACK for OACK (block #0)")
                options_negotiated = True
                continue  # Wait for the first data block (block 1)
            # end testing
            elif opcode == 3:
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
                display_error(error_code)
                print(f"Server returned error {error_code}: {error_msg}") # remove after testing 
                break
            else:
                print(f"Unknown opcode: {opcode}") # for testing purposes
                break


def ask_option(option_name: str) -> str | None:
    while True:
        answer = input(f"Do you want to have a custom {option_name}? (y/n): ")
        if answer.lower() in ['y', 'n']:
            break
        else:
            print("Invalid choice. Please enter 'y' or 'n'.")

    if answer.lower() == 'y':   
        custom_value = input(f"Enter custom {option_name}: ")
        return custom_value
    else:
        return None

# Option 1: Block Size
def custom_block_size():
    block_size = ask_option("block size")
    print(f"block size: {block_size}")
    return b'blksize\x00' + block_size.encode('ascii') + b'\x00' if block_size else b''

# Option 2: Timeout
def custom_timeout():
    timeout = ask_option("timeout")
    print(f"timeout: {timeout}")
    return b'timeout\x00' + timeout.encode('ascii') + b'\x00' if timeout else b''

# Option 3: Transfer Size
def custom_tsize():
    transfer_size = ask_option("transfer size")
    print(f"transfer size: {transfer_size}")
    return b'tsize\x00' + transfer_size.encode('ascii') + b'\x00' if transfer_size else b''

# this constructs the RRQ packet format
def construct_rrq_packet(filename):
    mode = "netascii" if filename.endswith(".txt") else "octet"
    rrq = b'\x00\x01' + filename.encode('ascii') + b'\x00' + mode.encode('ascii') + b'\x00' 
    rrq += custom_block_size() + custom_timeout() + custom_tsize()
    return rrq

# this constructs the WRQ packet format
def cqonstruct_wrq_packet(filename):
    mode = "netascii" if filename.endswith(".txt") else "octet"
    return b'\x00\x02' + filename.encode('ascii') + b'\x00' + mode.encode('ascii') + b'\x00'
    

def main():
    host, port = ask_address() # type => string, int
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5) # default timeout is 5 seconds
    server_address = (host, port) # type => tuple

    while True:
        choice = display_menu()

        if choice == 1: # RRQ
            tftp_download(sock, server_address)  # currently implementing this function
        elif choice == 2: # WRQ
            tftp_upload(sock, server_address)    # finish implementing this function
        elif choice == 3:
            sock.close() # close the socket
            break
        else:
            print("Invalid choice. Please try again.")


main()