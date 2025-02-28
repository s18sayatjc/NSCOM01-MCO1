# @NSCOM01 - Machine Project #1
# @author: Andrei De Jesus, John Sayat
# @section: S13
# last modified @ 02/19/2025 11:00 PM final version

import socket
import os

# print a line of asterisks for design purposes
def print_ast():
    print("*" * 75)

# ask user to input server address and validate if the input is valid
def ask_address():
    while True:
        print_ast()
        try:
            host = input("ENTER SERVER ADDRESS: ")
            if host.count('.') != 3 or host.endswith('.'):
                raise ValueError("Invalid IP address format")
            port = 69  # use default port number for TFTP
            return (host, port)  # return the host and port number
        except Exception as e:
            print("Error:", e)  # print error message

# display the operations a client can do
def display_menu() -> int:
    while True:
        print_ast()
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

# function to handle the WRQ operation
def tftp_upload(sock, server_address): 
    print_ast()

    print("-- UPLOAD FILE (WRQ) --")
    upload_file_name = input("NAME OF FILE TO UPLOAD: ")
    print("Note: ./ => retain original name")
    custom_file_name = input("CUSTOM FILE NAME WHEN UPLOADED TO SERVER: ")
    file_name2 = ""

    if custom_file_name == "./":
        file_name2 = upload_file_name # Retain original name
    else:
        file_name2 = custom_file_name # Use custom name
    
    # Check if the file exists in the client's directory
    if not os.path.isfile(upload_file_name):
        print(f"Error: File '{upload_file_name}' does not exist in the client's directory.")
        return

    print(f"File will be saved as '{file_name2}'")
    print_ast()

    # test the custom options handling and display
    wrq = construct_tftp_packet(file_name2, "WRQ")
    print(f"Constructed WRQ packet: {wrq}")

    try:
        sock.sendto(wrq, server_address)
        print(f"Sent WRQ for '{file_name2}' to {server_address}")
    except socket.error as e:
        print(f"Error: Unable to send WRQ to server. Server might not be listening. Details: {e}")
        return

    expected_block = 1  # Set initial expected block to 1
    buffer_size = 516  # Default buffer size

    with open(upload_file_name, 'rb') as f:
        while True:
            print_ast()
            try:
                data, addr = sock.recvfrom(buffer_size)
                print(f"Received data from {addr}")
            except socket.timeout:
                print("Timeout waiting for response from the server.")
                break
            
            opcode = int.from_bytes(data[:2], byteorder='big')
            print(f"Received opcode: {opcode}")

            if opcode == 6:  # OACK packet
                print("Received OACK from server. Negotiating options...")
                options = {}
                parts = data[2:].split(b'\x00')
                parts = [p for p in parts if p]  # remove empty parts
                for i in range(0, len(parts), 2):
                    key = parts[i].decode('ascii')
                    value = parts[i+1].decode('ascii') if i+1 < len(parts) else None
                    options[key] = value
                print("Negotiated options:", options)

                if "blksize" in options:
                    negotiated_blksize = int(options["blksize"])
                    print(f"Negotiated block size: {negotiated_blksize}")
                    buffer_size = negotiated_blksize + 4  # Adjust buffer size for data + TFTP header

                if "timeout" in options:
                    negotiated_timeout = int(options["timeout"])
                    print(f"Negotiated timeout: {negotiated_timeout}")
                    sock.settimeout(negotiated_timeout)

                if "tsize" in options:
                    negotiated_tsize = int(options["tsize"])
                    print(f"Negotiated transfer size: {negotiated_tsize}")

                ack = b'\x00\x04' + (0).to_bytes(2, byteorder='big')
                sock.sendto(ack, addr)
                print("Sent ACK for OACK (block #0)")

                block = f.read(buffer_size - 4)
                if block:
                    data_packet = b'\x00\x03' + expected_block.to_bytes(2, byteorder='big') + block
                    sock.sendto(data_packet, addr)
                    print(f"Sent DATA packet, block #{expected_block} to {addr}")
                    print(f"Block size: {len(block)} bytes")
                    expected_block += 1
                continue  # Wait for the first ACK (block 1)
            elif opcode == 4:  # ACK packet
                block_num = int.from_bytes(data[2:4], byteorder='big')
                print(f"Received ACK #{block_num} for block #{block_num} from {addr}")
                if block_num == expected_block - 1:
                    block = f.read(buffer_size - 4)
                    if not block:
                        print("Upload Complete. All data blocks sent.")
                        break
                    data_packet = b'\x00\x03' + expected_block.to_bytes(2, byteorder='big') + block
                    sock.sendto(data_packet, addr)
                    print(f"Sent DATA packet, block #{expected_block} to {addr}")
                    print(f"Block size: {len(block)} bytes")
                    expected_block += 1
                else:
                    print(f"Unexpected ACK block number: {block_num}. Expected: {expected_block - 1}")
                    break
            elif opcode == 5:  # ERROR packet
                error_code = int.from_bytes(data[2:4], byteorder='big')
                error_msg = data[4:-1].decode('ascii')
                print(display_error(error_code))
                print(f"Server returned error {error_code}: {error_msg}")
                break
            else:
                print(f"Unknown opcode: {opcode}")
                break

