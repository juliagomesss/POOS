import json
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, request, session, make_response

app = Flask(__name__)
app.secret_key = "itrades"

app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PHOTOCARDS = "photocards.json"
ARQUIVO_COMENTARIOS = "comentarios.json"
ARQUIVO_CHAT = "chat.json"


def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_usuarios():
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)


usuarios = carregar_usuarios()
for usuario, dados in usuarios.items():
    dados.setdefault("tipo", "cliente")
    dados.setdefault("carrinho", [])
    dados.setdefault("seguindo", [])
    dados.setdefault("tema", "claro")
    dados.setdefault("foto_perfil", "")

# PHOTOCARDS
if not os.path.exists(ARQUIVO_PHOTOCARDS):
    with open(ARQUIVO_PHOTOCARDS, "w", encoding="utf-8") as arquivo:
        json.dump([], arquivo)

with open(ARQUIVO_PHOTOCARDS, "r", encoding="utf-8") as arquivo:
    conteudo = arquivo.read().strip()
    if conteudo:
        photocards = json.loads(conteudo)
    else:
        photocards = []


# COMENTÁRIOS
if not os.path.exists(ARQUIVO_COMENTARIOS):
    with open(ARQUIVO_COMENTARIOS, "w", encoding="utf-8") as arquivo:
        json.dump({}, arquivo)

with open(ARQUIVO_COMENTARIOS, "r", encoding="utf-8") as arquivo:
    conteudo = arquivo.read().strip()
    if conteudo:
        comentarios = json.loads(conteudo)
    else:
        comentarios = {}


if not os.path.exists(ARQUIVO_CHAT):
    with open(ARQUIVO_CHAT, "w", encoding="utf-8") as arquivo:
        json.dump({}, arquivo)

with open(ARQUIVO_CHAT, "r", encoding="utf-8") as arquivo:
    conteudo = arquivo.read().strip()
    if conteudo:
        chat = json.loads(conteudo)
    else:
        chat = {}
    # Se o arquivo vier em formato antigo (lista), converte para dict vazio e persiste
    if isinstance(chat, list):
        chat = {}
        with open(ARQUIVO_CHAT, "w", encoding="utf-8") as arquivo2:
            json.dump(chat, arquivo2, indent=4, ensure_ascii=False)


@app.context_processor
def inject_chat_notifications():
    if "user" not in session:
        return {"novas_mensagens": 0}

    usuario = session["user"]
    contador = 0

    for key, msgs in chat.items():
        if ":" not in key or not msgs:
            continue

        pid_str, buyer = key.split(":", 1)
        try:
            pid = int(pid_str)
        except ValueError:
            continue

        card = next((c for c in photocards if c.get("id") == pid), None)
        if not card:
            continue

        seller = card.get("vendedor")
        if usuario != seller and usuario != buyer:
            continue

        last_msg = msgs[-1]
        if last_msg and last_msg.get("usuario") != usuario:
            contador += 1

    # Também conta propostas de troca pendentes para itens do usuário quando ele é vendedor.
    propostas = 0
    for card in photocards:
        if card.get("vendedor") == usuario and card.get("trocas"):
            propostas += len(card.get("trocas", []))

    return {"novas_mensagens": contador + propostas}


@app.route("/")
def inicio():
    return render_template(
        "inicio.html",
        cards=photocards,
        usuarios=usuarios
    )


@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").strip().lower()
    tipo = request.args.get("tipo", "produtos")

    if not q:
        return redirect(url_for("inicio"))

    if tipo == "usuarios":
        resultados = []
        for nome, dados in usuarios.items():
            if q in nome.lower() or q in dados.get("nome", "").lower() or q in dados.get("email", "").lower():
                resultados.append({
                    "usuario": nome,
                    "nome": dados.get("nome", ""),
                    "email": dados.get("email", ""),
                    "tipo": dados.get("tipo", "cliente"),
                    "foto_perfil": dados.get("foto_perfil", ""),
                    "seguindo": dados.get("seguindo", [])
                })
        resultados.sort(key=lambda item: item["usuario"].lower())
        return render_template("usuarios.html", resultados=resultados, query=q, usuarios=usuarios)

    resultados = [c for c in photocards if q in c.get("nome", "").lower() or q in c.get("grupo", "").lower() or q in c.get("descricao", "").lower()]
    return render_template("inicio.html", cards=resultados, usuarios=usuarios, query=q)



