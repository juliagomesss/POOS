from datetime import datetime


class Usuario:

    def __init__(self, id, nome, email, login):

        self.id = id
        self.nome = nome
        self.email = email
        self.login = login
        self.data_cadastro = datetime.now()

        self.telefones = []
        self.enderecos = []

    def adicionar_telefone(self, telefone):
        self.telefones.append(telefone)

    def adicionar_endereco(self, endereco):
        self.enderecos.append(endereco)

    def exibir_usuario(self):

        print(f"\nUsuário: {self.nome}")
        print(f"Email: {self.email}")

        print("\nTelefones:")
        for telefone in self.telefones:
            print(f"- {telefone.numero}")

        print("\nEndereços:")
        for endereco in self.enderecos:
            endereco.exibir_endereco()


class Telefone:

    def __init__(self, numero):
        self.numero = numero


class Endereco:

    def __init__(self, rua, numero, cep, cidade, estado, pais):

        self.rua = rua
        self.numero = numero
        self.cep = cep
        self.cidade = cidade
        self.estado = estado
        self.pais = pais

    def exibir_endereco(self):

        print(
            f"{self.rua}, {self.numero} - "
            f"{self.cidade}/{self.estado} - "
            f"{self.pais}"
        )


class Cliente:

    def __init__(self, usuario):
        self.usuario = usuario

class Vendedor:

    def __init__(self, usuario):
        self.usuario = usuario


class Produto:

    def __init__(self, id, nome, preco, origem):

        self.id = id
        self.nome = nome
        self.preco = preco
        self.origem = origem
        self.data_cadastro = datetime.now()

    def exibir_produto(self):

        print(
            f"{self.nome} - "
            f"R$ {self.preco}"
        )


class Origem:

    def __init__(self, empresa):
        self.empresa = empresa


class ItemTransacao:

    def __init__(self, produto, quantidade):

        self.produto = produto
        self.quantidade = quantidade
        self.preco_unitario = produto.preco

    def subtotal(self):

        return (
            self.quantidade *
            self.preco_unitario
        )


class MetodoPagamento:

    def __init__(self, tipo):
        self.tipo = tipo


class TipoTransporte:

    def __init__(self, tipo):
        self.tipo = tipo


class Entrega:

    def __init__(self, taxa, frete, tipo_transporte):

        self.taxa = taxa
        self.frete = frete
        self.tipo_transporte = tipo_transporte

    def calcular_total_entrega(self):

        return self.taxa + self.frete


class Transacao:

    def __init__(self, id, cliente, vendedor, metodo_pagamento):

        self.id = id

        self.cliente = cliente
        self.vendedor = vendedor

        self.metodo_pagamento = metodo_pagamento

        self.data_transacao = datetime.now()

        self.itens = []

        self.entrega = None

    def adicionar_item(self, item):

        self.itens.append(item)

    def adicionar_entrega(self, entrega):

        self.entrega = entrega

    def calcular_total(self):

        total = 0

        for item in self.itens:
            total += item.subtotal()

        if self.entrega:
            total += self.entrega.calcular_total_entrega()

        return total

    def exibir_resumo(self):

        print("\n---------- Transação ----------")

        print(
            f"Cliente: "
            f"{self.cliente.usuario.nome}"
        )

        print(
            f"Vendedor: "
            f"{self.vendedor.usuario.nome}"
        )

        print(
            f"Pagamento: "
            f"{self.metodo_pagamento.tipo}"
        )

        print("\nItens:")

        for item in self.itens:

            print(
                f"{item.produto.nome} "
                f"x{item.quantidade} "
                f"= R$ {item.subtotal()}"
            )

        if self.entrega:

            print("\nEntrega:")
            print(
                f"Transporte: "
                f"{self.entrega.tipo_transporte.tipo}"
            )

            print(
                f"Frete: "
                f"R$ {self.entrega.frete}"
            )

        print(
            f"\nTotal: "
            f"R$ {self.calcular_total()}"
        )


usuario_cliente = Usuario(1, "Renjun", "renjun@email.com", "renjun123")


telefone1 = Telefone("127127127")


endereco1 = Endereco("Rua da SM", "127", "12712-767", "Seul", "Seoul", "Coreia")

usuario_cliente.adicionar_telefone(telefone1)
usuario_cliente.adicionar_endereco(endereco1)


cliente = Cliente(usuario_cliente)


usuario_vendedor = Usuario(2, "Mark", "mark@email.com", "mark123")

vendedor = Vendedor(usuario_vendedor)


origem = Origem("Dell")


photocard1 = Produto(1, "Photocard Ryo Ode to Love", 120, origem)

photocard2 = Produto(2, "Photocard Jaehee Steady", 80, origem)


item1 = ItemTransacao(photocard1, 1)
item2 = ItemTransacao(photocard2, 1)


pagamento = MetodoPagamento("Cartão")


transacao = Transacao(1, cliente, vendedor, pagamento)

transacao.adicionar_item(item1)
transacao.adicionar_item(item2)


tipo_transporte = TipoTransporte("Correios")

entrega = Entrega(10, 15, tipo_transporte)

transacao.adicionar_entrega(entrega)

usuario_cliente.exibir_usuario()

transacao.exibir_resumo()