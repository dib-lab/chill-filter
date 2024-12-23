import os
from chill_filter_web import utils


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


def test_upload_d_exists(app):
    # this is really a test for the test fixtures ;)
    with app.app_context():
        dirpath = app.config['UPLOAD_FOLDER']
        print(dirpath)
        assert os.path.exists(os.path.join(dirpath, 'Bu5.abund.k51.s100_000.sig.zip.x.all.gather.csv'))


def test_fail_example(client):
    response = client.get('/example?filename=XXX_Bu5.abund.k51.s100_000.sig.zip')
    print(response.data)
    assert response.status_code == 404


def test_bad_example(client):
    response = client.get('/example?filename=bad-example.sig.zip')
    print(response.data)
    assert response.status_code == 404


def test_display_abund(client):
    response = client.get('/example?filename=Bu5.abund.k51.s100_000.sig.zip',
                          follow_redirects=True)
    print(response.data)
    assert b'this looks like a set of reads' in response.data
    assert b'at least <b>81.5%</b> of your sequencing data will map' in response.data
    assert b'76.3% (60.1 Gbp)' in response.data
    assert b'4.8% (3.8 Gbp)' in response.data
    assert b'0.3% (215.2 Mbp)' in response.data
    assert b'bacteria and archaea (GTDB rs220)' in response.data
    assert b'22x' in response.data
    assert b'1x' in response.data    


def test_display_flat(client):
    response = client.get('/example?filename=Bu5.flat.k51.s100_000.sig.zip',
                          follow_redirects=True)
    print(response.data)
    assert b'this looks like an assembly' in response.data
    assert b'<b>90.7%</b>\n  of your contigs' in response.data
    assert b'83.5% (2.1 Gbp)' in response.data
    assert b'bacteria and archaea (GTDB rs220) ' in response.data
    assert b'7.1% (176.1 Mbp)' in response.data


def test_display_no_matches(client):
    response = client.get('/ac5b62eb/no-matches.sig.zip/search',
                          follow_redirects=True)
    print(response.data)
    assert b'no matches to your sample' in response.data


def test_delete(app):
    # this is really a test for the test fixtures ;)
    with app.app_context():
        client = app.test_client()

        # copy the example over
        response = client.get('/example?filename=Bu5.abund.k51.s100_000.sig.zip',
                              follow_redirects=True)
        dirpath = app.config['UPLOAD_FOLDER']

        # the CSV should also exist
        assert os.path.exists(os.path.join(dirpath, 'Bu5.abund.k51.s100_000.sig.zip'))
        assert os.path.exists(os.path.join(dirpath, 'Bu5.abund.k51.s100_000.sig.zip.x.all.gather.csv'))
        response = client.get('/97681062/Bu5.abund.k51.s100_000.sig.zip/delete')
        assert not os.path.exists(os.path.join(dirpath, 'Bu5.abund.k51.s100_000.sig.zip'))
        assert not os.path.exists(os.path.join(dirpath, 'Bu5.abund.k51.s100_000.sig.zip.x.all.gather.csv'))


def test_sample_index(client):
    # copy it in...
    response = client.get('/example?filename=Bu5.abund.k51.s100_000.sig.zip',
                          follow_redirects=True)

    # ...check location.
    response = client.get('97681062/Bu5.abund.k51.s100_000.sig.zip/')
    assert b'Bu5.abund.k51.s100_000.sig.zip' in response.data


def test_sample_download_sketch(client, tmp_path):
    response = client.get('/example?filename=Bu5.abund.k51.s100_000.sig.zip',
                          follow_redirects=True)
    response = client.get('97681062/Bu5.abund.k51.s100_000.sig.zip/download')
    data = response.get_data()
    outfile = tmp_path / 'xyz.sig.zip'
    with open(outfile, 'wb') as fp:
        fp.write(data)

    assert utils.load_sig(outfile)


def test_sample_download_csv(client):
    response = client.get('/example?filename=Bu5.abund.k51.s100_000.sig.zip',
                          follow_redirects=True)
    response = client.get('97681062/Bu5.abund.k51.s100_000.sig.zip/download_csv')
    assert response.status_code == 200
    data = response.get_data()
    print(data)
    assert data.startswith(b'intersect_bp,f_orig_query,f_match,')
