from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "123"

# -------- BANCO --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "farmacia.db")

def db():
    return sqlite3.connect(db_path)

def criar():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY,
        user TEXT,
        senha TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS produtos(
        id INTEGER PRIMARY KEY,
        nome TEXT,
        preco REAL,
        estoque INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS vendas(
        id INTEGER PRIMARY KEY,
        produto TEXT,
        quantidade INTEGER,
        total REAL
    )
    """)

    # 👇 cria usuário padrão
    c.execute("INSERT OR IGNORE INTO usuarios(id, user, senha) VALUES (1, 'admin', '123')")

    conn.commit()
    conn.close()

# 🔥 ESSA LINHA RESOLVE SEU ERRO NO RENDER
criar()

# -------- LOGIN --------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        senha = request.form["senha"]

        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE user=? AND senha=?", (user, senha))
        usuario = c.fetchone()
        conn.close()

        if usuario:
            session["user"] = user
            return redirect("/dashboard")

    return render_template("login.html")

# -------- DASHBOARD --------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = db()
    c = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        preco = request.form["preco"]
        estoque = request.form["estoque"]

        c.execute("INSERT INTO produtos(nome, preco, estoque) VALUES(?,?,?)",
                  (nome, preco, estoque))
        conn.commit()

    c.execute("SELECT * FROM produtos")
    produtos = c.fetchall()
    conn.close()

    return render_template("dashboard.html", produtos=produtos)

# -------- VENDAS --------
@app.route("/vendas", methods=["GET","POST"])
def vendas():
    conn = db()
    c = conn.cursor()

    if request.method == "POST":
        produto_id = request.form["produto"]
        qtd = int(request.form["qtd"])

        c.execute("SELECT nome, preco, estoque FROM produtos WHERE id=?", (produto_id,))
        p = c.fetchone()

        if p:
            nome, preco, estoque = p

            if qtd > estoque:
                return "Estoque insuficiente"

            total = preco * qtd

            novo = estoque - qtd
            c.execute("UPDATE produtos SET estoque=? WHERE id=?", (novo, produto_id))

            c.execute("INSERT INTO vendas(produto, quantidade, total) VALUES(?,?,?)",
                      (nome, qtd, total))

            conn.commit()

    c.execute("SELECT * FROM produtos")
    produtos = c.fetchall()

    c.execute("SELECT * FROM vendas")
    vendas = c.fetchall()

    conn.close()

    return render_template("vendas.html", produtos=produtos, vendas=vendas)

# -------- EXEC --------
