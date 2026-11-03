import os
import secrets

import click
from flask import Flask

from .models import db


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    # a chave secreta vem de variavel de ambiente (nao fica no codigo)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///almoxarifado.db"
    )
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if config:
        app.config.update(config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from .auth import auth_bp
    from .estoque import estoque_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(estoque_bp)

    with app.app_context():
        db.create_all()

    registrar_comandos(app)
    return app


def registrar_comandos(app):
    @app.cli.command("criar-usuario")
    @click.argument("login")
    @click.password_option()
    def criar_usuario(login, password):
        """Cria um operador para acessar o sistema."""
        from .models import Usuario

        if Usuario.query.filter_by(login=login).first():
            click.echo("Já existe um usuário com esse login.")
            return
        usuario = Usuario(login=login)
        usuario.definir_senha(password)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuário '{login}' criado.")
