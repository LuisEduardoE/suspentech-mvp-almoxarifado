"""Regras de negocio do estoque.

Fica separado das rotas para poder testar as regras sem precisar
abrir o navegador.
"""

from sqlalchemy import or_

from .models import Item, Movimentacao, db


class ErroEstoque(ValueError):
    """Erro de validacao mostrado para o operador."""


def _inteiro(valor, campo):
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        raise ErroEstoque(f"{campo} deve ser um número inteiro.")


def cadastrar_item(nome, codigo, quantidade_inicial=0, localizacao=None):
    nome = (nome or "").strip()
    codigo = (codigo or "").strip().upper()
    localizacao = (localizacao or "").strip() or None

    if not nome:
        raise ErroEstoque("Informe o nome do item.")
    if not codigo:
        raise ErroEstoque("Informe o código do item.")
    if len(nome) > 120 or len(codigo) > 40:
        raise ErroEstoque("Nome ou código muito longo.")

    quantidade = _inteiro(quantidade_inicial if quantidade_inicial != "" else 0,
                          "Quantidade inicial")
    if quantidade < 0:
        raise ErroEstoque("A quantidade inicial não pode ser negativa.")

    if Item.query.filter_by(codigo=codigo).first():
        raise ErroEstoque(f"Já existe um item com o código {codigo}.")

    item = Item(nome=nome, codigo=codigo, quantidade_atual=quantidade,
                localizacao=localizacao)
    db.session.add(item)
    db.session.commit()
    return item


def registrar_movimentacao(item_id, tipo, quantidade):
    item = db.session.get(Item, item_id)
    if item is None:
        raise ErroEstoque("Item não encontrado.")
    if tipo not in ("entrada", "saida"):
        raise ErroEstoque("Tipo deve ser entrada ou saída.")

    quantidade = _inteiro(quantidade, "Quantidade")
    if quantidade <= 0:
        raise ErroEstoque("A quantidade deve ser maior que zero.")

    if tipo == "saida":
        if quantidade > item.quantidade_atual:
            raise ErroEstoque(
                f"Saldo insuficiente: há apenas {item.quantidade_atual} "
                f"unidade(s) de {item.nome}."
            )
        item.quantidade_atual -= quantidade
    else:
        item.quantidade_atual += quantidade

    mov = Movimentacao(item=item, tipo=tipo, quantidade=quantidade)
    db.session.add(mov)
    db.session.commit()
    return mov


def buscar_itens(termo=None):
    consulta = Item.query
    termo = (termo or "").strip()
    if termo:
        padrao = f"%{termo}%"
        consulta = consulta.filter(
            or_(Item.nome.ilike(padrao), Item.codigo.ilike(padrao))
        )
    return consulta.order_by(Item.nome).all()


def historico_do_item(item_id):
    """Movimentacoes do item, da mais recente para a mais antiga (RF04)."""
    return (
        Movimentacao.query.filter_by(item_id=item_id)
        .order_by(Movimentacao.data_hora.desc(), Movimentacao.id.desc())
        .all()
    )