@app.route("/chat")
def chat_inbox():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = session["user"]

    # Se for vendedor, lista threads dos seus produtos
    threads = []
    for key, msgs in chat.items():
        # chave esperada: "{product_id}:{buyer}"
        if ":" in key:
            pid_str, buyer = key.split(":", 1)
            try:
                pid = int(pid_str)
            except ValueError:
                continue
            card = next((c for c in photocards if c.get("id") == pid), None)
            if not card:
                continue
            seller = card.get("vendedor")
            if usuario == seller or usuario == buyer:
                threads.append({"product": card, "buyer": buyer, "key": key, "last": msgs[-1] if msgs else None})

    return render_template("chat_threads.html", threads=threads, usuarios=usuarios)


@app.route("/chat/product/<int:product_id>", methods=["GET", "POST"])
def chat_product(product_id):
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = session["user"]
    card = next((c for c in photocards if c.get("id") == product_id), None)
    if not card:
        return redirect(url_for("inicio"))

    seller = card.get("vendedor")

    # Se for vendedor, pode especificar o comprador via query param
    if usuario == seller:
        buyer = request.args.get("user")
        if not buyer:
            # lista de conversas para este produto
            keys = [k for k in chat.keys() if k.startswith(f"{product_id}:")]
            buyers = [k.split(":", 1)[1] for k in keys]
            return render_template("chat_product_list.html", product=card, buyers=buyers, usuarios=usuarios)
    else:
        buyer = usuario

    if not buyer:
        return redirect(url_for("chat_inbox"))

    key = f"{product_id}:{buyer}"

    # Acesso permitido apenas ao vendedor e ao comprador
    if usuario != seller and usuario != buyer:
        return redirect(url_for("chat_inbox"))

    if request.method == "POST":
        mensagem = request.form.get("mensagem", "").strip()
        if mensagem:
            novo = {"usuario": usuario, "mensagem": mensagem}
            chat.setdefault(key, []).append(novo)
            with open(ARQUIVO_CHAT, "w", encoding="utf-8") as arquivo:
                json.dump(chat, arquivo, indent=4, ensure_ascii=False)
        return redirect(url_for("chat_product", product_id=product_id, user=buyer) if usuario == seller else url_for("chat_product", product_id=product_id))

    mensagens = chat.get(key, [])
    return render_template("chat_product.html", product=card, buyer=buyer, mensagens=mensagens, usuarios=usuarios)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and "user" in session:
        return redirect(url_for("perfil"))

    erro = None
    if request.method == "POST":
        user = request.form["user"]
        senha = request.form["senha"]

        if user not in usuarios:
            erro = "Usuário não existe."
        elif usuarios[user]["senha"] != senha:
            erro = "Usuário ou senha incorretos."
        else:
            session["user"] = user
            session.modified = True
            return redirect(url_for("perfil"))

    return render_template("login.html", erro=erro, usuarios=usuarios)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        user = request.form["user"]

        foto = request.files.get("foto_perfil")
        nome_arquivo = ""
        if foto and foto.filename:
            nome_arquivo = secure_filename(foto.filename)
            caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo)
            foto.save(caminho)

        usuarios[user] = {
            "senha": request.form["senha"],
            "nome": request.form["nome"],
            "email": request.form["email"],
            "tipo": "",
            "carrinho": [],
            "seguindo": [],
            "tema": "claro",
            "foto_perfil": nome_arquivo
        }

        salvar_usuarios()
        session["user"] = user
        return redirect(url_for("alterar_tipo"))

    return render_template("cadastro.html", usuarios=usuarios)


@app.route("/tipo", methods=["GET", "POST"])
def alterar_tipo():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        tipo = request.form.get("tipo")
        usuarios[session["user"]]["tipo"] = tipo
        salvar_usuarios()
        return redirect(url_for("inicio"))

    return render_template("tipo.html", usuarios=usuarios)


@app.route("/perfil")
def perfil():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = session["user"]
    if usuario not in usuarios:
        session.pop("user", None)
        return redirect(url_for("login"))

    info = usuarios[usuario]
    seguidores = [u for u, data in usuarios.items() if usuario in data.get("seguindo", [])]
    seguindo = info.get("seguindo", [])
    return render_template("perfil.html", usuario=usuario, info=info, usuarios=usuarios, seguidores=seguidores, seguindo=seguindo)


