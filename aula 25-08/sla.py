import tkinter as tk
from tkinter import messagebox
import sqlite3

# ===== CONEXÃO COM BANCO DE DADOS =====
def criar_banco():
    conn = sqlite3.connect('produtos.db')
    cursor = conn.cursor()
    
    # Cria a tabela se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT UNIQUE,
            nome TEXT NOT NULL,
            categoria TEXT,
            preco_venda REAL,
            estoque INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

criar_banco()

# ===== FUNÇÃO PARA SALVAR NO BANCO =====
def salvar_produto_db(codigo, nome, categoria, preco, estoque):
    try:
        conn = sqlite3.connect('produtos.db')
        cursor = conn.cursor()
        
        # Converte preço para float
        preco_float = float(preco.replace(',', '.'))
        
        cursor.execute('''
            INSERT INTO produtos (codigo_barras, nome, categoria, preco_venda, estoque)
            VALUES (?, ?, ?, ?, ?)
        ''', (codigo, nome, categoria, preco_float, int(estoque)))
        
        conn.commit()
        conn.close()
        
        return True
        
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Código de barras já existe no sistema!")
        return False
    except ValueError as e:
        messagebox.showerror("Erro", f"Erro no formato do preço: {e}")
        return False
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar: {e}")
        return False

# ===== INTERFACE =====
janela = tk.Tk()
janela.title("vendas")
janela.geometry("400x450")

# Título
titulo = tk.Label(janela, text="NOVO PRODUTO", font=("Arial", 14, "bold"))
titulo.pack(pady=10)

# Código
tk.Label(janela, text="Código de Barras:").pack()
entry_cod = tk.Entry(janela, width=30)
entry_cod.pack(pady=5)

# Nome
tk.Label(janela, text="Nome do Produto:").pack()
entry_nome = tk.Entry(janela, width=30)
entry_nome.pack(pady=5)

# Categoria
tk.Label(janela, text="Categoria:").pack()
categorias = ["Mercearia", "Hortifruti", "Açougue", "Bebidas", "Limpeza", "Padaria"]
categoria_var = tk.StringVar()
categoria_var.set(categorias[0])
menu_categoria = tk.OptionMenu(janela, categoria_var, *categorias)
menu_categoria.config(width=27)
menu_categoria.pack(pady=5)

# Preço
tk.Label(janela, text="Preço de Venda:").pack()
spin_preco = tk.Spinbox(janela, from_=0, to=9999, width=27, increment=0.01)
spin_preco.pack(pady=5)
spin_preco.delete(0, tk.END)
spin_preco.insert(0, "0.00")

# Estoque
tk.Label(janela, text="Estoque Inicial:").pack()
spin_estoque = tk.Spinbox(janela, from_=0, to=9999, width=27)
spin_estoque.pack(pady=5)
spin_estoque.delete(0, tk.END)
spin_estoque.insert(0, "0")

# Funções
def limpar():
    entry_cod.delete(0, tk.END)
    entry_nome.delete(0, tk.END)
    spin_preco.delete(0, tk.END)
    spin_preco.insert(0, "0.00")
    spin_estoque.delete(0, tk.END)
    spin_estoque.insert(0, "0")
    categoria_var.set(categorias[0])

def salvar():
    # Pega os valores dos campos
    codigo = entry_cod.get().strip()
    nome = entry_nome.get().strip()
    categoria = categoria_var.get()
    preco = spin_preco.get()
    estoque = spin_estoque.get()
    
    # Validações
    if codigo == "":
        messagebox.showwarning("Aviso", "Preencha o código de barras!")
        entry_cod.focus()
        return
    
    if nome == "":
        messagebox.showwarning("Aviso", "Preencha o nome do produto!")
        entry_nome.focus()
        return
    
    if preco == "0.00" or preco == "0":
        messagebox.showwarning("Aviso", "Defina um preço para o produto!")
        spin_preco.focus()
        return
    
    # Tenta salvar no banco
    if salvar_produto_db(codigo, nome, categoria, preco, estoque):
        messagebox.showinfo("Sucesso", "Produto salvo com sucesso!")
        limpar()  # Limpa o formulário após salvar

# Botões
frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=20)

tk.Button(
    frame_botoes, 
    text="Limpar", 
    command=limpar, 
    width=10
).pack(side=tk.LEFT, padx=10)

tk.Button(
    frame_botoes, 
    text="Salvar", 
    bg="green",
    fg="white",
    command=salvar, 
    width=10
).pack(side=tk.LEFT, padx=10)

janela.mainloop()