"""Testes unitarios das regras de estoque (RF01, RF02, RF03)."""

import pytest

from app.models import Movimentacao, Usuario
from app.servicos import (ErroEstoque, buscar_itens, cadastrar_item,
                          registrar_movimentacao)


def test_cadastra_item_valido(app):
    item = cadastrar_item("Mola parabólica", "par-001", 10, "Corredor A")
    assert item.id is not None
    assert item.codigo == "PAR-001"
    assert item.quantidade_atual == 10


def test_nao_aceita_codigo_repetido(app):
    cadastrar_item("Mola", "PAR-001", 5)
    with pytest.raises(ErroEstoque, match="Já existe"):
        cadastrar_item("Outra mola", "par-001", 1)


@pytest.mark.parametrize("nome, codigo", [("", "X1"), ("Bucha", ""), ("  ", "X2")])
def test_campos_obrigatorios(app, nome, codigo):
    with pytest.raises(ErroEstoque):
        cadastrar_item(nome, codigo, 1)


def test_quantidade_inicial_negativa(app):
    with pytest.raises(ErroEstoque, match="negativa"):
        cadastrar_item("Bucha", "BUC-01", -3)


def test_quantidade_texto_invalido(app):
    with pytest.raises(ErroEstoque, match="número inteiro"):
        cadastrar_item("Bucha", "BUC-01", "dez")


def test_entrada_soma_no_saldo(app):
    item = cadastrar_item("Grampo", "GRA-10", 4)
    registrar_movimentacao(item.id, "entrada", 6)
    assert item.quantidade_atual == 10


def test_saida_subtrai_do_saldo(app):
    item = cadastrar_item("Grampo", "GRA-10", 10)
    registrar_movimentacao(item.id, "saida", 3)
    assert item.quantidade_atual == 7


def test_saida_maior_que_saldo_e_bloqueada(app):
    item = cadastrar_item("Grampo", "GRA-10", 2)
    with pytest.raises(ErroEstoque, match="Saldo insuficiente"):
        registrar_movimentacao(item.id, "saida", 5)
    assert item.quantidade_atual == 2
    assert Movimentacao.query.count() == 0


@pytest.mark.parametrize("qtd", [0, -1])
def test_quantidade_da_movimentacao_deve_ser_positiva(app, qtd):
    item = cadastrar_item("Grampo", "GRA-10", 2)
    with pytest.raises(ErroEstoque, match="maior que zero"):
        registrar_movimentacao(item.id, "entrada", qtd)


def test_tipo_invalido(app):
    item = cadastrar_item("Grampo", "GRA-10", 2)
    with pytest.raises(ErroEstoque):
        registrar_movimentacao(item.id, "emprestimo", 1)


def test_busca_por_nome_e_codigo(app):
    cadastrar_item("Mola parabólica", "PAR-001", 1)
    cadastrar_item("Bucha do feixe", "BUC-002", 1)
    assert [i.codigo for i in buscar_itens("mola")] == ["PAR-001"]
    assert [i.codigo for i in buscar_itens("buc")] == ["BUC-002"]
    assert len(buscar_itens("")) == 2


def test_senha_nao_fica_em_texto_puro(app):
    usuario = Usuario.query.filter_by(login="operador").first()
    assert usuario.senha_hash != "senha123"
    assert usuario.confere_senha("senha123")
    assert not usuario.confere_senha("errada")


def test_historico_em_ordem_do_mais_recente(app):
    from app.servicos import historico_do_item

    item = cadastrar_item("Grampo", "GRA-10", 0)
    registrar_movimentacao(item.id, "entrada", 10)
    registrar_movimentacao(item.id, "saida", 4)
    historico = historico_do_item(item.id)
    assert [(m.tipo, m.quantidade) for m in historico] == [("saida", 4), ("entrada", 10)]