@app.route("/usuarios")
def usuarios_listar():
    q = request.args.get("q", "").strip().lower()
    resultados = []
    for nome, dados in usuarios.items():
        if not q or q in nome.lower() or q in dados.get("nome", "").lower() or q in dados.get("email", "").lower():
            resultados.append({
                "usuario": nome,
                "nome": dados.get("nome", ""),
                "email": dados.get("email", ""),
                "tipo": dados.get("tipo", "cliente"),
                "foto_perfil": dados.get("foto_perfil", ""),
                "seguindo": dados.get("seguindo", [])
            })
    resultados.sort(key=lambda item: item["usuario"].lower())
    return render_template("usuarios.html", resultados=resultados, query=q, usuarios=usuarios)


@app.route("/seguir/<usuario_alvo>")
def seguir_usuario(usuario_alvo):
    if "user" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["user"]
    if usuario_alvo not in usuarios or usuario_alvo == usuario_atual:
        return redirect(url_for("usuarios_listar"))

    usuarios[usuario_atual].setdefault("seguindo", [])
    if usuario_alvo not in usuarios[usuario_atual]["seguindo"]:
        usuarios[usuario_atual]["seguindo"].append(usuario_alvo)
        salvar_usuarios()

    return redirect(request.referrer or url_for("usuarios_listar"))


@app.route("/deixar_seguir/<usuario_alvo>")
def deixar_seguir_usuario(usuario_alvo):
    if "user" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["user"]
    if usuario_alvo not in usuarios or usuario_alvo == usuario_atual:
        return redirect(url_for("usuarios_listar"))

    seguindo = usuarios[usuario_atual].get("seguindo", [])
    if usuario_alvo in seguindo:
        seguindo.remove(usuario_alvo)
        usuarios[usuario_atual]["seguindo"] = seguindo
        salvar_usuarios()

    return redirect(request.referrer or url_for("usuarios_listar"))


@app.route("/produto/<int:id>")
def produto(id):
    card = next((c for c in photocards if c["id"] == id), None)
    # Recomendações: outros photocards do mesmo grupo (exceto o atual)
    if card:
        grupo = card.get("grupo")
        recomendacoes = [c for c in photocards if c.get("grupo") == grupo and c.get("id") != id]
    else:
        recomendacoes = []

    return render_template(
        "produto.html",
        card=card,
        recomendacoes=recomendacoes[:4],
        usuarios=usuarios
    )


@app.route("/anunciar", methods=["POST"])
def anunciar():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = usuarios[session["user"]]
    if usuario["tipo"] != "vendedor":
        return redirect(url_for("inicio"))

    foto = request.files.get("imagem")
    nome_arquivo = None

    if foto and foto.filename:
        nome_arquivo = secure_filename(foto.filename)
        caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo)
        foto.save(caminho)

    novo = {
        "id": len(photocards) + 1,
        "nome": request.form["nome"],
        "grupo": request.form["grupo"],
        "preco": request.form["preco"],
        "descricao": request.form["descricao"],
        "imagem": nome_arquivo,
        "vendedor": session["user"],
        "tipo_anuncio": request.form["tipo_anuncio"],
        "avaliacoes": [],
        "trocas": []
    }

    photocards.append(novo)

    with open(ARQUIVO_PHOTOCARDS, "w", encoding="utf-8") as arquivo:
        json.dump(photocards, arquivo, indent=4, ensure_ascii=False)

    return redirect(url_for("inicio"))


@app.route("/novo_photocard")
def novo_photocard():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = usuarios[session["user"]]
    if usuario["tipo"] != "vendedor":
        return redirect(url_for("inicio"))

    return render_template("novo_photocard.html", usuarios=usuarios)


@app.route("/meus_anuncios")
def meus_anuncios():
    if "user" not in session:
        return redirect(url_for("login"))

    meus = [card for card in photocards if card.get("vendedor") == session["user"]]
    return render_template("meus_anuncios.html", cards=meus, usuarios=usuarios)


@app.route("/logout")
def logout():
    session.clear()
    session.modified = True
    resp = make_response(redirect(url_for("login")))
    cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
    resp.set_cookie(cookie_name, "", expires=0, max_age=0, path="/")
    resp.delete_cookie(cookie_name, path="/")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


