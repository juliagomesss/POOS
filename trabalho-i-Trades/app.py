import json
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, request, session

app = Flask(__name__)
app.secret_key = "itrades"

app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PHOTOCARDS = "photocards.json"
ARQUIVO_COMENTARIOS = "comentarios.json"


def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_usuarios():
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)


usuarios = carregar_usuarios()

photocards = [
    {
        "id": 1,
        "nome": "Jungkook Golden",
        "grupo": "BTS",
        "preco": "R$120",
        "descricao": "Photocard oficial álbum Golden",
        "imagem": None
    },
    {
        "id": 2,
        "nome": "Karina Drama",
        "grupo": "aespa",
        "preco": "R$95",
        "descricao": "Versão exclusiva",
        "imagem": None
    }
]

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


@app.route("/")
def inicio():
    return render_template("inicio.html", cards=photocards)


@app.route("/login", methods=["GET", "POST"])
def login():
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
            return redirect(url_for("perfil"))

    return render_template("login.html", erro=erro)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        user = request.form["user"]

        usuarios[user] = {
            "senha": request.form["senha"],
            "nome": request.form["nome"],
            "email": request.form["email"],
            "tipo": "cliente",
            "carrinho": []
        }

        salvar_usuarios()

        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/alterar_tipo", methods=["POST"])
def alterar_tipo():
    if "user" not in session:
        return redirect(url_for("login"))

    tipo = request.form["tipo"]
    usuarios[session["user"]]["tipo"] = request.form["tipo"]
    salvar_usuarios()

    return redirect(url_for("perfil"))


@app.route("/perfil")
def perfil():
    if "user" not in session:
        return redirect(url_for("login"))

    usuario = session["user"]

    if usuario not in usuarios:
        session.pop("user", None)
        return redirect(url_for("login"))

    info = usuarios[usuario]

    return render_template(
        "perfil.html",
        usuario=usuario,
        info=info
    )


@app.route("/produto/<int:id>")
def produto(id):
    card = next((c for c in photocards if c["id"] == id), None)
    return render_template(
        "produto.html",
        card=card,
        usuarios=usuarios
    )


@app.route("/anunciar", methods=["POST"])
def anunciar():

    if "user" not in session:
        return redirect(url_for("login"))

    foto = request.files.get("foto")

    nome_arquivo = None

    if foto and foto.filename:

        nome_arquivo = secure_filename(foto.filename)

        caminho = os.path.join(
            app.config["UPLOAD_FOLDER"],
            nome_arquivo
        )

        foto.save(caminho)

    novo = {
        "id": len(photocards)+1,
        "nome": request.form["nome"],
        "grupo": request.form["grupo"],
        "preco": request.form["preco"],
        "descricao": request.form["descricao"],
        "imagem": nome_arquivo,
        "avaliacoes": []
    }

    photocards.append(novo)

    with open(ARQUIVO_PHOTOCARDS, "w", encoding="utf-8") as arquivo:
        json.dump(
            photocards,
            arquivo,
            indent=4,
            ensure_ascii=False
        )

    return redirect(url_for("inicio"))

    
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("inicio"))

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
        json.dump(
            photocards,
            arquivo,
            indent=4,
            ensure_ascii=False
        )

    return redirect(url_for("produto", id=id))


@app.route("/add_carrinho/<int:id>")
def add_carrinho(id):

    if "user" not in session:
        return redirect(url_for("login"))

    if "carrinho" not in session:
        session["carrinho"] = []

    session["carrinho"].append(id)
    session.modified = True

    return redirect(url_for("carrinho"))


@app.route("/carrinho")
def carrinho():

    ids = session.get("carrinho", [])

    cards = [
        card for card in photocards
        if card["id"] in ids
    ]

    return render_template(
        "carrinho.html",
        cards=cards
    )


@app.route("/remover_carrinho/<int:id>")
def remover_carrinho(id):

    if "carrinho" in session:

        session["carrinho"] = [
            item for item in session["carrinho"]
            if item != id
        ]

        session.modified = True

    return redirect(url_for("carrinho"))


@app.route("/checkout", methods=["GET","POST"])
def checkout():

    if "user" not in session:
        return redirect(url_for("login"))

    selecionados = request.form.getlist("selecionados")

    ids = [int(i) for i in selecionados]

    cards = [
        card for card in photocards
        if card["id"] in ids
    ]

    subtotal = sum(
        float(
            card["preco"]
            .replace("R$","")
            .replace(",",".")
        )
        for card in cards
    )

    taxa = subtotal * 0.08
    frete = 18.90
    total = subtotal + taxa + frete

    if request.method == "POST" and request.form.get("endereco"):

        session["carrinho"] = [
            item for item in session["carrinho"]
            if item not in ids
        ]

        session.modified = True

        return render_template(
            "sucesso.html",
            total=total
        )

    return render_template(
        "checkout.html",
        cards=cards,
        subtotal=subtotal,
        taxa=taxa,
        frete=frete,
        total=total,
        ids=ids
    )

@app.route("/remover_selecionados", methods=["POST"])
def remover_selecionados():

    ids = request.form.getlist("selecionados")
    ids = [int(i) for i in ids]

    session["carrinho"] = [
        item for item in session["carrinho"]
        if item not in ids
    ]

    session.modified = True

    return redirect(url_for("carrinho"))

if __name__ == "__main__":
    app.run(debug=True)