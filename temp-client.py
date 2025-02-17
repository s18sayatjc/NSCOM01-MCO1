import socket

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


def display_menu() -> int:
    print("1. Read file")
    print("2. Write file")
    print("3. Exit Program")
    choice = input("Enter choice: ")
    return int(choice)


def create_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# this is still for testing
def send_rrq(client, address, filename):
    opcode = 1  # Opcode for RRQ
    mode = "octet"  # Mode for binary transfer

    # Construct the RRQ packet
    rrq_packet = bytearray()
    rrq_packet.extend(opcode.to_bytes(2, byteorder='big'))
    rrq_packet.extend(filename.encode('ascii'))
    rrq_packet.append(0)
    rrq_packet.extend(mode.encode('ascii'))
    rrq_packet.append(0)

    # Send the RRQ packet to the server
    client.sendto(rrq_packet, address)

def main():
    host, port = ask_address()
    client = create_socket() # create a socket object
    address = (host, port)  # create a tuple of host and port number


    print(type(host), type(port)) # host -> string, port -> int

    # try to connect to the server
    try {
        client.connect(address)
    } except Exception as e {
        print("Error:", e)
    }

    print(type(host), type(port))

    while True:
        choice = display_menu()
        print(type(choice))
        if choice == 1:
            filename = input("Enter the filename to read: ")
            send_rrq(client, address, filename)
            # Receive the response from the server
            while True:
                data, addr = client.recvfrom(1024)
                if data:
                    print("Received:", data.decode())
                    break
        elif choice == 2:
            # call write file function here
            print("Write file")
        elif choice == 3:
            # this breaks the loop and exits the program
            print("Exit program")
            break
        else:
            print("Invalid choice")



    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(b"Hello, server!", (host, port))
        data, addr = s.recvfrom(1024)
        print("Received:", data.decode())
    

    