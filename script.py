#!/usr/bin/python3
import subprocess

# By default the VPN only applies to other peers

PEERS=32 # max 255
SERVER_PORT=47420
# NETWORK_ITRF="eth0"
NETWORK_NAME="melchiorNetwork"
SERVER_ENDPOINT="ventarc.mywire.org"
NETWORK_ITRF="enp3s0"
IPADDRRAN="10.0.0." 

dict = {}
subprocess.run(["mkdir", "-p", f"./{NETWORK_NAME}"])

# Making Private/Public key pairs
for peer_num in range(1, 1+PEERS):
    client = {}
    subprocess.run(["mkdir", "-p", f"./{NETWORK_NAME}/client_{str(peer_num)}"])

    client["privatekey"] = subprocess.run(["/usr/bin/wg", "genkey"], capture_output=True).stdout.decode("utf-8")
    pk = open(f"./{NETWORK_NAME}/client_{str(peer_num)}/client_{str(peer_num)}_privatekey", "w")
    pk.write(client["privatekey"])
    pk = open(f"./{NETWORK_NAME}/client_{str(peer_num)}/client_{str(peer_num)}_privatekey", "r")

    client["publickey"] = subprocess.run(["/usr/bin/wg", "pubkey"], stdin=pk,  capture_output=True).stdout.decode("utf-8")
    pk = open(f"./{NETWORK_NAME}/client_{str(peer_num)}/client_{str(peer_num)}_publickey", "w")
    pk.write(client["publickey"])

    client["ip"] = f"{IPADDRRAN}{str(peer_num)}"
    dict[peer_num] = client

# Making Clients configurations files
def client_template(ip_client, ip_server, client_privatekey, server_publickey):
    return f"\
[Interface]\n\
  Address = {ip_client}/32\n\
  PrivateKey = {client_privatekey}\
\n\
[Peer]\n\
  PublicKey = {server_publickey}\
  EndPoint = {ip_server}:{str(SERVER_PORT)}\n\
  AllowedIPs = {IPADDRRAN}0/24"

for client_num in range(2, 1+PEERS):
    conf = open(f"./{NETWORK_NAME}/client_{str(client_num)}/{NETWORK_NAME}.conf", "w")
    conf.write(client_template(dict[client_num]["ip"], SERVER_ENDPOINT, dict[client_num]["privatekey"], dict[1]["publickey"]))

# Making QR codes for clients
for client_num in range(2, 1+PEERS):
    conf = open(f"./{NETWORK_NAME}/client_{str(client_num)}/{NETWORK_NAME}.conf", "r")
    subprocess.run(["qrencode", "-t", "png", "-o", f"./{NETWORK_NAME}/client_{str(client_num)}/qr-peer-"+str(client_num)+".png", "-r", f"./{NETWORK_NAME}/client_{str(client_num)}/{NETWORK_NAME}.conf"])

# Making Server configuration files
server_conf = f"\
[Interface]\n\
Address = {dict[1]['ip']}/24\n\
PostUp = iptables -A FORWARD -i {NETWORK_NAME} -j ACCEPT; iptables -t nat -A POSTROUTING -o {NETWORK_ITRF} -j MASQUERADE ; iptables -A FORWARD -i {NETWORK_NAME} -j ACCEPT\n\
PostDown = iptables -D FORWARD -i {NETWORK_NAME} -j ACCEPT; iptables -t nat -D POSTROUTING -o {NETWORK_ITRF} -j MASQUERADE ; iptables -D FORWARD -i {NETWORK_NAME} -j ACCEPT\n\
ListenPort = {SERVER_PORT}\n\
PrivateKey = {dict[1]['privatekey']}\
\n"
for client_num in range(2, 1+PEERS):
    server_conf += f"\
[Peer]\n\
PublicKey = {dict[client_num]['publickey']}\
AllowedIPs = {dict[client_num]['ip']}/32\n\
\n"
conf = open(f"./{NETWORK_NAME}/client_{str(1)}/{NETWORK_NAME}.conf", "w")
conf.write(server_conf)


print(server_conf)
print(dict)