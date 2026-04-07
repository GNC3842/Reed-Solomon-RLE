import numpy as np

#def bruiter(data, taux_erreur=0.01):
#    if taux_erreur >1 or taux_erreur <0:
#        raise valueerror("taux d'erreur invalide")
#    bruit_img = data[:]
#    longueur = len(data)
#    nb_erreurs = int(longueur*taux_erreur)
#    pos = np.random.choice(longueur,nb_erreurs,replace=false)

#    for pos in bruit_img:
#        bruit_img[pos] = np.random.randint(0,256)
#    return bruit_img

def bruiter(data,taux_erreur):
    if taux_erreur>1 or taux_erreur < 0:
        raise ValueError("Valeur incorrecte")
    bruit_img = data[:]
    for i in range(len(data)):
        if np.random.random() < taux_erreur:
            bruit_img[i] = np.random.randint(0,256)
    return bruit_img