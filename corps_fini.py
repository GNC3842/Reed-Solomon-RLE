class GF256(object):
    def __init__(self,PRIMITIVE_POLY=0b110000111): # X^8+X^7+X^2+X+1 polynome de degré 8 irréductible dans F2
        self.primitive_poly =  PRIMITIVE_POLY
        self.tables = self.init_tables()
        self.exp = self.tables[0]
        self.log = self.tables[1]

    def add(self,x,y): #addition et soustraction bit à bit (XOR) ie modulo 2
        return x^y
    
    #Multiplication dans GF256 utilisant la multiplication standard avec reduction modulaire
    #seulement utiliser pour les tables
    #pourrait etre optimisé avec l'algorithme Russian Peasant Multiplication par exemple
    def mult_bin(self,x, y):
        result = self.cl_mult(x,y)
        result = self.cl_div(result,self.primitive_poly)
        return result

    ###multiplication classique###
    def cl_mult(self,x,y):
        z = 0
        i = 0
        while (y>>i) > 0:
            if y & (1<<i):
                z ^= x<<i
            i += 1
        return z

    ###Calcul position du bit de poids fort ie le degré du polynome associé
    def bit_length(self,n): 
        bits = 0
        while n >> bits: bits += 1
        return bits

    #division euclidienne de 2 octects et renvoie le reste
    def cl_div(self,dividend, divisor):
        # Calculer la position du bit le plus significatif pour chaque entier
        dl1 = self.bit_length(dividend)
        dl2 = self.bit_length(divisor)
        #Si degré du dividende plus petit que diviseur sortir
        if dl1 < dl2:
            return dividend
        # Sinon, alignez le 1 le plus significatif du diviseur sur le 1 le plus 
        # significatif du dividende (en décalant le diviseur)
        for i in range(dl1-dl2,-1,-1):
        # Vérifier que le dividende est divisible (inutile pour la première itération mais important pour les suivantes)
            if dividend & (1 << i+dl2-1):
            # Si divisible, décalez le diviseur pour aligner les bits les plus significatifs 
            # et effectuez un XOR (soustraction sans retenue)
                dividend ^= divisor << i
        return dividend

    #tables de calcul car plus simple
    def init_tables(self):
        gf_exp = [0] * 512 
        gf_log = [0] * 256
        x = 1
        for i in range(255):
            gf_exp[i] = x
            gf_log[x] = i
            x = self.mult_bin(x,2)
        for i in range(255,512):
            gf_exp[i] = gf_exp[i-255]
        return [gf_exp,gf_log]

    #multiplication en pratique de 2 elements de GF256
    def mult(self,x,y):
        if x==0 or y==0:
            return 0
        return self.exp[self.log[x] + self.log[y]]
    #division en pratique de 2 elements de GF256
    def div(self,x,y):
        if y==0:
            raise ZeroDivisionError("Division par zéro")
        if x==0:
            return 0
        return self.exp[(self.log[x]+255-self.log[y])%255]
    #elevation de x à la puissance power
    def pow(self,x,power):
        return self.exp[(self.log[x]*power)%255]

    #renvoie l'inverse de x noté y tel que x*y = y*x = 1
    def inverse(self,x):
        return self.exp[255-self.log[x]]

    ####CALCUL DE POLYNOMES A COEFF DANS GF256
    #multiplication polynome par scalaire
    def poly_scalaire(self,p,x):
        r = [0] * len(p)
        for i in range(0, len(p)):
            r[i] = self.mult(p[i], x)
        return r
    #addition de 2 polynomes à coeff dans GF256
    def poly_add(self,p,q):
        r = [0]*max(len(p),len(q))
        for i in range(len(p)):
            r[i+len(r)-len(p)] = p[i]
        for i in range(len(q)):
            r[i+len(r)-len(q)] ^= q[i]
        return r

    #multplication de 2 polynomes à coeff dans GF256
    def poly_mult(self,p,q):
        r = [0] * (len(p)+len(q)-1)
        #multiplication coef par coef
        for j in range(0, len(q)):
            for i in range(0, len(p)):
                r[i+j] ^= self.mult(p[i], q[j]) 
        return r
    
    #evaluer p en x
    def poly_eval(self,poly,x):
        y = poly[0]
        for i in range(1,len(poly)):
            y = self.mult(x,y)^poly[i]
        return y

    #division de polynome à coefficient dans
    # GF256 utilisant l'algorithme de division synthetic optimisé
    #pour ce corps de Galois GF(2^8)
    def poly_div(self,dividende,divisor):
        msg = list(dividende)
        for i in range(len(dividende)-(len(divisor)-1)):
            coef = msg[i]
            if coef != 0:
                for j in range(1,len(divisor)):
                    if divisor[j] != 0:
                        msg[i+j] ^= self.mult(divisor[j],coef)
        s = -(len(divisor)-1)
        return msg[:s],msg[s:] #quotient et reste