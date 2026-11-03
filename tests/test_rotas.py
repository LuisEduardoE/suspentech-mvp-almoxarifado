"""Testes de integracao: navegador simulado -> rotas Flask -> banco SQLite."""

from app.models import Item
from tests.conftest import pegar_csrf


def test_sem_login_redireciona_para_login(client):
    resposta = client.get("/")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_login_com_senha_errada(client):
    token = pegar_csrf(client)
    resposta = client.post("/login", data={"login": "operador", "senha": "x", "csrf": token})
    assert "Usuário ou senha inválidos" in resposta.get_data(as_text=True)


def test_post_sem_token_csrf_e_recusado(client):
    resposta = client.post("/login", data={"login": "operador", "senha": "senha123"})
    assert resposta.status_code == 400


def test_fluxo_completo_cadastro_e_movimentacao(logado, app):
    resposta = logado.post("/itens/novo", data={
        "nome": "Mola parabólica", "codigo": "PAR-001",
        "quantidade": "10", "localizacao": "A1", "csrf": logado.csrf,
    }, follow_redirects=True)
    html = resposta.get_data(as_text=True)
    assert "Item Mola parabólica cadastrado" in html
    assert "PAR-001" in html

    item = Item.query.filter_by(codigo="PAR-001").first()
    resposta = logado.post(f"/itens/{item.id}/movimentar", data={
        "tipo": "saida", "quantidade": "4", "csrf": logado.csrf,
    }, follow_redirects=True)
    assert "Saldo atual: 6" in resposta.get_data(as_text=True)


def test_saida_sem_saldo_mostra_erro(logado):
    logado.post("/itens/novo", data={
        "nome": "Bucha", "codigo": "BUC-1", "quantidade": "1", "csrf": logado.csrf,
    })
    item = Item.query.filter_by(codigo="BUC-1").first()
    resposta = logado.post(f"/itens/{item.id}/movimentar", data={
        "tipo": "saida", "quantidade": "9", "csrf": logado.csrf,
    })
    assert resposta.status_code == 400
    assert "Saldo insuficiente" in resposta.get_data(as_text=True)


def test_busca_filtra_listagem(logado):
    for nome, codigo in [("Mola", "PAR-1"), ("Grampo", "GRA-1")]:
        logado.post("/itens/novo", data={"nome": nome, "codigo": codigo, "csrf": logado.csrf})
    html = logado.get("/?busca=gra").get_data(as_text=True)
    assert "GRA-1" in html
    assert "PAR-1" not in html


def test_script_no_nome_nao_e_executado(logado):
    logado.post("/itens/novo", data={
        "nome": "<script>alert(1)</script>", "codigo": "XSS-1", "csrf": logado.csrf,
    })
    html = logado.get("/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_logout_encerra_sessao(logado):
    logado.post("/logout", data={"csrf": logado.csrf})
    assert logado.get("/").status_code == 302


def test_tela_de_historico(logado):
    logado.post("/itens/novo", data={"nome": "Mola", "codigo": "PAR-9", "quantidade": "5", "csrf": logado.csrf})
    item = Item.query.filter_by(codigo="PAR-9").first()
    logado.post(f"/itens/{item.id}/movimentar", data={"tipo": "saida", "quantidade": "2", "csrf": logado.csrf})
    html = logado.get(f"/itens/{item.id}/historico").get_data(as_text=True)
    assert "Histórico de PAR-9" in html
    assert "Saída" in html


def test_historico_de_item_inexistente(logado):
    assert logado.get("/itens/999/historico").status_code == 404