@app.route("/comprar/<int:id>")
def comprar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    carrinho = usuarios[session["user"]]["carrinho"]
    if id in carrinho:
        carrinho.remove(id)

    salvar_usuarios()
    return redirect(url_for("carrinho"))


@app.route("/comprar_tudo")
def comprar_tudo():
    if "user" not in session:
        return redirect(url_for("login"))

    usuarios[session["user"]]["carrinho"] = []
    salvar_usuarios()
    return redirect(url_for("carrinho"))


@app.route("/avaliar/<int:id>", methods=["POST"])
def avaliar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    card = next((c for c in photocards if c["id"] == id), None)
    if card:
        if "avaliacoes" not in card:
            card["avaliacoes"] = []

        nova = {
            "usuario": session["user"],
            "nota": request.form["nota"],
            "comentario": request.form["comentario"]
        }
        card["avaliacoes"].append(nova)

    with open(ARQUIVO_PHOTOCARDS, "w", encoding="utf-8") as arquivo:
        json.dump(photocards, arquivo, indent=4, ensure_ascii=False)

    # Também salva o comentário em comentarios.json (mapeado por id do photocard)
    chave = str(id)
    if chave not in comentarios:
        comentarios[chave] = []
    comentarios[chave].append(nova)
    with open(ARQUIVO_COMENTARIOS, "w", encoding="utf-8") as arquivo:
        json.dump(comentarios, arquivo, indent=4, ensure_ascii=False)

    return redirect(url_for("produto", id=id))


@app.route("/add_carrinho/<int:id>")
def add_carrinho(id):
    if "user" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["user"]
    
    # Garante que a lista do carrinho existe no usuário dentro do JSON
    if "carrinho" not in usuarios[usuario_atual]:
        usuarios[usuario_atual]["carrinho"] = []

    # Adiciona o ID do photocard ao carrinho do usuário se já não estiver lá
    if id not in usuarios[usuario_atual]["carrinho"]:
        usuarios[usuario_atual]["carrinho"].append(id)
        salvar_usuarios()

    return redirect(url_for("carrinho"))


@app.route("/troca/<int:id>", methods=["GET", "POST"])
def propor_troca(id):
    if "user" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["user"]
    card = next((c for c in photocards if c.get("id") == id), None)
    if not card:
        return redirect(url_for("inicio"))

    if card.get("vendedor") == usuario_atual:
        return redirect(url_for("produto", id=id))

    if card.get("tipo_anuncio") not in ("troca", "ambos"):
        return redirect(url_for("produto", id=id))

    if request.method == "POST":
        mensagem = request.form.get("mensagem", "").strip()
        if mensagem:
            troca = {
                "usuario": usuario_atual,
                "mensagem": mensagem
            }
            card.setdefault("trocas", []).append(troca)
            with open(ARQUIVO_PHOTOCARDS, "w", encoding="utf-8") as arquivo:
                json.dump(photocards, arquivo, indent=4, ensure_ascii=False)
        return redirect(url_for("produto", id=id))

    return render_template("troca.html", card=card, usuarios=usuarios)


@app.route("/carrinho")
def carrinho():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["user"]
    # Pega a lista de IDs salva no JSON do usuário
    ids = usuarios[usuario_atual].get("carrinho", [])

    # Remove IDs inválidos (que não existem mais em `photocards`) e persiste a limpeza
    valid_ids = [i for i in ids if any(card.get("id") == i for card in photocards)]
    if valid_ids != ids:
        usuarios[usuario_atual]["carrinho"] = valid_ids
        salvar_usuarios()
    
    # Filtra os photocards que estão com o ID nessa lista
    cards_no_carrinho = [card for card in photocards if card["id"] in valid_ids]

    return render_template("carrinho.html", cards=cards_no_carrinho, usuarios=usuarios)


@app.route("/remover_carrinho/<int:id>")
def remover_carrinho(id):
    if "user" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["user"]
    carrinho_usuario = usuarios[usuario_atual].get("carrinho", [])

    if id in carrinho_usuario:
        carrinho_usuario.remove(id)
        usuarios[usuario_atual]["carrinho"] = carrinho_usuario
        salvar_usuarios()

    return redirect(url_for("carrinho"))