# function to handle the RRQ operation
def tftp_download(sock, server_address):
    print_ast()
    print("-- DOWNLOAD FILE (RRQ) --")
    download_file_name = input("NAME OF FILE TO DOWNLOAD: ")
    print("Note: ./ => retain original name")
    custom_file_name = input("CUSTOM FILE NAME WHEN DOWNLOADED LOCALLY: ")
    file_name = ""

    # Check if the file name is a custom name
    if custom_file_name.startswith("./"):
        file_name = download_file_name  # Retain original name
    else:
        file_name = custom_file_name  # Use custom name

    # display the file name that will be use to store the downloaded file
    print(f"File will be saved as '{file_name}'")
    print_ast()

    # Construct RRQ packet
    rrq = construct_tftp_packet(download_file_name, "RRQ")
    print(f"Constructed RRQ packet: {rrq}")
    try:
        sock.sendto(rrq, server_address)
        print(f"Sent RRQ for '{download_file_name}' to {server_address}")
    except socket.error as e:
        print(f"Error: Unable to send RRQ to server. Server might not be listening. Details: {e}")
        return

    expected_block = 1
    options_negotiated = False
    buffer_size = 516  # Default buffer size

    with open(file_name, 'wb') as f:
        while True:
            print_ast()
            try:
                data, addr = sock.recvfrom(buffer_size)
            except socket.timeout:
                print("Timeout waiting for response from the server.")
                break
            
            opcode = int.from_bytes(data[:2], byteorder='big')
            print(f"Received opcode: {opcode}") # remove after debugging

            if opcode == 6:  # OACK packet
                print("Received OACK from server. Negotiating options...")
                options = {}
                parts = data[2:].split(b'\x00')
                parts = [p for p in parts if p]  # remove empty parts
                for i in range(0, len(parts), 2):
                    key = parts[i].decode('ascii')
                    value = parts[i+1].decode('ascii') if i+1 < len(parts) else None
                    options[key] = value
                print("Negotiated options:", options)

                if "blksize" in options:
                    negotiated_blksize = int(options["blksize"])
                    print(f"Negotiated block size: {negotiated_blksize}")
                    buffer_size = negotiated_blksize + 4  # Adjust buffer size for data + TFTP header
                
                if "timeout" in options:
                    negotiated_timeout = int(options["timeout"])
                    print(f"Negotiated timeout: {negotiated_timeout}")
                    sock.settimeout(negotiated_timeout)
                # removed tsize option in rrq packet
                ack = b'\x00\x04' + (0).to_bytes(2, byteorder='big')
                sock.sendto(ack, addr)
                print("Sent ACK for OACK (block #0)")
                options_negotiated = True
                continue  # Wait for the first data block (block 1)
            elif opcode == 3:
                block_num = int.from_bytes(data[2:4], byteorder='big')
                print(f"Received DATA packet, block #{block_num} from {addr}")
                if block_num == expected_block:
                    block_size = len(data[4:])
                    print(f"Block size: {block_size} bytes")
                    f.write(data[4:])
                    ack = b'\x00\x04' + data[2:4]
                    sock.sendto(ack, addr)
                    print(f"Sent ACK #{block_num} for block #{block_num} to {addr}")

                    expected_block += 1 

                    if block_size < buffer_size - 4:
                        print(f"Download Complete. Received final data block. Block size: {block_size} bytes")
                        break
                else:
                    print(f"Unexpected block number: {block_num}. Expected: {expected_block}")
                    break
            elif opcode == 5:
                error_code = int.from_bytes(data[2:4], byteorder='big')
                error_msg = data[4:-1].decode('ascii')
                display_error(error_code)
                print(f"Server returned error {error_code}: {error_msg}")
                break
            else:
                print(f"Unknown opcode: {opcode}")  # print unknown opcode if there is any for debugging purposes
                break

