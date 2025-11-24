import sqlite3
from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "segredo123"
bcrypt = Bcrypt(app)


# -----------------------------
# Conexão com banco
# -----------------------------
def conectar():
    return sqlite3.connect("banco.db")


# -----------------------------
# Criar tabelas
# -----------------------------
def criar_tabelas():
    con = conectar()
    cur = con.cursor()

    # Usuários
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    # Clientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    # Produtos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL
        )
    """)

    # Carrinho (relaciona cliente e produto)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carrinho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)

    # Usuário padrão
    cur.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cur.fetchone():
        senha_hash = bcrypt.generate_password_hash("123").decode('utf-8')
        cur.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ("admin", senha_hash))

    con.commit()
    con.close()


# -----------------------------
# AUTENTICAÇÃO
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT senha FROM usuarios WHERE username = ?", (usuario,))
        linha = cur.fetchone()
        con.close()

        if linha and bcrypt.check_password_hash(linha[0], senha):
            session["usuario"] = usuario
            return redirect("/home")
        else:
            return "Login inválido"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect("/")


@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect("/")
    return render_template("home.html", nome_usuario=session["usuario"])


# -----------------------------
# CRUD CLIENTES
# -----------------------------
@app.route("/clientes", methods=["GET"])
def clientes():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT * FROM clientes")
    dados = cur.fetchall()
    con.close()
    return render_template("clientes.html", clientes=dados)


@app.route("/clientes/add", methods=["GET", "POST"])
def clientes_add():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]

        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO clientes (nome, email) VALUES (?, ?)", (nome, email))
        con.commit()
        con.close()
        return redirect("/clientes")

    return render_template("add_cliente.html")


@app.route("/clientes/edit/<id>", methods=["GET", "POST"])
def clientes_edit(id):
    con = conectar()
    cur = con.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        cur.execute("UPDATE clientes SET nome=?, email=? WHERE id=?", (nome, email, id))
        con.commit()
        con.close()
        return redirect("/clientes")

    cur.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    cliente = cur.fetchone()
    con.close()
    return render_template("edit_cliente.html", cliente=cliente)


@app.route("/clientes/delete/<id>")
def clientes_delete(id):
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM clientes WHERE id = ?", (id,))
    con.commit()
    con.close()
    return redirect("/clientes")


# -----------------------------
# CRUD PRODUTOS
# -----------------------------
@app.route("/produtos", methods=["GET"])
def produtos():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT * FROM produtos")
    dados = cur.fetchall()
    con.close()
    return render_template("produtos.html", produtos=dados)


@app.route("/produtos/add", methods=["GET", "POST"])
def produtos_add():
    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])  # Conversão correta para float

        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
        con.commit()
        con.close()
        return redirect("/produtos")

    return render_template("add_produto.html")


@app.route("/produtos/edit/<id>", methods=["GET", "POST"])
def produtos_edit(id):
    con = conectar()
    cur = con.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        cur.execute("UPDATE produtos SET nome=?, preco=? WHERE id=?", (nome, preco, id))
        con.commit()
        con.close()
        return redirect("/produtos")

    cur.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    produto = cur.fetchone()
    con.close()
    return render_template("edit_produto.html", produto=produto)


@app.route("/produtos/delete/<id>")
def produtos_delete(id):
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM produtos WHERE id = ?", (id,))
    con.commit()
    con.close()
    return redirect("/produtos")


# -----------------------------
# CRUD CARRINHO
# -----------------------------
@app.route("/carrinho", methods=["GET"])
def carrinho():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT c.id, cli.nome, p.nome, p.preco, c.quantidade
        FROM carrinho c
        JOIN clientes cli ON c.cliente_id = cli.id
        JOIN produtos p ON c.produto_id = p.id
    """)
    dados = cur.fetchall()

    cur.execute("SELECT * FROM clientes")
    clientes = cur.fetchall()

    cur.execute("SELECT * FROM produtos")
    produtos = cur.fetchall()

    con.close()
    return render_template("carrinho.html", itens=dados, clientes=clientes, produtos=produtos)


@app.route("/carrinho/add", methods=["POST"])
def carrinho_add():
    cliente_id = request.form["cliente"]
    produto_id = request.form["produto"]
    quantidade = int(request.form["quantidade"])

    con = conectar()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO carrinho (cliente_id, produto_id, quantidade) 
        VALUES (?, ?, ?)
    """, (cliente_id, produto_id, quantidade))
    con.commit()
    con.close()
    return redirect("/carrinho")


@app.route("/carrinho/delete/<id>")
def carrinho_delete(id):
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM carrinho WHERE id = ?", (id,))
    con.commit()
    con.close()
    return redirect("/carrinho")


# -----------------------------
# INICIAR APP
# -----------------------------
if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
