#La clase valores inicializa por defecto el par establecido y la cantidad de dias
class valores:
    #colocamos parametros por defecto para cuando no se envien dichos parametros
    def __init__(self, dias=10, par="ETHUSDT"):
        self.dias = dias
        self.par = par

    def __str__(self):
        return f"{self.dias}({self.par})"