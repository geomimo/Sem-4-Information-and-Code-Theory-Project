import ShannonFano as SF
import scipy.stats
import random
import numpy as np
import base64
import json
import os
import sys
import socket
import struct
from itertools import permutations


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

def send(content):
    host = socket.gethostname()
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    content = struct.pack('>I', len(content)) + content
    s.sendall(content)
    s.close()
    print('Sended!')

def w(v):
    '''Calculate Hammin weight of a word'''

    v = stringToArray(v)
    return np.count_nonzero(v)

def dminCodewords(ones, n):
    '''Calculate and return a list with all codewords with minimum weight.'''

    dminCodewords = []
    curOnes = 1
    while curOnes <= ones:
        arr = []
        count = 0
        for i in range(n):
            if count < curOnes:
                arr.append(1)
                count +=1
            else:
                arr.append(0)
        perm = permutations(arr)

        for p in list(perm):
            if p not in dminCodewords:
                dminCodewords.append(p)
        curOnes += 1

    return dminCodewords

#Get file name
while True:
    fileName = input("Give file name: ")
    try:
        file = open(fileName, "rb")
        fileSize = os.path.getsize("test.txt")
        text = bytearray(file.read())
        file.close()
        break
    except:
        print("Wrong name! Please try again.")

#Get dimension k
print("")
while True:
    K = input("Give dimension k: ")
    try:
        K = int(K)
    except:
        print("Wrong input! Please try again. k must be a positive integer.")
        continue

    if K <= 0:
        print("Wrong input! Please try again. k must be a positive integer.")
    else:
        break

#Get message lenght n
print("")
while True:
    N = input("Give message lenght n: ")
    try:
        N = int(N)
    except:
        print("Wrong input! Please try again. n must be a positive integer.")
        continue

    if N <= 0:
        print("Wrong input! Please try again. n must be a positive integer.")
    else:
        break


#Get noise
print("")
while True:
    noise = input("Give noise: ")
    try:
        noise = int(noise)
    except:
        print("Wrong input! Please try again. noise must be a positive integer.")
        continue

    if noise < 0 or noise > N:
        print("Wrong input! Please try again. noise must be a positive integer and less or equal than n.")
    else:
        break



#Calculate the total number of each byte value in the file
freqList = [0] * 256
for c in text:
    freqList[c] += 1

#Create a list of (frequency, byteValue, encodingBitStr) tuples
tupleList = []
for b in range(256):
    if freqList[b] > 0:
        tupleList.append((freqList[b], b, ''))

 #Sort the list according to the frequencies descending
tupleList = sorted(tupleList, key=lambda tup: tup[0], reverse = True)

# Calculate the probabillities for each element
probabilities = []
for t in tupleList:
    probabilities.append(round(t[0] / len(text), 3))

entropy = round(scipy.stats.entropy(probabilities), 3)

#Encode with Shannon-Fano method
encoder = SF.ShannonFano()
encoder.encode(tupleList, 0, len(tupleList) - 1)

#Create a dictionary of byteValue : encodingBitStr pairs
dic = dict([(tup[1], tup[2]) for tup in tupleList])

#Compress the text
compressedStr = ""
for c in text:
    compressedStr += dic[c]

#Add zeros
padding = K - (len(compressedStr) % K)
compressedStr += padding*'0'

#create P
P = []
for i in range(K):
    while True:
        temp = [random.choice([0,1]) for j in range(N - K)]
        if temp.count(0) != 0:
            break
    P.append(temp)
P = np.asarray(P)
I = np.identity(K)
G = np.concatenate((I,P), axis = 1).astype(int)


#Encode with linear Code
encodedStr = ""
allMsgs = {}
for i in range(0, len(compressedStr), K):
    word = np.array([int(compressedStr[i + j]) for j in range(K)])
    encodedWord = word.dot(G) % 2
    #Create a table with all messages and their codewords
    if arrayToString(word) not in allMsgs:
        allMsgs[arrayToString(word)] = arrayToString(encodedWord)

    #Add random noise
    randNoise = random.randint(0, noise)
    for j in range(randNoise):
        randIndex = random.randint(0, K - 1)
        encodedWord[randIndex] = (encodedWord[randIndex] + 1) % 2

    encodedStr += arrayToString(encodedWord)

#Calculate the minimum weight
dmin = N
for k,v in allMsgs.items():
    if w(v) != 0 and w(v) < dmin:
        dmin = w(v)

#Create the Standard Table
dminCodewords = dminCodewords(dmin,N)
standardArr = []

#First row with all codewords.
tempArr = []
for k,v in allMsgs.items():
    tempArr.append(v)
tempArr.sort()

for i in range(len(tempArr)):
    tempArr[i] = stringToArray(tempArr[i])
standardArr.append(tempArr)

#Fill the table
for c in dminCodewords:
    s = np.asarray(c)
    exists = False
    #Check if exists
    for r in standardArr:
        for a in r:
            if np.array_equal(a, s):
                exists = True
                break
        if exists:
            break
    #Calculate and add the row
    if not exists:
        temp = [s]
        for j in range(1, len(standardArr[0])):
            temp.append((s + standardArr[0][j]) % 2)
        standardArr.append(temp)

#Calculate H
P = np.asarray(P).astype(int)
PT = P.T
I = np.identity(N - K).astype(int)
H = np.concatenate((PT,I), axis = 1)

#Create the decode table
decodeTable = {}
for r in standardArr:
    decodeTable[arrayToString(H.dot(r[0].T) % 2)] = arrayToString(r[0])

#To base64
encodedStr = encodedStr.encode("utf-8")
base64Str = str(base64.b64encode(encodedStr), "utf-8")

print("")
print("Data:")
print(str(text, "utf-8"))

#Json
data = {
    'compression':{
        'name': "Shannon-Fano",
        'dictionary': dic,
    },
    'code':{
        'name': "linear",
        'n': N,
        'k': K,
        'H': H.tolist(),
        'decode-table': decodeTable,
        'all-messages': allMsgs
    },
    'noise': noise,
    'entropy': entropy,
    'padding': padding,
    'initial-file-size': fileSize,
    'data': base64Str
}
data['final-file-size'] = sys.getsizeof(data)

#Send the json
finalJson = json.dumps(data).encode("utf-8")
send(finalJson)
