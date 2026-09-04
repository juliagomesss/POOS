"""Aplicação principal de cadastro de pessoas."""
import sys
import sqlite3
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QSpacerItem, QSizePolicy,
    QComboBox, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from models import Pessoa, Endereco
from validators import Validador
from cep_api import CepAPI
from database import Database


class TabelaPessoasWidget(QWidget):
    """Widget para exibir a tabela de pessoas cadastradas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.parent_app = parent
        self._setup_ui()
        self.carregar_dados()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        titulo = QLabel("Pessoas Cadastradas")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0;")
        layout.addWidget(titulo)
        
        # Tabela com 7 colunas
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "CPF/CNPJ", "Email", "Celular", "Endereço", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSortingEnabled(True)
        layout.addWidget(self.tabela)
        
        # Botão recarregar
        btn_layout = QHBoxLayout()
        self.btn_recarregar = QPushButton("Recarregar Lista")
        self.btn_recarregar.clicked.connect(self.carregar_dados)
        btn_layout.addWidget(self.btn_recarregar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def carregar_dados(self):
        """Carrega os dados do banco de dados na tabela."""
        pessoas = self.db.listar_pessoas()
        self.tabela.setRowCount(len(pessoas))
        
        for i, pessoa in enumerate(pessoas):
            self.tabela.setItem(i, 0, QTableWidgetItem(str(pessoa.id)))
            self.tabela.setItem(i, 1, QTableWidgetItem(pessoa.nome_completo))
            self.tabela.setItem(i, 2, QTableWidgetItem(pessoa.cpf_cnpj))
            self.tabela.setItem(i, 3, QTableWidgetItem(pessoa.email))
            self.tabela.setItem(i, 4, QTableWidgetItem(pessoa.celular))
            
            # Endereço resumido
            if pessoa.endereco:
                endereco_resumido = f"{pessoa.endereco.logradouro}, {pessoa.endereco.numero} - {pessoa.endereco.cidade}/{pessoa.endereco.estado}"
            else:
                endereco_resumido = "Sem endereço"
            self.tabela.setItem(i, 5, QTableWidgetItem(endereco_resumido))
            
            # Widget de ações (Editar + Deletar)
            widget_acoes = QWidget()
            layout_acoes = QHBoxLayout(widget_acoes)
            layout_acoes.setContentsMargins(5, 2, 5, 2)
            layout_acoes.setSpacing(5)
            
            # Botão Editar (AZUL)
            btn_editar = QPushButton("✏️")
            btn_editar.setFixedSize(30, 30)
            btn_editar.setToolTip("Editar cadastro")
            btn_editar.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            btn_editar.clicked.connect(lambda checked, id=pessoa.id: self.editar_pessoa(id))
            
            # Botão Deletar (VERMELHO)
            btn_deletar = QPushButton("🗑️")
            btn_deletar.setFixedSize(30, 30)
            btn_deletar.setToolTip("Deletar cadastro")
            btn_deletar.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            btn_deletar.clicked.connect(lambda checked, id=pessoa.id: self.deletar_pessoa(id))
            
            layout_acoes.addWidget(btn_editar)
            layout_acoes.addWidget(btn_deletar)
            layout_acoes.addStretch()
            
            self.tabela.setCellWidget(i, 6, widget_acoes)
        
        # Ajusta altura das linhas
        for i in range(len(pessoas)):
            self.tabela.setRowHeight(i, 40)
        
        if self.parent_app:
            self.parent_app.atualizar_status(f"{len(pessoas)} registros carregados", "info")
    
    def editar_pessoa(self, pessoa_id: int):
        """Abre o diálogo de edição para uma pessoa."""
        pessoas = self.db.listar_pessoas()
        pessoa = next((p for p in pessoas if p.id == pessoa_id), None)
        
        if not pessoa:
            QMessageBox.warning(self, "Erro", "Pessoa não encontrada!")
            return
        
        dialog = EditarPessoaDialog(self, pessoa)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()
            if self.parent_app:
                self.parent_app.atualizar_status("Cadastro editado com sucesso!", "sucesso")
    
    def deletar_pessoa(self, pessoa_id: int):
        """Deleta uma pessoa após confirmação."""
        resposta = QMessageBox.question(
            self,
            "Confirmar Deleção",
            f"Tem certeza que deseja deletar a pessoa com ID {pessoa_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if resposta == QMessageBox.Yes:
            try:
                self.db.deletar_pessoa(pessoa_id)
                self.carregar_dados()
                if self.parent_app:
                    self.parent_app.atualizar_status("Cadastro deletado com sucesso!", "sucesso")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao deletar cadastro:\n\n{str(e)}")


class EditarPessoaDialog(QDialog):
    """Diálogo para editar uma pessoa."""
    
    def __init__(self, parent, pessoa: Pessoa):
        super().__init__(parent)
        self.pessoa = pessoa
        self.db = Database()
        self.parent_app = parent.parent_app if hasattr(parent, 'parent_app') else None
        self._setup_ui()
        self._preencher_dados()
        self._conectar_sinais()
    
    def _setup_ui(self):
        """Configura a interface do diálogo de edição."""
        self.setWindowTitle(f"Editar Cadastro - ID {self.pessoa.id}")
        self.setMinimumSize(700, 650)
        self.setModal(True)
        
        layout_principal = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        conteudo = QWidget()
        layout = QVBoxLayout(conteudo)
        
        titulo = QLabel(f"Editando: {self.pessoa.nome_completo}")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 0;")
        layout.addWidget(titulo)
        
        # Grupo Dados Pessoais
        grupo_pessoal = QGroupBox("Dados Pessoais")
        layout_pessoal = QGridLayout(grupo_pessoal)
        layout_pessoal.setVerticalSpacing(15)
        layout_pessoal.setHorizontalSpacing(10)
        
        layout_pessoal.addWidget(QLabel("Nome Completo:*"), 0, 0)
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Digite o nome completo")
        layout_pessoal.addWidget(self.nome_input, 0, 1, 1, 2)
        
        layout_pessoal.addWidget(QLabel("CPF/CNPJ:*"), 1, 0)
        self.cpf_cnpj_input = QLineEdit()
        self.cpf_cnpj_input.setReadOnly(True)
        layout_pessoal.addWidget(self.cpf_cnpj_input, 1, 1, 1, 2)
        
        layout_pessoal.addWidget(QLabel("Email:*"), 2, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@email.com")
        layout_pessoal.addWidget(self.email_input, 2, 1, 1, 2)
        
        layout_pessoal.addWidget(QLabel("Celular:*"), 3, 0)
        self.celular_input = QLineEdit()
        self.celular_input.setPlaceholderText("(99) 99999-9999")
        layout_pessoal.addWidget(self.celular_input, 3, 1, 1, 2)
        
        layout.addWidget(grupo_pessoal)
        
        # Grupo Endereço
        grupo_endereco = QGroupBox("Endereço")
        layout_endereco = QGridLayout(grupo_endereco)
        layout_endereco.setVerticalSpacing(15)
        layout_endereco.setHorizontalSpacing(10)
        
        layout_endereco.addWidget(QLabel("CEP:*"), 0, 0)
        cep_layout = QHBoxLayout()
        self.cep_input = QLineEdit()
        self.cep_input.setPlaceholderText("Digite o CEP")
        self.cep_input.setFixedWidth(150)
        cep_layout.addWidget(self.cep_input)
        
        self.btn_consultar_cep = QPushButton("Consultar CEP")
        self.btn_consultar_cep.setFixedWidth(120)
        cep_layout.addWidget(self.btn_consultar_cep)
        cep_layout.addStretch()
        layout_endereco.addLayout(cep_layout, 0, 1, 1, 2)
        
        layout_endereco.addWidget(QLabel("Logradouro:*"), 1, 0)
        self.logradouro_input = QLineEdit()
        self.logradouro_input.setPlaceholderText("Rua, Avenida, etc.")
        layout_endereco.addWidget(self.logradouro_input, 1, 1, 1, 2)
        
        layout_endereco.addWidget(QLabel("Número:*"), 2, 0)
        self.numero_input = QLineEdit()
        self.numero_input.setPlaceholderText("Nº")
        self.numero_input.setFixedWidth(120)
        layout_endereco.addWidget(self.numero_input, 2, 1)
        
        layout_endereco.addWidget(QLabel("Complemento:"), 2, 2)
        self.complemento_input = QLineEdit()
        self.complemento_input.setPlaceholderText("Complemento (opcional)")
        layout_endereco.addWidget(self.complemento_input, 2, 3)
        
        layout_endereco.addWidget(QLabel("Bairro:*"), 3, 0)
        self.bairro_input = QLineEdit()
        self.bairro_input.setPlaceholderText("Bairro")
        layout_endereco.addWidget(self.bairro_input, 3, 1, 1, 3)
        
        layout_endereco.addWidget(QLabel("Cidade:*"), 4, 0)
        self.cidade_input = QLineEdit()
        self.cidade_input.setPlaceholderText("Cidade")
        layout_endereco.addWidget(self.cidade_input, 4, 1, 1, 2)
        
        layout_endereco.addWidget(QLabel("Estado:*"), 4, 3)
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
                                    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", 
                                    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
        self.estado_combo.setFixedWidth(80)
        layout_endereco.addWidget(self.estado_combo, 4, 4)
        
        layout.addWidget(grupo_endereco)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_salvar = QPushButton("Salvar Alterações")
        self.btn_salvar.setFixedHeight(40)
        self.btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedHeight(40)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        btn_layout.addWidget(self.btn_salvar)
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        scroll.setWidget(conteudo)
        layout_principal.addWidget(scroll)
    
    def _preencher_dados(self):
        """Preenche os campos com os dados da pessoa."""
        self.nome_input.setText(self.pessoa.nome_completo)
        self.cpf_cnpj_input.setText(self.pessoa.cpf_cnpj)
        self.email_input.setText(self.pessoa.email)
        self.celular_input.setText(self.pessoa.celular)
        
        if self.pessoa.endereco:
            self.cep_input.setText(self.pessoa.endereco.cep)
            self.logradouro_input.setText(self.pessoa.endereco.logradouro)
            self.numero_input.setText(self.pessoa.endereco.numero)
            self.complemento_input.setText(self.pessoa.endereco.complemento)
            self.bairro_input.setText(self.pessoa.endereco.bairro)
            self.cidade_input.setText(self.pessoa.endereco.cidade)
            self.estado_combo.setCurrentText(self.pessoa.endereco.estado)
    
    def _conectar_sinais(self):
        """Conecta os sinais aos slots."""
        self.btn_consultar_cep.clicked.connect(self.consultar_cep)
        self.btn_salvar.clicked.connect(self.salvar_alteracoes)
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.cep_input.textChanged.connect(self._aplicar_mascara_cep)
        self.celular_input.textChanged.connect(self._aplicar_mascara_celular)
    
    def _aplicar_mascara_cep(self, texto: str):
        texto = ''.join(filter(str.isdigit, texto))
        if len(texto) > 8:
            texto = texto[:8]
        if len(texto) > 5:
            texto = f"{texto[:5]}-{texto[5:]}"
        self.cep_input.blockSignals(True)
        self.cep_input.setText(texto)
        self.cep_input.blockSignals(False)
    
    def _aplicar_mascara_celular(self, texto: str):
        texto = ''.join(filter(str.isdigit, texto))
        if len(texto) > 11:
            texto = texto[:11]
        if len(texto) > 2:
            texto = f"({texto[:2]}) {texto[2:]}"
        if len(texto) > 10:
            texto = f"{texto[:10]}-{texto[10:]}"
        elif len(texto) > 9:
            texto = f"{texto[:9]}-{texto[9:]}"
        self.celular_input.blockSignals(True)
        self.celular_input.setText(texto)
        self.celular_input.blockSignals(False)
    
    def consultar_cep(self):
        """Consulta o CEP na API."""
        cep = self.cep_input.text()
        if not cep:
            QMessageBox.warning(self, "Aviso", "Digite um CEP para consultar.")
            return
        
        cep_limpo = ''.join(filter(str.isdigit, cep))
        if len(cep_limpo) != 8:
            QMessageBox.warning(self, "Aviso", "CEP inválido. Digite um CEP com 8 dígitos.")
            return
        
        self.btn_consultar_cep.setEnabled(False)
        self.btn_consultar_cep.setText("Consultando...")
        
        try:
            dados = CepAPI.consultar(cep_limpo)
            if dados:
                self.logradouro_input.setText(dados['logradouro'])
                self.bairro_input.setText(dados['bairro'])
                self.cidade_input.setText(dados['cidade'])
                self.estado_combo.setCurrentText(dados['estado'])
                if self.parent_app:
                    self.parent_app.atualizar_status("CEP encontrado!", "sucesso")
            else:
                QMessageBox.warning(self, "CEP não encontrado", "O CEP informado não foi encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao consultar CEP:\n\n{str(e)}")
        finally:
            self.btn_consultar_cep.setEnabled(True)
            self.btn_consultar_cep.setText("Consultar CEP")
    
    def salvar_alteracoes(self):
        """Salva as alterações no banco de dados."""
        nome = self.nome_input.text().strip()
        email = self.email_input.text().strip()
        celular = self.celular_input.text().strip()
        cep = self.cep_input.text().strip()
        logradouro = self.logradouro_input.text().strip()
        numero = self.numero_input.text().strip()
        complemento = self.complemento_input.text().strip()
        bairro = self.bairro_input.text().strip()
        cidade = self.cidade_input.text().strip()
        estado = self.estado_combo.currentText()
        
        erros = []
        if not nome:
            erros.append("Nome completo é obrigatório")
        if not email:
            erros.append("Email é obrigatório")
        elif not Validador.validar_email(email):
            erros.append("Email inválido")
        if not celular:
            erros.append("Celular é obrigatório")
        elif not Validador.validar_celular(celular):
            erros.append("Celular inválido")
        if not cep:
            erros.append("CEP é obrigatório")
        elif not Validador.validar_cep(cep):
            erros.append("CEP inválido")
        if not logradouro:
            erros.append("Logradouro é obrigatório")
        if not numero:
            erros.append("Número é obrigatório")
        if not bairro:
            erros.append("Bairro é obrigatório")
        if not cidade:
            erros.append("Cidade é obrigatória")
        if not estado:
            erros.append("Estado é obrigatório")
        
        if erros:
            mensagem = "Por favor, corrija os seguintes erros:\n\n" + "\n".join(f"• {erro}" for erro in erros)
            QMessageBox.warning(self, "Erros de Validação", mensagem)
            return
        
        self.pessoa.nome_completo = nome
        self.pessoa.email = email
        self.pessoa.celular = celular
        
        if self.pessoa.endereco:
            self.pessoa.endereco.cep = cep
            self.pessoa.endereco.logradouro = logradouro
            self.pessoa.endereco.numero = numero
            self.pessoa.endereco.complemento = complemento
            self.pessoa.endereco.bairro = bairro
            self.pessoa.endereco.cidade = cidade
            self.pessoa.endereco.estado = estado
        
        try:
            self.db.atualizar_pessoa(self.pessoa)
            QMessageBox.information(self, "Sucesso!", "Cadastro atualizado com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar alterações:\n\n{str(e)}")


class CadastroPessoaWidget(QWidget):
    """Widget para formulário de cadastro de pessoas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.parent_app = parent
        self._setup_ui()
        self._conectar_sinais()
    
    def _setup_ui(self):
        """Configura a interface do formulário."""
        layout_principal = QVBoxLayout(self)
        
        titulo = QLabel("Novo Cadastro")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0;")
        layout_principal.addWidget(titulo)
        
        # Grupo de Dados Pessoais
        grupo_pessoal = QGroupBox("Dados Pessoais")
        layout_pessoal = QGridLayout(grupo_pessoal)
        layout_pessoal.setVerticalSpacing(15)
        layout_pessoal.setHorizontalSpacing(10)
        
        layout_pessoal.addWidget(QLabel("Nome Completo:*"), 0, 0)
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Digite o nome completo")
        layout_pessoal.addWidget(self.nome_input, 0, 1, 1, 2)
        
        layout_pessoal.addWidget(QLabel("CPF/CNPJ:*"), 1, 0)
        self.cpf_cnpj_input = QLineEdit()
        self.cpf_cnpj_input.setPlaceholderText("Digite o CPF ou CNPJ (apenas números)")
        layout_pessoal.addWidget(self.cpf_cnpj_input, 1, 1, 1, 2)
        
        layout_pessoal.addWidget(QLabel("Email:*"), 2, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@email.com")
        self.email_input.setStyleSheet("text-transform: lowercase;")
        layout_pessoal.addWidget(self.email_input, 2, 1, 1, 2)
        
        layout_pessoal.addWidget(QLabel("Celular:*"), 3, 0)
        self.celular_input = QLineEdit()
        self.celular_input.setPlaceholderText("(99) 99999-9999")
        layout_pessoal.addWidget(self.celular_input, 3, 1, 1, 2)
        
        layout_principal.addWidget(grupo_pessoal)
        
        # Grupo de Endereço
        grupo_endereco = QGroupBox("Endereço")
        layout_endereco = QGridLayout(grupo_endereco)
        layout_endereco.setVerticalSpacing(15)
        layout_endereco.setHorizontalSpacing(10)
        
        layout_endereco.addWidget(QLabel("CEP:*"), 0, 0)
        cep_layout = QHBoxLayout()
        self.cep_input = QLineEdit()
        self.cep_input.setPlaceholderText("Digite o CEP (apenas números)")
        self.cep_input.setFixedWidth(150)
        cep_layout.addWidget(self.cep_input)
        
        self.btn_consultar_cep = QPushButton("Consultar CEP")
        self.btn_consultar_cep.setFixedWidth(120)
        cep_layout.addWidget(self.btn_consultar_cep)
        cep_layout.addStretch()
        layout_endereco.addLayout(cep_layout, 0, 1, 1, 2)
        
        layout_endereco.addWidget(QLabel("Logradouro:*"), 1, 0)
        self.logradouro_input = QLineEdit()
        self.logradouro_input.setPlaceholderText("Rua, Avenida, etc.")
        layout_endereco.addWidget(self.logradouro_input, 1, 1, 1, 2)
        
        layout_endereco.addWidget(QLabel("Número:*"), 2, 0)
        self.numero_input = QLineEdit()
        self.numero_input.setPlaceholderText("Nº")
        self.numero_input.setFixedWidth(120)
        layout_endereco.addWidget(self.numero_input, 2, 1)
        
        layout_endereco.addWidget(QLabel("Complemento:"), 2, 2)
        self.complemento_input = QLineEdit()
        self.complemento_input.setPlaceholderText("Complemento (opcional)")
        layout_endereco.addWidget(self.complemento_input, 2, 3)
        
        layout_endereco.addWidget(QLabel("Bairro:*"), 3, 0)
        self.bairro_input = QLineEdit()
        self.bairro_input.setPlaceholderText("Bairro")
        layout_endereco.addWidget(self.bairro_input, 3, 1, 1, 3)
        
        layout_endereco.addWidget(QLabel("Cidade:*"), 4, 0)
        self.cidade_input = QLineEdit()
        self.cidade_input.setPlaceholderText("Cidade")
        layout_endereco.addWidget(self.cidade_input, 4, 1, 1, 2)
        
        layout_endereco.addWidget(QLabel("Estado:*"), 4, 3)
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
                                    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", 
                                    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
        self.estado_combo.setFixedWidth(80)
        layout_endereco.addWidget(self.estado_combo, 4, 4)
        
        layout_principal.addWidget(grupo_endereco)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_salvar = QPushButton("Salvar Cadastro")
        self.btn_salvar.setFixedHeight(40)
        self.btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_limpar = QPushButton("Limpar Campos")
        self.btn_limpar.setFixedHeight(40)
        self.btn_limpar.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        btn_layout.addWidget(self.btn_salvar)
        btn_layout.addWidget(self.btn_limpar)
        btn_layout.addStretch()
        
        layout_principal.addLayout(btn_layout)
        layout_principal.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def _conectar_sinais(self):
        """Conecta os sinais aos slots."""
        self.btn_consultar_cep.clicked.connect(self.consultar_cep)
        self.btn_salvar.clicked.connect(self.salvar_cadastro)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        
        self.cep_input.textChanged.connect(self._aplicar_mascara_cep)
        self.cpf_cnpj_input.textChanged.connect(self._aplicar_mascara_cpf_cnpj)
        self.celular_input.textChanged.connect(self._aplicar_mascara_celular)
    
    def _aplicar_mascara_cep(self, texto: str):
        texto = ''.join(filter(str.isdigit, texto))
        if len(texto) > 8:
            texto = texto[:8]
        if len(texto) > 5:
            texto = f"{texto[:5]}-{texto[5:]}"
        self.cep_input.blockSignals(True)
        self.cep_input.setText(texto)
        self.cep_input.blockSignals(False)
    
    def _aplicar_mascara_cpf_cnpj(self, texto: str):
        texto = ''.join(filter(str.isdigit, texto))
        if len(texto) > 14:
            texto = texto[:14]
        if len(texto) <= 11:
            if len(texto) >= 4:
                texto = f"{texto[:3]}.{texto[3:]}"
            if len(texto) >= 8:
                texto = f"{texto[:7]}.{texto[7:]}"
            if len(texto) >= 12:
                texto = f"{texto[:11]}-{texto[11:]}"
        else:
            if len(texto) >= 3:
                texto = f"{texto[:2]}.{texto[2:]}"
            if len(texto) >= 7:
                texto = f"{texto[:6]}.{texto[6:]}"
            if len(texto) >= 11:
                texto = f"{texto[:10]}/{texto[10:]}"
            if len(texto) >= 15:
                texto = f"{texto[:14]}-{texto[14:]}"
        self.cpf_cnpj_input.blockSignals(True)
        self.cpf_cnpj_input.setText(texto)
        self.cpf_cnpj_input.blockSignals(False)
    
    def _aplicar_mascara_celular(self, texto: str):
        texto = ''.join(filter(str.isdigit, texto))
        if len(texto) > 11:
            texto = texto[:11]
        if len(texto) > 2:
            texto = f"({texto[:2]}) {texto[2:]}"
        if len(texto) > 10:
            texto = f"{texto[:10]}-{texto[10:]}"
        elif len(texto) > 9:
            texto = f"{texto[:9]}-{texto[9:]}"
        self.celular_input.blockSignals(True)
        self.celular_input.setText(texto)
        self.celular_input.blockSignals(False)
    
    def consultar_cep(self):
        """Consulta o CEP na API."""
        cep = self.cep_input.text()
        if not cep:
            QMessageBox.warning(self, "Aviso", "Digite um CEP para consultar.")
            return
        cep_limpo = ''.join(filter(str.isdigit, cep))
        if len(cep_limpo) != 8:
            QMessageBox.warning(self, "Aviso", "CEP inválido. Digite um CEP com 8 dígitos.")
            return
        self.btn_consultar_cep.setEnabled(False)
        self.btn_consultar_cep.setText("⏳ Consultando...")
        try:
            dados = CepAPI.consultar(cep_limpo)
            if dados:
                self.logradouro_input.setText(dados['logradouro'])
                self.bairro_input.setText(dados['bairro'])
                self.cidade_input.setText(dados['cidade'])
                self.estado_combo.setCurrentText(dados['estado'])
                if self.parent_app:
                    self.parent_app.atualizar_status("CEP encontrado!", "sucesso")
            else:
                QMessageBox.warning(self, "CEP não encontrado", "O CEP informado não foi encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao consultar CEP:\n\n{str(e)}")
        finally:
            self.btn_consultar_cep.setEnabled(True)
            self.btn_consultar_cep.setText("Consultar CEP")
    
    def salvar_cadastro(self):
        """Salva o cadastro no banco de dados."""
        nome = self.nome_input.text().strip()
        cpf_cnpj = self.cpf_cnpj_input.text().strip()
        email = self.email_input.text().strip()
        celular = self.celular_input.text().strip()
        cep = self.cep_input.text().strip()
        logradouro = self.logradouro_input.text().strip()
        numero = self.numero_input.text().strip()
        complemento = self.complemento_input.text().strip()
        bairro = self.bairro_input.text().strip()
        cidade = self.cidade_input.text().strip()
        estado = self.estado_combo.currentText()
        
        erros = []
        if not nome:
            erros.append("Nome completo é obrigatório")
        if not cpf_cnpj:
            erros.append("CPF/CNPJ é obrigatório")
        else:
            cpf_cnpj_limpo = ''.join(filter(str.isdigit, cpf_cnpj))
            valido, tipo = Validador.validar_cpf_cnpj(cpf_cnpj_limpo)
            if not valido:
                erros.append(f"{tipo} inválido")
        if not email:
            erros.append("Email é obrigatório")
        elif not Validador.validar_email(email):
            erros.append("Email inválido")
        if not celular:
            erros.append("Celular é obrigatório")
        elif not Validador.validar_celular(celular):
            erros.append("Celular inválido")
        if not cep:
            erros.append("CEP é obrigatório")
        elif not Validador.validar_cep(cep):
            erros.append("CEP inválido")
        if not logradouro:
            erros.append("Logradouro é obrigatório")
        if not numero:
            erros.append("Número é obrigatório")
        if not bairro:
            erros.append("Bairro é obrigatório")
        if not cidade:
            erros.append("Cidade é obrigatória")
        if not estado:
            erros.append("Estado é obrigatório")
        
        if erros:
            mensagem = "Por favor, corrija os seguintes erros:\n\n" + "\n".join(f"• {erro}" for erro in erros)
            QMessageBox.warning(self, "Erros de Validação", mensagem)
            if self.parent_app:
                self.parent_app.atualizar_status("Corrija os erros no formulário", "erro")
            return
        
        endereco = Endereco(cep=cep, logradouro=logradouro, numero=numero,
                           complemento=complemento, bairro=bairro, cidade=cidade, estado=estado)
        pessoa = Pessoa(nome_completo=nome, cpf_cnpj=cpf_cnpj, email=email,
                       celular=celular, endereco=endereco)
        
        try:
            self.db.salvar_pessoa(pessoa)
            QMessageBox.information(self, "Sucesso!", "Cadastro realizado com sucesso!")
            if self.parent_app:
                self.parent_app.atualizar_status("Cadastro realizado com sucesso!", "sucesso")
                self.parent_app.recarregar_tabela()
            self.limpar_campos()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Já existe um cadastro com este CPF/CNPJ.")
            if self.parent_app:
                self.parent_app.atualizar_status("CPF/CNPJ já cadastrado", "erro")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar cadastro:\n\n{str(e)}")
    
    def limpar_campos(self):
        """Limpa todos os campos do formulário."""
        self.nome_input.clear()
        self.cpf_cnpj_input.clear()
        self.email_input.clear()
        self.celular_input.clear()
        self.cep_input.clear()
        self.logradouro_input.clear()
        self.numero_input.clear()
        self.complemento_input.clear()
        self.bairro_input.clear()
        self.cidade_input.clear()
        self.estado_combo.setCurrentIndex(0)
        self.nome_input.setFocus()
        if self.parent_app:
            self.parent_app.atualizar_status("Campos limpos", "info")


class MainWindow(QMainWindow):
    """Janela principal da aplicação."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Cadastro de Pessoas")
        self.setMinimumSize(900, 700)
        
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Pronto")
        self.status_bar.addWidget(self.status_label)
        self.status_bar.setStyleSheet("QStatusBar { background-color: #f0f0f0; }")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
            }
            QTabBar::tab {
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078d7;
                color: white;
            }
        """)
        
        self.cadastro_widget = CadastroPessoaWidget(self)
        self.tabs.addTab(self.cadastro_widget, "Novo Cadastro")
        
        self.tabela_widget = TabelaPessoasWidget(self)
        self.tabs.addTab(self.tabela_widget, "Listar Cadastros")
        
        layout_principal.addWidget(self.tabs)
    
    def atualizar_status(self, mensagem: str, tipo: str = "info"):
        cores = {
            "info": "#2196F3",
            "sucesso": "#4CAF50",
            "erro": "#f44336",
            "aviso": "#FF9800"
        }
        cor = cores.get(tipo, "#2196F3")
        self.status_label.setText(mensagem)
        self.status_bar.setStyleSheet(f"QStatusBar {{ background-color: {cor}; color: white; padding: 5px; }}")
    
    def recarregar_tabela(self):
        self.tabela_widget.carregar_dados()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()