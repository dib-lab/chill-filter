import os


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


def test_upload_d(app):
    with app.app_context():
        dirpath = app.config['UPLOAD_FOLDER']
        print(dirpath)
        assert os.path.exists(os.path.join(dirpath, 'Bu5.abund.k51.s100_000.sig.zip.x.all.gather.csv'))
