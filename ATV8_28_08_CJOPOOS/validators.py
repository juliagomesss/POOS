import re

class Validador:

    @staticmethod
    def _apenas_numeros(valor):
        return re.sub(r'[^0-9]', '', valor)

    @staticmethod
    def validar_cpf(cpf):
        cpf = Validador._apenas_numeros(cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Cálculo do 1º dígito verificador do CPF
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        
        # Cálculo do 2º dígito verificador do CPF
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        
        return int(cpf[9]) == digito1 and int(cpf[10]) == digito2

    @staticmethod
    def validar_cnpj(cnpj):
        cnpj = Validador._apenas_numeros(cnpj)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        # Cálculo do 1º dígito verificador do CNPJ
        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
        digito1 = 0 if soma % 11 < 2 else 11 - (soma % 11)
        
        # Cálculo do 2º dígito verificador do CNPJ
        pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
        digito2 = 0 if soma % 11 < 2 else 11 - (soma % 11)
        
        return int(cnpj[12]) == digito1 and int(cnpj[13]) == digito2

    @staticmethod
    def validar_cpf_cnpj(documento):
        """Retorna (booleano válido, tipo)"""
        doc_limpo = Validador._apenas_numeros(documento)
        
        if len(doc_limpo) == 11:
            return Validador.validar_cpf(doc_limpo), "CPF"
        elif len(doc_limpo) == 14:
            return Validador.validar_cnpj(doc_limpo), "CNPJ"
        else:
            return False, "Documento"

    @staticmethod
    def validar_email(email):
        # Regex simples para validar email
        return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))

    @staticmethod
    def validar_celular(celular):
        celular = Validador._apenas_numeros(celular)
        # Aceita 10 ou 11 dígitos (com ou sem 9)
        return len(celular) in (10, 11)

    @staticmethod
    def validar_cep(cep):
        cep = Validador._apenas_numeros(cep)
        return len(cep) == 8