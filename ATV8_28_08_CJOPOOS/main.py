# main.py
import sys
import re
import sqlite3
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal  # <-- ADICIONEI Qt AQUI

import requests


# ===================== VALIDAÇÕES =====================
class Validador:
    """Validações dos campos do formulário"""
    
    @staticmethod
    def cpf(cpf: str) -> bool:
        cpf = re.sub(r'[^0-9]', '', cpf)
        if len(cpf) != 11 or len(set(cpf)) == 1:
            return False
        
        # Validação simples dos dígitos verificadores
        for i in range(9, 11):
            soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
            digito = 0 if soma % 11 < 2 else 11 - (soma % 11)
            if int(cpf[i]) != digito:
                return False
        return True
    
    @staticmethod
    def cnpj(cnpj: str) -> bool:
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            return False
        
        # Validação simplificada do CNPJ
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(12))
        digito1 = 0 if soma % 11 < 2 else 11 - (soma % 11)
        
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(13))
        digito2 = 0 if soma % 11 < 2 else 11 - (soma % 11)
        
        return int(cnpj[12]) == digito1 and int(cnpj[13]) == digito2
    
    @staticmethod
    def email(email: str) -> bool:
        return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))
    
    @staticmethod
    def celular(celular: str) -> bool:
        celular = re.sub(r'[^0-9]', '', celular)
        return len(celular) in [10, 11]
    
    @staticmethod
    def cep(cep: str) -> bool:
        cep = re.sub(r'[^0-9]', '', cep)
        return len(cep) == 8


# ===================== API CEP =====================
class ApiCep:
    @staticmethod
    def consultar(cep: str):
        cep = re.sub(r'[^0-9]', '', cep)
        try:
            resposta = requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=5)
            dados = resposta.json()
            if 'erro' in dados:
                return None
            return {
                'logradouro': dados.get('logradouro', ''),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('localidade', ''),
                'estado': dados.get('uf', ''),
                'complemento': dados.get('complemento', '')
            }
        except:
            return None


# ===================== THREAD CEP =====================
class ThreadCep(QThread):
    resultado = Signal(dict)
    erro = Signal(str)
    
    def __init__(self, cep):
        super().__init__()
        self.cep = cep
    
    def run(self):
        dados = ApiCep.consultar(self.cep)
        if dados:
            self.resultado.emit(dados)
        else:
            self.erro.emit("CEP não encontrado ou erro na consulta")


# ===================== BANCO DE DADOS =====================
class Banco:
    def __init__(self):
        self.conexao = sqlite3.connect('cadastros.db')
        self.cursor = self.conexao.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pessoas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                documento TEXT,
                tipo TEXT,
                email TEXT,
                celular TEXT,
                cep TEXT,
                logradouro TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                estado TEXT,
                data TEXT
            )
        ''')
        self.conexao.commit()
    
    def salvar(self, dados):
        try:
            self.cursor.execute('''
                INSERT INTO pessoas (
                    nome, documento, tipo, email, celular, cep,
                    logradouro, numero, complemento, bairro, cidade, estado, data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dados['nome'], dados['documento'], dados['tipo'],
                dados['email'], dados['celular'], dados['cep'],
                dados['logradouro'], dados['numero'], dados['complemento'],
                dados['bairro'], dados['cidade'], dados['estado'],
                datetime.now().strftime('%d/%m/%Y %H:%M')
            ))
            self.conexao.commit()
            return True
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            return False
    
    def fechar(self):
        self.conexao.close()


