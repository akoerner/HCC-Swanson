import socket

UDPSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

listen_addr = ("",12345)
UDPSock.bind(listen_addr)


# up to the server to sort this out!)
while True:
        data,addr = UDPSock.recvfrom(1024)
        print data.strip(),addr