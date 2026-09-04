"""Módulo para gerenciamento do banco de dados."""
import sqlite3
from typing import List, Optional
from models import Pessoa, Endereco
from validators import Validador


class Database:
    """Classe para gerenciar operações com o banco de dados."""
    
    def __init__(self, db_path: str = "cadastro.db"):
        self.db_path = db_path
        self._criar_tabelas()
    
    def _criar_tabelas(self):
        """Cria as tabelas necessárias se não existirem."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de pessoas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pessoas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_completo TEXT NOT NULL,
                    cpf_cnpj TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL,
                    celular TEXT NOT NULL
                )
            """)
            
            # Tabela de endereços
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enderecos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pessoa_id INTEGER NOT NULL,
                    cep TEXT NOT NULL,
                    logradouro TEXT NOT NULL,
                    numero TEXT NOT NULL,
                    complemento TEXT,
                    bairro TEXT NOT NULL,
                    cidade TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    FOREIGN KEY (pessoa_id) REFERENCES pessoas (id)
                )
            """)
            
            conn.commit()
    
    def salvar_pessoa(self, pessoa: Pessoa) -> int:
        """
        Salva uma pessoa no banco de dados.
        
        Returns:
            ID da pessoa salva
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insere a pessoa
            cursor.execute("""
                INSERT INTO pessoas (nome_completo, cpf_cnpj, email, celular)
                VALUES (?, ?, ?, ?)
            """, (pessoa.nome_completo, pessoa.cpf_cnpj, pessoa.email, pessoa.celular))
            
            pessoa_id = cursor.lastrowid
            
            # Insere o endereço
            if pessoa.endereco:
                cursor.execute("""
                    INSERT INTO enderecos 
                    (pessoa_id, cep, logradouro, numero, complemento, bairro, cidade, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pessoa_id,
                    pessoa.endereco.cep,
                    pessoa.endereco.logradouro,
                    pessoa.endereco.numero,
                    pessoa.endereco.complemento,
                    pessoa.endereco.bairro,
                    pessoa.endereco.cidade,
                    pessoa.endereco.estado
                ))
            
            conn.commit()
            return pessoa_id
    
    def listar_pessoas(self) -> List[Pessoa]:
        """Lista todas as pessoas cadastradas."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Primeiro busca todas as pessoas
            cursor.execute("""
                SELECT id, nome_completo, cpf_cnpj, email, celular
                FROM pessoas
                ORDER BY id
            """)
            
            pessoas = []
            for row in cursor.fetchall():
                pessoa_id = row[0]
                
                # Depois busca o endereço de cada pessoa
                cursor.execute("""
                    SELECT cep, logradouro, numero, complemento, bairro, cidade, estado
                    FROM enderecos
                    WHERE pessoa_id = ?
                """, (pessoa_id,))
                
                endereco_data = cursor.fetchone()
                
                if endereco_data:
                    endereco = Endereco(
                        cep=endereco_data[0] or '',
                        logradouro=endereco_data[1] or '',
                        numero=endereco_data[2] or '',
                        complemento=endereco_data[3] or '',
                        bairro=endereco_data[4] or '',
                        cidade=endereco_data[5] or '',
                        estado=endereco_data[6] or ''
                    )
                else:
                    endereco = Endereco(
                        cep='', logradouro='', numero='', 
                        complemento='', bairro='', cidade='', estado=''
                    )
                
                pessoa = Pessoa(
                    id=row[0],
                    nome_completo=row[1],
                    cpf_cnpj=row[2],
                    email=row[3],
                    celular=row[4],
                    endereco=endereco
                )
                pessoas.append(pessoa)
            
            return pessoas
    
    def deletar_pessoa(self, pessoa_id: int):
        """Deleta uma pessoa do banco de dados."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Primeiro deleta o endereço
            cursor.execute("DELETE FROM enderecos WHERE pessoa_id = ?", (pessoa_id,))
            
            # Depois deleta a pessoa
            cursor.execute("DELETE FROM pessoas WHERE id = ?", (pessoa_id,))
            
            conn.commit()

    def atualizar_pessoa(self, pessoa: Pessoa) -> None:
        """Atualiza uma pessoa no banco de dados."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Atualiza a pessoa
            cursor.execute("""
                UPDATE pessoas 
                SET nome_completo = ?, email = ?, celular = ?
                WHERE id = ?
            """, (pessoa.nome_completo, pessoa.email, pessoa.celular, pessoa.id))
            
            # Atualiza o endereço
            if pessoa.endereco:
                cursor.execute("""
                    UPDATE enderecos 
                    SET cep = ?, logradouro = ?, numero = ?, complemento = ?, 
                        bairro = ?, cidade = ?, estado = ?
                    WHERE pessoa_id = ?
                """, (
                    pessoa.endereco.cep,
                    pessoa.endereco.logradouro,
                    pessoa.endereco.numero,
                    pessoa.endereco.complemento,
                    pessoa.endereco.bairro,
                    pessoa.endereco.cidade,
                    pessoa.endereco.estado,
                    pessoa.id
                ))
            
            conn.commit()