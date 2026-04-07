import cv2
import numpy as np

def charger_image(path):
    img = cv2.imread(path)
    return img


def reconstruire(h,w,canaux):
    reconstructed_image = np.zeros((h,w,len(canaux)))
    for i in range(h):
        for j in range(w):
            reconstructed_image[i][j] = [canaux[k][i+w*j] for k in range(len(canaux))]
    return reconstructed_image

def afficher(image,title):
    cv2.imshow(title, image)
    cv2.waitKey(0)


def encoder(codeRS,data,k):
    encoded_data = []
    i=0
    n=len(data)
    while i+k<n:
        encoded_data += codeRS.encode_message(data[i:i+k])
        i+=k
    encoded_data+=codeRS.encode_message(data[i:])
    return encoded_data

def decoder(codeRS,data,n):
    decoded_data = []
    i=0
    while i+n < len(data):
        decoded_data+= codeRS.correct_msg(data[i:i+n])[0]
        i+=n
    decoded_data+=codeRS.correct_msg(data[i:])[0]
    return decoded_data

def sauvegarder(img):
    choix = str(input("[?] Voulez-vous sauvegarder l'image transmise? [y/n]"))
    if choix == "n":
        return 0
    elif choix =="y":
        titre = str(input("     [?] Titre? "))
        titre+='.jpg'
        cv2.imwrite(titre,img)
        return 1
    else:
        raise ValueError("Reponse invalide")