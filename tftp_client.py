import socket
import os
from pathlib import Path

#Constants
PORT = 69
MIN_BLK_SIZE = 8 
MAX_BLK_SIZE = 65464
BLK_SIZE = 512
RRQ = 1
WRQ = 2
DAT = 3
ACK = 4
ERR = 5


def create_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def verify_directory():

def request():
    """Using RRQ and WRQ request to the TFTP server"""

def upload_file():


def download_file():
    """Downloads file from the TFTP server using RRQ"""


def main():
    """Main function for command-line interface to perform file transfer"""
    ip_add = input("Enter Server IP Address: ")

    while True:
        print("Actions: ")
        print("[1] Upload")
        print("[2] Download")
        choice = int(input("Choice (1 or 2): "))
        filename= input("Enter filename: ")
        blksize = int(input("Enter block size (default 512): ") or BLK_SIZE)

        if choice == 1:
            upload_file()
            break
        elif choice == 2:
            download_file()
            break
        else:
            print("Invalid action, Please type a valid command.")



if __name__ == "__main__":
    main()