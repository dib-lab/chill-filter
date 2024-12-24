def test_display_abund(client):
    # test search of abund sketch
    # copy sig zip in
    response = client.get('/example?filename=SRR606249.k51.s100_000.sig.zip',
                          follow_redirects=True)
    # @CTB assert

    # now, get search results
    response = client.get('/ee6adb3e/SRR606249.k51.s100_000.sig.zip/subsearch/all/')

    print(response.data)
    assert b'this looks like a set of reads' in response.data
    assert b'95.0% (5.1 Gbp)' in response.data
    # @CTB assert

def test_display_abund_podar(client):
    response = client.get('/example?filename=SRR606249.k51.s100_000.sig.zip',
                          follow_redirects=True)
    # @CTB assert

    # test search of abund sketch
    response = client.get('/ee6adb3e/SRR606249.k51.s100_000.sig.zip/subsearch/podar-ref/')

    print(response.data)
    assert b'this looks like a set of reads' in response.data


def test_display_no_matches(client):
    # test display of no matches
    response = client.get('/ac5b62eb/no-matches.sig.zip/subsearch/all',
                          follow_redirects=True)
    print(response.data)
    assert b'no matches to your sample' in response.data


def test_download_csv(client):
    # test download of CSV
    response = client.get('/example?filename=Bu5.abund.k51.s100_000.sig.zip',
                          follow_redirects=True)
    response = client.get('97681062/Bu5.abund.k51.s100_000.sig.zip/subsearch/all/download_csv')
    assert response.status_code == 200
    data = response.get_data()
    print(data)
    assert data.startswith(b'intersect_bp,f_orig_query,f_match,')
