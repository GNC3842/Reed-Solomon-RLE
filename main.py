import compression
import reed_solomon
import auxi
import cv2
import canal_bruite as canal


def main():
    mp.hello()
    # 1. Charger l'image originale
    image_path = input("nom avec extension de l'image:")
    image = auxi.charger_image(image_path)
    print("[INFO] Image chargée :", image.shape)
    h,w,c=image.shape
    print("[INFO] Taille initiale :",h*w*c,"octets.")

    # 2. Compresser l'image
    compressed_data = compression.compression_RLE(image)
    print("[INFO] Taille après compression :", len(compressed_data), "octets")
    print('[INFO] Taux de compression:',len(compressed_data)/(h*w*c)*100,"%")

    # 3. Encoder avec Reed-Solomon
    choix = str(input("\n[?]Voulez vous choisir les paramètres du code Reed Solomon? [y/n]"))
    if choix == "y":
        k = int(input("Taille des blocs? "))
        n = k + int(input("Nombre de symbole de redondance? "))
        if n>255 or n < k or k >255 or k < 1 :
            raise ValueError("Valeurs incorrectes")
    elif choix == 'n':
        k,n=212,244
    else:
        raise ValueError("Reponse incorrect")

    rs = reed_solomon.ReedSolomon(n,k)
    encoded_data = auxi.encoder(rs,compressed_data,k)
    print("[INFO] Taille après encodage avec RS("+str(n)+","+str(k)+"):", len(encoded_data), "octets")

    # 4. Simuler une transmission bruitée
    choix = str(input("\n[?] Voulez vous choisir le taux d'erreur? [y/n]"))
    if choix == "y":
        taux_erreur = float(input("Taux d'erreurs? "))
    elif choix == 'n':
        taux_erreur = 0.02
    else:
        raise ValueError("Reponse incorrect")
    noisy_data = canal.bruiter(encoded_data, taux_erreur)
    print("[INFO] Transmission bruitée avec taux_erreur = "+str(taux_erreur*100)+"%")

    # 5. Décoder avec Reed-Solomon
    decoded_data = auxi.decoder(rs,noisy_data,n)
    print("[INFO] Données décodées (RS)")
    print("Taille après décodage:",len(decoded_data))

    # 6. Décompresser l'image
    c,h,w,reconstructed_image = compression.decompress(decoded_data)
    print("[INFO] Image reconstruite :("+str(h)+","+str(w)+","+str(c)+")")

    # 7. Afficher résultats
    #auxi.afficher(image, title="Image originale")
    
    auxi.afficher(reconstructed_image, title="Image reconstruite")
    auxi.afficher(image,title="Image originale")
    auxi.sauvegarder(reconstructed_image)

if __name__ == "__main__":
    main()