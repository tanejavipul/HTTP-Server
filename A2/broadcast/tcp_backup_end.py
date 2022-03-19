import os
import select
import sys
import time
from socket import *
from PacketExtract import *
from threading import Thread


ROUTER_ADDRESS = ""
ROUTER = (ROUTER_ADDRESS, PACKET_PORT)


def setup():
    global ROUTER_ADDRESS
    global ROUTER
    print(sys.argv)
    if len(sys.argv) < 2:
        host_address = input("Enter End Point IP: ")
    else:
        host_address = sys.argv[1]

    ROUTER_ADDRESS = host_address[:host_address.rfind('.')+1] + "1"
    ROUTER = (ROUTER_ADDRESS, PACKET_PORT)
    print("Host IP: " + str(host_address))
    print("Router IP: " + str(ROUTER_ADDRESS))
    print("ROUTER: " + str(ROUTER))

    #UDP BROADCAST CONNECT
    broad = socket(AF_INET, SOCK_DGRAM)
    broad.bind((host_address, 0))
    broad.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    #PACKET CONNECT
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((host_address, PACKET_PORT))
    sock.listen()
    return broad, sock


def send_broadcast(s):
    src_address = s.getsockname()[0]
    src_port = s.getsockname()[1]
    message = "Hello I am a host"
    simple_packet = make_broadcast_packet(TYPE_INITIALIZE, src_address, src_port, 0, message)
    s.sendto(simple_packet, ("255.255.255.255", BROADCAST_PORT))


def main():
    global ROUTER
    broad, sock = setup() #UDP sock, TCP sock
    send_broadcast(broad)

    # maintains a list of possible input streams
    sockets_list = [sys.stdin, sock]

    while True:
        """ There are two possible input situations. Either the
        user wants to give manual input to send to other people,
        or the server is sending a message to be printed on the
        screen. Select returns from sockets_list, the stream that
        is reader for input. So for example, if the server wants
        to send a message, then the if condition will hold true
        below.If the user wants to send a message, the else
        condition will evaluate as true"""
        read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])

        for socks in read_sockets:
            if socks == sock and 1 == 0:
                print("inside")
                # conn, addr = sock.accept()
                # message = conn.recv(4096)
                # data = ""
                # while message:
                #     data += message
                #     message = conn.recv(4096)
                # print(addr, message)

            else:
                message = sys.stdin.readline()
                if message:
                    print(sock)
                    sock.sendall(message.encode())
                message = ""
                # sys.stdout.flush()



if __name__ == "__main__":
    main()





#ROUTER TEST CODE
# if __name__ == "__main__":
#     s = socket(AF_INET, SOCK_STREAM)
#     s.bind(("172.16.0.1", 8008))
#     s.listen(5)
#     while True:
#         conn, addr = s.accept()
#         print(conn.recv(4096))