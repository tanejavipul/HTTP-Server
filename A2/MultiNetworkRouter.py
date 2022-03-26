import os
import random
import select
import sys
import time
from socket import *
from Packets import *
from threading import Thread
from ForwardTable import *
import netifaces as ni
import datetime as dt

DELAY = 1
ETH = []
ROUTER_ADDRESS = ""

NAT = {}
forward_table = {}
NEIGHBORS = {} #TODO KILL ROUTER IF NOT ADVERTISED

def broadcast_setup(ip):
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind((ip, BROADCAST_PORT))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    return s


def eth_thread(eth, address):
    global forward_table
    print(str(eth) + " Thread Started with IP: " + address)
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind((address, ROUTER_PORT))

    # ADD ROUTER INTERFACE TO FORWARD TABLE
    forward_table[address] = {}
    forward_table[address][HOSTS] = []
    forward_table[address][HOPS] = 0
    forward_table[address][SEND_TO] = address

    while True:
        packet_data, add = s.recvfrom(4096)
        print("ADDRESS: " + str(add) + " ETH: " + str(eth) + " PACKET: " + str(packet_data))

        data = convert_to_dict(packet_data)

        if int(data[TTL]) < 1:
            print("PACKET DROPPED")
            #TODO FIX THIS

        # FIXME CHECK WITH PROF IF DELAY NEED BETWEEN INTERFACES
        # TODO fix delays
        if add[0] not in ETH:
            update_TTL(data)
            update_DELAY(data, DELAY)

        # Scenarios
        # SCENARIO 1: INTERNAL COMMUNICATION
        #       -->  SCENARIO 1.1  -  DEST IP IS IN CURRENT ETH
        #       -->  SCENARIO 1.2  -  DEST IP IS OTHER ETH
        dest = data[DEST_IP]
        found = False
        if dest in NAT:
            for interface in ETH:
                if dest in forward_table[interface][HOSTS]:
                    if interface == address:
                        found = True
                        s.sendto(convert_to_json(data), (NAT[dest][ADDRESS], NAT[dest][PORT]))
                    else:
                        found = True
                        s.sendto(convert_to_json(data), (interface, ROUTER_PORT))
        # SCENARIO 2: DEST IP IN ANOTHER ROUTER
        else:
            for key in forward_table:
                if dest in forward_table[key][HOSTS]:
                    found = True
                    s.sendto(convert_to_json(data), (forward_table[key][SEND_TO], ROUTER_PORT))
                    break
        if not found:
            print("ERROR: PACKET DROPPED - DESTINATION NOT FOUND")


# For receiving FORWARD TABLE from neighbors to update current router tables
# and for updating NAT's with KEEP_ALIVE
def broadcast_recv_thread():
    print("Broadcast Receiving Thread Started")
    global forward_table
    global NAT

    s_recv = socket(AF_INET, SOCK_DGRAM)
    s_recv.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s_recv.bind(('255.255.255.255', BROADCAST_PORT))

    while True:
        valid = False
        data, address = s_recv.recvfrom(4096)
        # print("BROADCAST INCO: " + str((address, data)))

        try:
            if address[0] in ETH: # TO ignore self broadcasts reads
                valid = False
            else:
                data = convert_to_dict(data)
                valid = True
        except:
            valid = False
        if valid:
            if data[TYPE] == TYPE_INITIALIZE:
                forward_table[data.get(ROUTER_INTERFACE)][HOSTS].append(data[ADDRESS])
                NAT[data[ADDRESS]] = {}
                NAT[data[ADDRESS]][ADDRESS] = address[0]
                NAT[data[ADDRESS]][PORT] = address[1]
                NAT[data[ADDRESS]][KEEP_ALIVE] = dt.datetime.now()
            if data[TYPE] == TYPE_KEEP_ALIVE:
                NAT[data[ADDRESS]][KEEP_ALIVE] = dt.datetime.now()
            if data[TYPE] == TYPE_ADVERTISE:
                # TODO update neighbors timing and fix update,if neighbors updated then send update out DONT DO
                update(forward_table, data)
                if data[FROM] not in NEIGHBORS:
                    NEIGHBORS[data[FROM]] = {}
                    NEIGHBORS[data[FROM]][DELAY_STR] = DELAY
                NEIGHBORS[data[FROM]][KEEP_ALIVE] = dt.datetime.now()

