import time
import socket

UDP_IP = "192.168.4.1"  # IP-адрес NodeMCU
UDP_PORT = 1234  # Порт, на котором NodeMCU будет слушать

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

data = "1"
sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
time.sleep(1)
data = "0"
sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
time.sleep(1)
data = "2"
sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
time.sleep(1)
data = "0"
sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
time.sleep(1)
data = "3"
sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
time.sleep(1)
data = "0"
sock.sendto(data.encode(), (UDP_IP, UDP_PORT))


sock.close()
