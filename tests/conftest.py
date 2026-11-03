import re

import pytest

from app import create_app
from app.models import Usuario, db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "chave-de-teste",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        usuario = Usuario(login="operador")
        usuario.definir_senha("senha123")
        db.session.add(usuario)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def pegar_csrf(client, url="/login"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


@pytest.fixture
def logado(client):
    token = pegar_csrf(client)
    client.post("/login", data={"login": "operador", "senha": "senha123", "csrf": token})
    client.csrf = pegar_csrf(client, "/itens/novo")
    return client