# For sending forward table to neighbors
def broadcast_send_thread():
    print("Broadcast Sending Thread Started")
    sock_list = []
    for eth in ETH:
        sock_list.append(broadcast_setup(eth))

    while True:
        time.sleep(2)
        adv = advertise(forward_table, ROUTER_ADDRESS)
        adv = convert_to_json(adv)
        for sock in sock_list:
            sock.sendto(adv, ("255.255.255.255", BROADCAST_PORT))

        temp = NAT.copy()
        for key in temp:
            now = dt.datetime.now()
            temp = now - NAT[key][KEEP_ALIVE]
            if temp.total_seconds() > HOST_NOT_ALIVE:
                print("REMOVING INACTIVE HOST: " + str(key))
                for eth in ETH:
                    if key in forward_table[eth][HOSTS]:
                        forward_table[eth][HOSTS].remove(key)
                        break
                NAT.pop(key)

        temp_neighbors = NEIGHBORS.copy()
        for key in temp_neighbors:
            now = dt.datetime.now()
            temp = now - NEIGHBORS[key][KEEP_ALIVE]
            if temp.total_seconds() > ROUTER_NOT_ALIVE:
                print("REMOVING INACTIVE ROUTER: " + str(key))
                forward_temp = forward_table.copy()
                for forward_key in forward_temp:
                    if forward_table[forward_key][SEND_TO] == key:
                        forward_table.pop(forward_key)
                NEIGHBORS.pop(key)
        #neightbors and forward table
        #forward table -> pop if send_to is the saem and if key is the same


# PRINT TABLE
# PRINT NAT
# PRINT NEIGHBORS
# SET DELAY 10   #when you update delay, you need to update neighbors
def get_command_input():
    global forward_table
    global NAT
    global DELAY
    global NEIGHBORS
    while True:
        message = sys.stdin.readline()
        message = message.strip().upper()
        if message == PRINT_NAT:
            print("NAT: " + str(NAT))
        elif message == PRINT_FORWARD_TABLE:
            print("FORWARD: " + str(forward_table))
        elif message == PRINT_NEIGHBORS:
            print("NEIGHBORS: " + str(NEIGHBORS))
        elif message == PRINT_DELAY:
            print("DELAY: " + str(DELAY))
        else:
            if SET_DELAY in message:
                try:
                    new_delay = int(message.split()[2])
                    DELAY = new_delay
                    for neigh in NEIGHBORS:
                        NEIGHBORS[neigh][DELAY_STR] = DELAY
                except:
                    print("INVALID COMMAND")
                    print("VALID COMMAND LIST: 'PRINT FORWARD TABLE', 'PRINT NEIGHBORS', 'PRINT NAT', 'SET DELAY <int>'")

            else:
                print("INVALID COMMAND")
                print("VALID COMMAND LIST: 'PRINT FORWARD TABLE', 'PRINT NEIGHBORS', 'PRINT NAT', 'SET DELAY <int>'")



if __name__ == "__main__":
    if len(sys.argv) == 2:
        try:
            if sys.argv[1].upper() == "R":
                delay = random.randint(1, 10)
            else:
                delay = int(sys.argv[1])
                print("Delay: " + str(delay))
            DELAY = delay
        except:
            print("Please provide a number for delay")
            print("Delay: 1")

    print("STARTING ETH THREADS")
    interfaces = ni.interfaces()
    if 'lo' in interfaces: interfaces.remove('lo')
    all_thread = []
    for inter in interfaces:
        ip_dict = ni.ifaddresses(inter)[2][0]
        ip = ip_dict.get('addr', "")

        if "eth0" in inter or "eth1" in inter:
            # Just populate it with any IP ADDRESS
            ROUTER_ADDRESS = ip

        if ip:
            thr = Thread(target=eth_thread, args=(inter, ip,))
            thr.start()
            ETH.append(ip)
            all_thread.append(thr)

    if len(ETH) == 0:
        raise Exception("ERROR: NO THREAD WERE MADE")
    if ROUTER_ADDRESS == "":
        ROUTER_ADDRESS = ETH[0]

    time.sleep(0.5)
    print("COMPLETED ETH THREADS\n")

    print("STARTING BROADCAST THREADS")
    Thread(target=broadcast_recv_thread).start()
    Thread(target=broadcast_send_thread).start()
    print("COMPLETED BROADCAST THREADS\n")

    Thread(target=get_command_input).start()
    print("ROUTER HAS STARTED!")
    print(ETH)



