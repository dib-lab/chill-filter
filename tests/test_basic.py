import pytest
from chill_filter_web import create_app


# from: https://flask.palletsprojects.com/en/stable/testing/

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    # other setup can go here
    yield app
    
    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def test_front(client):
    response = client.get("/")
    print(response.data)
    assert b"chill-filter: What's in my sample?" in response.data

def test_guide(client):
    response = client.get("/guide")
    assert b"The chill-filter user guide" in response.data

def test_faq(client):
    response = client.get("/faq")
    assert b"Frequently Asked Questions - chill-filter" in response.data
