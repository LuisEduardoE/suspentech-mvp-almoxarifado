import secrets
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)

from .models import Usuario

auth_bp = Blueprint("auth", __name__)


def login_obrigatorio(view):
    """Bloqueia a rota para quem nao esta logado."""

    @wraps(view)
    def envolvida(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return envolvida


def token_csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@auth_bp.app_context_processor
def injeta_csrf():
    return {"csrf_token": token_csrf}


@auth_bp.before_app_request
def confere_csrf():
    # todo formulario enviado precisa trazer o token da sessao
    if request.method == "POST":
        enviado = request.form.get("csrf")
        if not enviado or enviado != session.get("csrf"):
            abort(400)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = Usuario.query.filter_by(
            login=request.form.get("login", "").strip()
        ).first()
        if usuario and usuario.confere_senha(request.form.get("senha", "")):
            session.clear()
            session["usuario_id"] = usuario.id
            session["usuario_login"] = usuario.login
            return redirect(url_for("estoque.listar"))
        # mensagem generica, nao diz se o erro foi no login ou na senha
        flash("Usuário ou senha inválidos.", "erro")
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu do sistema.", "ok")
    return redirect(url_for("auth.login"))
