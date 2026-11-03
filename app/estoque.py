from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)

from .auth import login_obrigatorio
from .models import Item, db
from .servicos import (ErroEstoque, buscar_itens, cadastrar_item,
                       historico_do_item, registrar_movimentacao)

estoque_bp = Blueprint("estoque", __name__)


@estoque_bp.route("/")
@login_obrigatorio
def listar():
    termo = request.args.get("busca", "")
    itens = buscar_itens(termo)
    return render_template("itens.html", itens=itens, termo=termo)


@estoque_bp.route("/itens/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo_item():
    if request.method == "POST":
        try:
            item = cadastrar_item(
                request.form.get("nome"),
                request.form.get("codigo"),
                request.form.get("quantidade", 0),
                request.form.get("localizacao"),
            )
        except ErroEstoque as erro:
            flash(str(erro), "erro")
            return render_template("item_form.html", dados=request.form), 400
        flash(f"Item {item.nome} cadastrado.", "ok")
        return redirect(url_for("estoque.listar"))
    return render_template("item_form.html", dados={})


@estoque_bp.route("/itens/<int:item_id>/movimentar", methods=["GET", "POST"])
@login_obrigatorio
def movimentar(item_id):
    item = db.get_or_404(Item, item_id)
    if request.method == "POST":
        try:
            registrar_movimentacao(
                item.id, request.form.get("tipo"), request.form.get("quantidade")
            )
        except ErroEstoque as erro:
            flash(str(erro), "erro")
            return render_template("movimentar.html", item=item), 400
        flash(f"Movimentação registrada. Saldo atual: {item.quantidade_atual}.", "ok")
        return redirect(url_for("estoque.listar"))
    return render_template("movimentar.html", item=item)


@estoque_bp.route("/itens/<int:item_id>/historico")
@login_obrigatorio
def historico(item_id):
    item = db.get_or_404(Item, item_id)
    return render_template("historico.html", item=item,
                           movimentacoes=historico_do_item(item.id))


@estoque_bp.app_errorhandler(404)
def nao_encontrado(_erro):
    return render_template("erro.html", mensagem="Página não encontrada."), 404


@estoque_bp.app_errorhandler(400)
def requisicao_invalida(_erro):
    return render_template("erro.html", mensagem="Requisição inválida. Recarregue a página e tente de novo."), 400


@estoque_bp.app_errorhandler(500)
def erro_interno(_erro):
    return render_template("erro.html", mensagem="Ocorreu um erro inesperado."), 500
