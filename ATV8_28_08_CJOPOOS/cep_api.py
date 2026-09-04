"""Módulo para consulta de CEP."""
import requests
from typing import Optional, Dict


class CepAPI:
    """Classe para consulta de CEP usando a API ViaCEP."""
    
    BASE_URL = "https://viacep.com.br/ws/{}/json/"
    
    @classmethod
    def consultar(cls, cep: str) -> Optional[Dict]:
        """
        Consulta um CEP na API ViaCEP.
        
        Args:
            cep: CEP a ser consultado (apenas números)
            
        Returns:
            Dicionário com os dados do endereço ou None em caso de erro
        """
        cep = ''.join(filter(str.isdigit, cep))
        
        if len(cep) != 8:
            return None
        
        try:
            response = requests.get(cls.BASE_URL.format(cep), timeout=10)
            response.raise_for_status()
            
            dados = response.json()
            
            # Verifica se o CEP foi encontrado
            if 'erro' in dados:
                return None
            
            return {
                'logradouro': dados.get('logradouro', ''),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('localidade', ''),
                'estado': dados.get('uf', ''),
                'cep': dados.get('cep', '')
            }
            
        except requests.exceptions.RequestException:
            return None