@app.route("/remover_selecionados", methods=["POST"])
def remover_selecionados():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["user"]
    ids_para_remover = request.form.getlist("selecionados")
    ids_para_remover = [int(i) for i in ids_para_remover]

    carrinho_usuario = usuarios[usuario_atual].get("carrinho", [])
    
    # Mantém no carrinho apenas o que NÃO foi selecionado para remoção
    usuarios[usuario_atual]["carrinho"] = [item for item in carrinho_usuario if item not in ids_para_remover]
    salvar_usuarios()

    return redirect(url_for("carrinho"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user" not in session:
        return redirect(url_for("login"))

    selecionados = request.form.getlist("selecionados")
    ids = [int(i) for i in selecionados]
    cards = [card for card in photocards if card["id"] in ids]

    subtotal = sum(
        float(card["preco"].replace("R$", "").replace(",", ".").strip())
        for card in cards
    )

    taxa = subtotal * 0.08
    frete = 18.90 if cards else 0.0
    total = subtotal + taxa + frete

    if request.method == "POST" and request.form.get("endereco"):
        # Atualiza o carrinho do usuário no arquivo `usuarios.json` (mantém persistência)
        usuario_atual = session["user"]
        carrinho_usuario = usuarios[usuario_atual].get("carrinho", [])
        usuarios[usuario_atual]["carrinho"] = [item for item in carrinho_usuario if item not in ids]
        salvar_usuarios()
        return render_template("sucesso.html", total=total)

    return render_template(
        "checkout.html",
        cards=cards,
        subtotal=subtotal,
        taxa=taxa,
        frete=frete,
        total=total,
        ids=ids,
        usuarios=usuarios
    )


@app.route("/excluir_photocard/<int:id>")
def excluir_photocard(id):
    if "user" not in session:
        return redirect(url_for("login"))

    for card in photocards:
        if card["id"] == id and card.get("vendedor") == session["user"]:
            photocards.remove(card)
            with open(ARQUIVO_PHOTOCARDS, "w", encoding="utf-8") as arquivo:
                json.dump(photocards, arquivo, indent=4, ensure_ascii=False)
            break

    return redirect(url_for("meus_anuncios"))


@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = session["user"]

    if request.method == "POST":
        novo_email = request.form["email"]
        usuarios[usuario]["email"] = novo_email
        tema = request.form.get("tema")
        usuarios[usuario]["tema"] = tema
        foto = request.files.get("foto_perfil")
        if foto and foto.filename:
            nome_arquivo = secure_filename(foto.filename)
            caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo)
            foto.save(caminho)
            usuarios[usuario]["foto_perfil"] = nome_arquivo
        # Atualiza o tipo de usuário se fornecido
        tipo = request.form.get("tipo")
        if tipo in ("cliente", "vendedor"):
            usuarios[usuario]["tipo"] = tipo
        salvar_usuarios()
        return render_template("configuracoes.html", info=usuarios[usuario], usuarios=usuarios)

    return render_template("configuracoes.html", info=usuarios[usuario], usuarios=usuarios)


@app.route("/excluir_conta", methods=["POST"])
def excluir_conta():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = session["user"]
    senha_fornecida = request.form.get("senha_excluir", "")
    # Verifica senha antes de apagar a conta
    if not senha_fornecida or usuarios.get(usuario, {}).get("senha") != senha_fornecida:
        # Re-renderiza a página de configurações com mensagem de erro
        erro = "Senha incorreta. Conta não excluída."
        return render_template("configuracoes.html", info=usuarios[usuario], usuarios=usuarios, erro_excluir=erro)

    if usuario in usuarios:
        del usuarios[usuario]

    salvar_usuarios()
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/editar_photocard/<int:id>", methods=["GET", "POST"])
def editar_photocard(id):
    if "user" not in session:
        return redirect(url_for("login"))

    card = next((p for p in photocards if p["id"] == id), None)

    if card is None:
        return "Photocard não encontrado"

    if card["vendedor"] != session["user"]:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        card["nome"] = request.form["nome"]
        card["grupo"] = request.form["grupo"]
        card["preco"] = request.form["preco"]
        card["descricao"] = request.form["descricao"]

        with open(ARQUIVO_PHOTOCARDS, "w", encoding="utf-8") as arquivo:
            json.dump(photocards, arquivo, indent=4, ensure_ascii=False)

        return redirect(url_for("meus_anuncios"))

    return render_template("editar_photocard.html", card=card, usuarios=usuarios)


if __name__ == "__main__":
    app.run(debug=True)