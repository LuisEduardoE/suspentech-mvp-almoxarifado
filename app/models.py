from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Usuario(db.Model):
    """Operador do almoxarifado. So guardamos login e o hash da senha."""

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def confere_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Item(db.Model):
    """Material cadastrado no almoxarifado."""

    __table_args__ = (
        CheckConstraint("quantidade_atual >= 0", name="ck_item_qtd_nao_negativa"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    codigo = db.Column(db.String(40), unique=True, nullable=False)
    quantidade_atual = db.Column(db.Integer, nullable=False, default=0)
    localizacao = db.Column(db.String(80))

    movimentacoes = db.relationship(
        "Movimentacao", back_populates="item", cascade="all, delete-orphan"
    )


class Movimentacao(db.Model):
    """Entrada ou saida de um item."""

    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_mov_qtd_positiva"),
        CheckConstraint("tipo IN ('entrada', 'saida')", name="ck_mov_tipo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.now)

    item = db.relationship("Item", back_populates="movimentacoes")