# ask user if they want to have a custom option
def ask_option(option_name: str) -> str | None:
    while True:
        answer = input(f"Do you want to have a custom {option_name}? (y/n): ")
        if answer.lower() in ['y', 'n']:
            break
        else:
            print("Invalid choice. Please enter 'y' or 'n'.")

    if answer.lower() == 'y':   
        custom_value = input(f"Enter custom {option_name} value: ")
        return custom_value
    else:
        return None

# this function handles the custom options for the client
def custom_options(request_type):
    options = b''
    
    block_size = ask_option("block size")
    if block_size:
        print(f"Custom block size: {block_size}")
        options += b'blksize\x00' + block_size.encode('ascii') + b'\x00'
    
    timeout = ask_option("timeout")
    if timeout:
        print(f"Custom timeout: {timeout}")
        options += b'timeout\x00' + timeout.encode('ascii') + b'\x00'
    
    if request_type == "WRQ":
        transfer_size = ask_option("transfer size")
        if transfer_size:
            print(f"Custom transfer size: {transfer_size}")
            options += b'tsize\x00' + transfer_size.encode('ascii') + b'\x00'

    return options

# construct the tftp packet with the custom options
def construct_tftp_packet(filename, request_type):
    print("-- NEGOTIATION OPTIONS --")

    mode = "netascii" if filename.endswith(".txt") else "octet"
    if request_type == "RRQ":
        opcode = b'\x00\x01'
        options = custom_options(request_type)
    elif request_type == "WRQ":
        opcode = b'\x00\x02'
        options = custom_options(request_type)
    else:
        raise ValueError("Invalid request type. Must be 'RRQ' or 'WRQ'.")

    packet = opcode + filename.encode('ascii') + b'\x00' + mode.encode('ascii') + b'\x00' + options
    return packet  # return the constructed packet with optional added custom options


# main function
def main():
    host, port = ask_address() # destructure the tuple
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # create a socket object
    sock.settimeout(5) # set the default timeout to 5 seconds
    server_address = (host, port) # assign the host and port to the server address

    # loop while the user does not exit the program
    while True:
        # prompt the user to select an operation
        choice = display_menu()

        if choice == 1:
            # perform the RRQ operation
            tftp_download(sock, server_address)
        elif choice == 2:
            # perform the WRQ operation
            tftp_upload(sock, server_address)    
        elif choice == 3:
            # display a message when the user exits the program
            print("Exiting program...")
            # close the socket and exit the program
            sock.close()
            break 
        else:
            # prompt the user to enter a valid choice
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main() # call the main function