"""Modelos de dados da aplicação."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Endereco:
    """Modelo para endereço."""
    cep: str
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cidade: str
    estado: str


@dataclass
class Pessoa:
    """Modelo para pessoa."""
    id: Optional[int] = None
    nome_completo: str = ""
    cpf_cnpj: str = ""
    email: str = ""
    celular: str = ""
    endereco: Optional[Endereco] = None