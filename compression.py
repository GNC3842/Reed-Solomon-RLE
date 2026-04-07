import cv2
import numpy as np

length_taille = 4
length_taille_canal = 4


#Pour eviter les valeurs > 255

def int_to_bytes(n, length):
    """Convertit un entier en 'length' octets big-endian."""
    return [(n >> (8 * (length - 1 - i))) & 0xFF for i in range(length)]

def bytes_to_int(byte_list):
    n = 0
    for b in byte_list:
        n = (n << 8) | b
    return n

#Compression RLE par canal
#Le trableau d'image est convertie en 1 vecteur 1D où les valeurs de R,G et B sont consécutives pour
#maximiser les répétitions

def RLE_cannal(vect):
    vect_compress = []
    actuel = vect[0]
    compt = 1
    for element in vect[1:]:
        if element == actuel and compt<255:#Reed solomon ne peut coder que des entiers entre 0 et 255 car ici sur 1 octet
            compt+=1
        else:
            vect_compress.append(actuel)
            vect_compress.append(compt)
            compt = 1
            actuel = element
    vect_compress.append(actuel)
    vect_compress.append(compt)
    return vect_compress


def compression_RLE(img):
    h,w,c = img.shape
    tab = [[] for i in range(c)] #RGB
    for i in range(h):
        for k in range(w):
            for j in range(c):
                tab[j].append(img[i][k][j])
    #tab contient chaque vecteur 1D contenant R,G,B
    #Compression des canaux
    compressed_data = []
    taille_canaux = []
    for i in range(c):
        d_compressed = RLE_cannal(tab[i])
        taille_canaux += int_to_bytes(len(d_compressed),length_taille_canal) #encoder la taille de chaque canal sur 4 octets
        compressed_data = compressed_data + d_compressed
    taille = int_to_bytes(h,length_taille)+int_to_bytes(w,length_taille) #encoder taille image sur 8 octets (2*4)
    return [c]+taille+taille_canaux+compressed_data
    

def decompress(data):
    #nombre canaux
    c = data[0]
    if c!=3:
        c=3
    #Taille comprise entre 0 et 2*length_taille  
    #Correspond au 8 premiers octets
    lim_taille = 2*length_taille
    h,w = bytes_to_int(data[1:1+length_taille]),bytes_to_int(data[1+length_taille:2*length_taille+1])

    #Attention taille h et w
    if h>1500:
        h=1500
    if w>1800:
        w=1800
    #Lire taille canaux
    #correspond aux c*4 octets suivants (car sur 4 octets)
    deb = 2*length_taille+1
    taille_canal = []
    for i in range(0,c):
        fin = deb+length_taille_canal
        L = data[deb:fin]
        taille_canal = taille_canal + [bytes_to_int(L)]
        deb = fin
        if taille_canal[i] > h*w:
            taille_canal[i] = h*w
    #Lire canaux
    canaux = []
    print("----------Lecture des canaux----------")
    for longueur in taille_canal:#lire chaque canal
        tab = []
        print("Working")
        for j in range(0,longueur,2):#parcourir le canal en question
            if deb+j+1>= len(data):
                break
            tab = tab + [data[deb+j]]*data[deb+j+1]
        tab = completer(tab,h*w)
        canaux.append(tab)
        deb = deb + longueur

    print("----------Reconstruction image----------")
    new_img = np.zeros((h,w,c),np.uint8)
    for i in range(min(h,len(canaux[0]))):
        for j in range(min(w,len(canaux[0]))):
            if i*w+j >= min([len(canaux[k]) for k in range(c)]):
                break
            new_img[i][j] = [canaux[k][i*w+j] for k in range(c)]
    return c,h,w,new_img

def completer(tab,n):
    if len(tab) <n:
        tab = tab + [0]*(n-len(tab))
    else:
        tab = tab[:n]
    return tab