import socket
import traceback
import struct
import json
import base64
import numpy as np
from difflib import SequenceMatcher

def stringToArray(s):
    '''Convert string to numpy array'''

    a = np.empty([len(s)])
    for i in range(len(s)):
        a[i] = s[i]
    return a.astype(int)

def arrayToString(a):
    '''Convert numpy array to string'''

    s = ''
    for i in range(len(a)):
        s += str(int(a[i]))
    return s

def recv_msg(sock):
    #Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    #Read the message data
    return recvall(sock, msglen)


def recvall(sock, n):
    #Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data



host = ''        #Symbolic name meaning all available interfaces
port = 12345     #Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))

print("host: " + host + "\nport: " + str(port))
s.listen(1)
conn, addr = s.accept()
print("Connected by " + str(addr))
while True:

    try:
        #Get data.
        data = recv_msg(conn)

        if not data: break
        data = data.decode("utf-8")
        print("Data received: ")
        data = json.loads(data)
        #Pass data to vars
        compName = data['compression']['name']
        dictionary = data['compression']['dictionary']
        codeName = data['code']['name']
        n = data['code']['n']
        k = data['code']['k']
        H = data['code']['H']
        decodeTable = data['code']['decode-table']
        allMsgs = data['code']['all-messages']
        noise = data['noise']
        entropy = data['entropy']
        padding = data['padding']
        initFileSize = data['initial-file-size']
        finalFileSize = data['final-file-size']

        base64Str = data['data']
        encodedStr = base64.b64decode(base64Str).decode("utf-8")


        allMsgs = {v: k for k,v in allMsgs.items()}
        H = np.asarray(H).astype(int)

        decodedStr = ""
        errorsFixed = 0
        errorsNotFixed = 0
        #Decode linear code.
        for i in range(0, len(encodedStr), n):
            msg = np.array([int(encodedStr[i + j]) for j in range(n)])
            word = H.dot(msg.T) % 2
            word = arrayToString(word)

            if arrayToString(word) in decodeTable:
                #Find the error
                error = decodeTable[arrayToString(word)]
                #Fix the error
                msg = (msg - stringToArray(error)) % 2
                decodedStr += allMsgs[arrayToString(msg)]

                if error != '0'*n:
                    errorsFixed += 1
            else:
                errorsNotFixed += 1

        #Remove extra zeros
        decodedStr = decodedStr[:-padding]

        #Decompress from Shannon-Fano
        decompressedStr = ""
        word = ""
        dictionary = {v: k for k, v in dictionary.items()}
        for c in decodedStr:
            word += c
            if word in dictionary:
                decompressedStr += chr(int(dictionary[word]))
                word = ""

        print(decompressedStr)
        print("")
        print("")
        print("Compression:", compName)
        print("Encoding:", codeName)
        print("Initial File Size:", initFileSize)
        print("Final File Size:", finalFileSize)
        print("Entropy:", entropy)
        print("Padding:", padding)
        print("Noise:", noise)
        print("Errors Fixed:", errorsFixed)
        print("Errors Not Fixed", errorsNotFixed)
        break
    except socket.error:
        traceback.print_exc()
        print("Error")
        break

conn.close()