# ===================== JANELA PRINCIPAL =====================
class JanelaCadastro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.banco = Banco()
        self.thread_cep = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Cadastro de Pessoas')
        self.setMinimumSize(700, 600)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QVBoxLayout(central)
        
        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout_principal.addWidget(scroll)
        
        # Container do formulário
        container = QWidget()
        scroll.setWidget(container)
        layout_form = QVBoxLayout(container)
        
        # Título
        titulo = QLabel('📋 CADASTRO DE PESSOA')
        titulo.setStyleSheet('font-size: 18px; font-weight: bold;')
        titulo.setAlignment(Qt.AlignCenter)  # <-- AGORA Qt ESTÁ DEFINIDO
        layout_form.addWidget(titulo)
        
        # Grupo Dados Pessoais
        grupo1 = QGroupBox('Dados Pessoais')
        grid1 = QGridLayout()
        grupo1.setLayout(grid1)
        layout_form.addWidget(grupo1)
        
        # Nome
        grid1.addWidget(QLabel('Nome Completo:'), 0, 0)
        self.nome = QLineEdit()
        self.nome.setPlaceholderText('Digite o nome completo')
        grid1.addWidget(self.nome, 0, 1, 1, 3)
        
        # Documento
        grid1.addWidget(QLabel('CPF/CNPJ:'), 1, 0)
        self.documento = QLineEdit()
        self.documento.setPlaceholderText('000.000.000-00')
        grid1.addWidget(self.documento, 1, 1)
        
        grid1.addWidget(QLabel('Tipo:'), 1, 2)
        self.tipo_doc = QComboBox()
        self.tipo_doc.addItems(['CPF', 'CNPJ'])
        self.tipo_doc.currentTextChanged.connect(self.trocar_placeholder_documento)
        grid1.addWidget(self.tipo_doc, 1, 3)
        
        # Email
        grid1.addWidget(QLabel('E-mail:'), 2, 0)
        self.email = QLineEdit()
        self.email.setPlaceholderText('exemplo@email.com')
        grid1.addWidget(self.email, 2, 1, 1, 3)
        
        # Celular
        grid1.addWidget(QLabel('Celular:'), 3, 0)
        self.celular = QLineEdit()
        self.celular.setPlaceholderText('(00) 00000-0000')
        grid1.addWidget(self.celular, 3, 1, 1, 3)
        
        # Grupo Endereço
        grupo2 = QGroupBox('Endereço')
        grid2 = QGridLayout()
        grupo2.setLayout(grid2)
        layout_form.addWidget(grupo2)
        
        # CEP
        grid2.addWidget(QLabel('CEP:'), 0, 0)
        self.cep = QLineEdit()
        self.cep.setPlaceholderText('00000-000')
        self.cep.textChanged.connect(self.verificar_cep)
        grid2.addWidget(self.cep, 0, 1)
        
        self.btn_consultar = QPushButton('🔍 Consultar')
        self.btn_consultar.clicked.connect(self.consultar_cep)
        grid2.addWidget(self.btn_consultar, 0, 2)
        
        # Logradouro
        grid2.addWidget(QLabel('Logradouro:'), 1, 0)
        self.logradouro = QLineEdit()
        grid2.addWidget(self.logradouro, 1, 1, 1, 2)
        
        # Número e Complemento
        grid2.addWidget(QLabel('Número:'), 2, 0)
        self.numero = QLineEdit()
        grid2.addWidget(self.numero, 2, 1)
        
        grid2.addWidget(QLabel('Complemento:'), 2, 2)
        self.complemento = QLineEdit()
        grid2.addWidget(self.complemento, 2, 3)
        
        # Bairro
        grid2.addWidget(QLabel('Bairro:'), 3, 0)
        self.bairro = QLineEdit()
        grid2.addWidget(self.bairro, 3, 1, 1, 3)
        
        # Cidade e Estado
        grid2.addWidget(QLabel('Cidade:'), 4, 0)
        self.cidade = QLineEdit()
        grid2.addWidget(self.cidade, 4, 1, 1, 2)
        
        grid2.addWidget(QLabel('Estado:'), 4, 3)
        self.estado = QLineEdit()
        self.estado.setPlaceholderText('UF')
        self.estado.setMaxLength(2)
        grid2.addWidget(self.estado, 4, 4)
        
        # Botões
        botoes = QHBoxLayout()
        botoes.addStretch()
        
        self.btn_salvar = QPushButton('💾 Salvar')
        self.btn_salvar.setStyleSheet('background-color: #27ae60; color: white; padding: 10px;')
        self.btn_salvar.clicked.connect(self.salvar)
        botoes.addWidget(self.btn_salvar)
        
        self.btn_limpar = QPushButton('🗑️ Limpar')
        self.btn_limpar.setStyleSheet('background-color: #e74c3c; color: white; padding: 10px;')
        self.btn_limpar.clicked.connect(self.limpar)
        botoes.addWidget(self.btn_limpar)
        
        botoes.addStretch()
        layout_form.addLayout(botoes)
        
        # Status
        self.status = QLabel('Pronto para cadastro')
        self.status.setStyleSheet('background-color: #ecf0f1; padding: 8px; border-radius: 4px;')
        layout_form.addWidget(self.status)
        
        # Estilo
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
        """)
    
    def trocar_placeholder_documento(self, tipo):
        if tipo == 'CPF':
            self.documento.setPlaceholderText('000.000.000-00')
        else:
            self.documento.setPlaceholderText('00.000.000/0000-00')
    
    def verificar_cep(self, texto):
        cep = re.sub(r'[^0-9]', '', texto)
        if len(cep) == 8:
            self.consultar_cep()
    
    def consultar_cep(self):
        cep = self.cep.text().strip()
        if not cep:
            QMessageBox.warning(self, 'Aviso', 'Digite um CEP')
            return
        
        if not Validador.cep(cep):
            QMessageBox.warning(self, 'Aviso', 'CEP inválido')
            return
        
        self.btn_consultar.setEnabled(False)
        self.btn_consultar.setText('⏳ Buscando...')
        self.status.setText('Consultando CEP...')
        
        self.thread_cep = ThreadCep(cep)
        self.thread_cep.resultado.connect(self.preencher_endereco)
        self.thread_cep.erro.connect(self.erro_consulta)
        self.thread_cep.finished.connect(self.finalizar_consulta)
        self.thread_cep.start()
    
    def preencher_endereco(self, dados):
        self.logradouro.setText(dados.get('logradouro', ''))
        self.bairro.setText(dados.get('bairro', ''))
        self.cidade.setText(dados.get('cidade', ''))
        self.estado.setText(dados.get('estado', ''))
        if dados.get('complemento'):
            self.complemento.setText(dados.get('complemento', ''))
        self.status.setText('Endereço preenchido com sucesso!')
        QMessageBox.information(self, 'Sucesso', 'Endereço encontrado e preenchido!')
    
    def erro_consulta(self, mensagem):
        QMessageBox.warning(self, 'Erro', mensagem)
        self.status.setText('Erro na consulta do CEP')
    
    def finalizar_consulta(self):
        self.btn_consultar.setEnabled(True)
        self.btn_consultar.setText('🔍 Consultar')
    
    def validar_campos(self):
        erros = []
        
        # Nome
        if not self.nome.text().strip():
            erros.append('Nome completo é obrigatório')
        
        # Documento
        doc = self.documento.text().strip()
        if not doc:
            erros.append('CPF/CNPJ é obrigatório')
        else:
            tipo = self.tipo_doc.currentText()
            if tipo == 'CPF' and not Validador.cpf(doc):
                erros.append('CPF inválido')
            elif tipo == 'CNPJ' and not Validador.cnpj(doc):
                erros.append('CNPJ inválido')
        
        # Email
        if not self.email.text().strip():
            erros.append('E-mail é obrigatório')
        elif not Validador.email(self.email.text()):
            erros.append('E-mail inválido')
        
        # Celular
        if not self.celular.text().strip():
            erros.append('Celular é obrigatório')
        elif not Validador.celular(self.celular.text()):
            erros.append('Celular inválido')
        
        # CEP
        if not self.cep.text().strip():
            erros.append('CEP é obrigatório')
        elif not Validador.cep(self.cep.text()):
            erros.append('CEP inválido')
        
        # Logradouro
        if not self.logradouro.text().strip():
            erros.append('Logradouro é obrigatório')
        
        # Número
        if not self.numero.text().strip():
            erros.append('Número é obrigatório')
        
        # Cidade
        if not self.cidade.text().strip():
            erros.append('Cidade é obrigatória')
        
        # Estado
        if not self.estado.text().strip():
            erros.append('Estado é obrigatório')
        elif len(self.estado.text().strip()) != 2:
            erros.append('Estado deve ter 2 letras (UF)')
        
        return erros
    
    def salvar(self):
        erros = self.validar_campos()
        
        if erros:
            msg = 'Corrija os seguintes erros:\n\n' + '\n'.join(f'• {e}' for e in erros)
            QMessageBox.warning(self, 'Erros no formulário', msg)
            self.status.setText(f'❌ {len(erros)} erro(s) encontrado(s)')
            return
        
        dados = {
            'nome': self.nome.text().strip(),
            'documento': re.sub(r'[^0-9]', '', self.documento.text()),
            'tipo': self.tipo_doc.currentText(),
            'email': self.email.text().strip(),
            'celular': re.sub(r'[^0-9]', '', self.celular.text()),
            'cep': re.sub(r'[^0-9]', '', self.cep.text()),
            'logradouro': self.logradouro.text().strip(),
            'numero': self.numero.text().strip(),
            'complemento': self.complemento.text().strip(),
            'bairro': self.bairro.text().strip(),
            'cidade': self.cidade.text().strip(),
            'estado': self.estado.text().strip().upper()
        }
        
        if self.banco.salvar(dados):
            QMessageBox.information(self, 'Sucesso', '✅ Cadastro realizado com sucesso!')
            self.status.setText('✅ Cadastro salvo com sucesso')
            self.limpar()
        else:
            QMessageBox.critical(self, 'Erro', '❌ Não foi possível salvar o cadastro')
            self.status.setText('❌ Erro ao salvar')
    
    def limpar(self):
        for campo in self.findChildren(QLineEdit):
            campo.clear()
        self.status.setText('Campos limpos')
        self.nome.setFocus()
    
    def closeEvent(self, event):
        """Fecha a conexão com o banco ao fechar a janela"""
        self.banco.fechar()
        event.accept()


# ===================== MAIN =====================
def main():
    app = QApplication(sys.argv)
    janela = JanelaCadastro()
    janela.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()