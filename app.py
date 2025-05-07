from flask import Flask, render_template, request, redirect, session
import psycopg2
from psycopg2 import errors
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'

# Conexión a PostgreSQL
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="Admin.123",
    host="192.168.1.92",
    port="5432"
)
cursor = conn.cursor()

# Página de inicio
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    
    cursor.execute("""
        SELECT posts.title, posts.content, posts.created_at, users.username
        FROM posts
        INNER JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC;
    """)
    posts = cursor.fetchall()
    return render_template("home.html", posts=posts, username=session["username"])

# Registro de usuarios
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = generate_password_hash(request.form["password"])
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
            return redirect("/login")
        except errors.UniqueViolation:
            conn.rollback()
            return render_template("register.html", error="Ese nombre de usuario ya está registrado.")
        except Exception as e:
            conn.rollback()
            return render_template("register.html", error=f"Error inesperado: {e}")
    return render_template("register.html")

# Login de usuarios
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = username
            return redirect("/")
        else:
            return render_template("login.html", error="Credenciales incorrectas.")
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Crear nueva publicación
@app.route("/newpost", methods=["GET", "POST"])
def newpost():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        cursor.execute(
            "INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)",
            (session["user_id"], title, content)
        )
        conn.commit()
        return redirect("/")
    return render_template("newpost.html")

if __name__ == "__main__":
    app.run(debug=True)
