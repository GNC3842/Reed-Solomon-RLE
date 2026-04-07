import corps_fini as cp

class ReedSolomonError(Exception):
    pass

class ZeroDivisionError(Exception):
    pass

class ReedSolomon(object):
    def __init__(self,n,k):
        self.n = n
        self.k = k
        self.gf = cp.GF256()
        self.nsym = n-k
        self.gen = self.polynome_generateur()

    def polynome_generateur(self):
        g = [1]
        for i in range(self.nsym):
            g = self.gf.poly_mult(g,[1,self.gf.pow(2,i)])
        return g

    #algorithme d'encode basique (pas optimisé)
    def encode_message_non_opti(self,msg):
        if msg == []:
            return msg
        q,reste = self.gf.poly_div(msg+[0]*(len(self.gen)-1),self.gen)
        msg_out = msg + reste
        return msg_out

    #algo d'encode un peu plus optimisé
    def encode_message(self,msg_in):
        '''Reed-Solomon encodage avec division polynomiale (algo division synthetique étendue)'''
        if (len(msg_in) + self.nsym) > 255: raise ValueError("Message is too long (%i when max is 255)" % (len(msg_in)+self.nsym))
        # Initialisez msg_out avec les valeurs à l'intérieur de msg_in et complétez avec len(gen)-1 octets (qui est le nombre de symboles ecc).
        msg_out = [0] * (len(msg_in) + len(self.gen)-1)
        # Initialisation de la division synthétique avec le dividende (= polynôme du message d'entrée)
        msg_out[:len(msg_in)] = msg_in

        # Boucle division synthétique
        for i in range(len(msg_in)):
            # Notez qu'il s'agit ici de msg_out, et non de msg_in. Ainsi, nous réutilisons la valeur mise à jour à chaque itération.
            # (c'est ainsi que fonctionne la division synthétique : au lieu de stocker dans un registre temporaire les valeurs intermédiaires,
            # nous les engageons directement dans la sortie).
            coef = msg_out[i]

            # log(0) n'est pas défini ; nous devons donc vérifier manuellement ce cas. Cette vérification est inutile.
            # # le diviseur ici car nous savons qu'il ne peut pas être 0 puisque nous l'avons généré
            if coef != 0:
                # dans la division synthétique, on saute toujours le premier coefficient du diviseur, car il ne sert qu'à normaliser 
                # le coefficient du dividende (ce qui est ici inutile puisque le diviseur, le polynôme générateur, est toujours unitaire)
                for j in range(1, len(self.gen)):
                    msg_out[i+j] ^= self.gf.mult(self.gen[j], coef) # équivalent à msg_out[i+j] += gf_mul(self.gen[j], coef)

        # À ce stade, la division synthétique étendue est terminée. msg_out contient le quotient dans msg_out[:len(msg_in)]
        # et le reste dans msg_out[len(msg_in):]. Pour l'encodage RS, nous n'avons pas besoin du quotient, mais uniquement du reste
        # (qui représente le code RS). Nous pouvons donc simplement écraser le quotient par le message d'entrée, afin d'obtenir
        # notre mot de code complet composé du message et du code.
        msg_out[:len(msg_in)] = msg_in

        return msg_out


    #Calcul syndrome
    def calc_syndrome(self,msg,nsym):
        synd = [0]*nsym
        for i in range(nsym):
            synd[i] = self.gf.poly_eval(msg,self.gf.pow(2,i))
        return [0]+synd
    #check si msg altéré
    def check(self,msg,nsym):
        return (max(self.calc_syndrome(msg,nsym)) == 0)

    ######QUAND LA POSITION DES ERREURS EST CONNU
    #polynome position
    def find_erreur_locator(self,e_pos):
        e_loc = [1]
        for i in e_pos:
            e_loc = self.gf.poly_mult(e_loc,self.gf.poly_add([1],[self.gf.pow(2,i),0]))
        return e_loc
    #
    def find_error_evaluator(self,synd,err_loc,nsym):
        _,reste = self.gf.poly_div(self.gf.poly_mult(synd,err_loc),([1]+[0]*(nsym+1)))
        return reste
    #recherche des bonnes valeurs par l'algortihme de Fornay
    def correct_effacement(self,msg,synd,err_pos):
        coef_pos = [len(msg)-1-p for p in err_pos]
        err_loc = self.find_erreur_locator(coef_pos)
        err_eval = self.find_error_evaluator(synd[::-1],err_loc,len(err_loc)-1)[::-1]
        X = []
        for i in range(len(coef_pos)):
            l = 255-coef_pos[i]
            X.append(self.gf.pow(2,-l))
        E = [0]*len(msg)
        X_length = len(X)
        for i,Xi in enumerate(X):
            Xi_inv = self.gf.inverse(Xi)
            err_loc_prime_temp = []
            for j in range(X_length):
                if j!=i:
                    err_loc_prime_temp.append(self.gf.add(1,self.gf.mult(Xi_inv,X[j])))
            err_loc_prime = 1
            for coef in err_loc_prime_temp:
                err_loc_prime = self.gf.mult(err_loc_prime,coef)

            y = self.gf.poly_eval(err_eval[::-1],Xi_inv)
            y = self.gf.mult(y,self.gf.pow(Xi,1))
            if err_loc_prime == 0:
                raise ReedSolomonError("Erreur magnitude")
            magnitude = self.gf.div(y,err_loc_prime)
            E[err_pos[i]] = magnitude
        msg = self.gf.poly_add(msg,E)
        return msg

    #position erreurs inconnu
    def find_error_locator(self,synd,nsym,erase_loc=None,erase_count=0):
        if erase_loc:
            err_loc = list(erase_loc)
            old_loc = list(erase_loc)
        else:
            err_loc= [1]
            old_loc = [1]
        synd_shift = len(synd)-nsym

        for i in range(nsym-erase_count):
            if erase_loc:
                K = erase_count + i + synd_shift
            else:
                K = i+synd_shift
            delta = synd[K]
            for j in range(1,len(err_loc)):
                delta ^=self.gf.mult(err_loc[-(j+1)],synd[K-j])
            old_loc = old_loc+[0]
            if delta != 0:
                if len(old_loc) > len(err_loc):
                    new_loc = self.gf.poly_scalaire(old_loc,delta)
                    old_loc = self.gf.poly_scalaire(err_loc,self.gf.inverse(delta))
                    err_loc = new_loc
                err_loc = self.gf.poly_add(err_loc,self.gf.poly_scalaire(old_loc,delta))
        
        while len(err_loc) and err_loc[0] ==0:del err_loc[0]
        errs = len(err_loc)-1
        #if (errs-erase_count)*2+erase_count>nsym:
        #    raise ReedSolomonError("Trop d'erreurs")

        return err_loc

    def find_error(self,err_loc,nmess):#nmess = len(msg)
        errs = len(err_loc)-1
        err_pos = []
        for i in range(nmess):
            if self.gf.poly_eval(err_loc,self.gf.pow(2,i))==0:
                err_pos.append(nmess-1-i)
        #if len(err_pos) != errs:
        #    raise ReedSolomonError("Trop d'erreurs")
        return err_pos

    def forney_syndromes(self,synd,pos,nmess):
        erase_pos_reversed = [nmess-1-p for p in pos]
        fsynd = list(synd[1:])
        for i in range(len(pos)):
            x = self.gf.pow(2,erase_pos_reversed[i])
            for j in range(len(fsynd)-1):
                fsynd[j] = self.gf.mult(fsynd[j],x)^fsynd[1+j]
        return fsynd

    ###FONCTION DE CORRECTION PRINCIPALE
    def correct_msg(self,msg_in, erase_pos=None):
        if len(msg_in) > 255: #verifie la taille du message ne soit pas trop grosse
            raise ValueError("Message is too long (%i when max is 255)" % len(msg_in))
        if msg_in ==[]:
            return [],[]
        if len(msg_in) <self.k:
            msg_in += [0]*(self.k-len(msg_in))

        msg_out = list(msg_in)     # copy of message
        if erase_pos is None:
            erase_pos = []
        else:
            for e_pos in erase_pos:
                msg_out[e_pos] = 0
        # verifie qu'il n'y a pas trop d'erreurs
        #if len(erase_pos) > self.nsym: raise ReedSolomonError("Too many erasures to correct")
        # préparer le polynôme du syndrome en utilisant uniquement les erreurs (c'est-à-dire : 
        # erreurs = caractères remplacés par un octet nul ou remplacés par un autre caractère, 
        # mais dont nous ignorons la position)
        synd = self.calc_syndrome(msg_out,self.nsym)
        if max(synd) == 0:
            return msg_out[:-self.nsym], msg_out[-self.nsym:]  # no errors

        # calculer les syndromes de Forney, qui cachent les effacements du syndrome d'origine (de sorte que BM n'aura qu'à gérer les erreurs, pas les effacements)
        fsynd = self.forney_syndromes(synd,erase_pos, len(msg_out))
        # calculer le polynome locateur d'erreurs avec Berlekamp-Massey
        err_loc = self.find_error_locator(fsynd,self.nsym, erase_count=len(erase_pos))
        # trouver les erreurs
        err_pos = self.find_error(err_loc[::-1] , len(msg_out))
        if err_pos is None:
            raise ReedSolomonError("Impossible de localiser")    # error location failed
        # Trouver la valeur des erreurs et les corriger
        msg_out = self.correct_effacement(msg_out,synd,erase_pos + err_pos) #
        #verifier que le message est bien reconstitué
        synd = self.calc_syndrome(msg_out,self.nsym)
        #if max(synd) > 0:
        #    raise ReedSolomonError("Impossible de corriger")    

        return msg_out[:-self.nsym], msg_out[-self.nsym:]
