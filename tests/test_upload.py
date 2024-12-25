# test upload, specifically - both of precalculated and in-form sketched.
import os
import shutil
import json

import pytest

import sourmash
from chill_filter_web import utils


def test_sample_upload_precalc(app):
    # test upload of precalculated sketch via POST to /
    #
    # NOTE: this does not actually run the search, since there is a precalc
    # .csv in the test upload directory.
    with app.app_context():
        client = app.test_client()

        sigfile = os.path.join(app.config['EXAMPLES_DIR'],
                               'Bu5.abund.k51.s100_000.sig.zip')

        form_d = dict(sketch=(open(sigfile, 'rb'),
                              'Bu5.abund.k51.s100_000.sig.zip',
                              'application/zip'))
        
        response = client.post('/upload', data=form_d,
                               follow_redirects=True)


        print(response.data)
        assert b'18.5% unknown' in response.data


def test_sample_upload_empty_precalc(app):
    # test upload of _empty_ precalculated sketch via POST to /
    with app.app_context():
        client = app.test_client()

        sigfile = os.path.join(app.config['EXAMPLES_DIR'],
                               'empty.sig.zip')

        form_d = dict(sketch=(open(sigfile, 'rb'),
                              'empty.sig.zip',
                              'application/zip'))
        
        response = client.post('/upload', data=form_d,
                               follow_redirects=True)


        print(response.data)
        assert b'sketch is empty' in response.data
        assert response.status_code == 404        


def test_sample_upload_sketch(app):
    # test upload of client-side sketch via POST to /sketch
    #
    # uses testing mode to avoid running the actual search.
    with app.app_context():
        client = app.test_client()

        sigfile = os.path.join(app.config['EXAMPLES_DIR'],
                               'no-matches.sig.zip')
        ss = utils.load_sig(sigfile)
        assert ss

        sig_json = sourmash.save_signatures_to_json([ss])

        # this returns an array, and the upload needs a single encoded
        # signature. So pull off the first element and re-encode.
        sig2 = json.loads(sig_json)
        sig2 = sig2[0]
        sig2_json = json.dumps(sig2)

        # submit!
        form_d = dict(signature=sig2_json)
        response = client.post('/sketch', data=form_d,
                               follow_redirects=True)

        print(response.data)
        assert b'TESTING MODE: upload successful'


def test_sample_upload_empty_sketch(app):
    # test upload of client-side sketch via POST to /sketch
    with app.app_context():
        client = app.test_client()

        sigfile = os.path.join(app.config['EXAMPLES_DIR'],
                               'empty.sig.zip')
        ss = utils.load_sig(sigfile)
        assert ss

        sig_json = sourmash.save_signatures_to_json([ss])

        # this returns an array, and the upload needs a single encoded
        # signature. So pull off the first element and re-encode.
        sig2 = json.loads(sig_json)
        sig2 = sig2[0]
        sig2_json = json.dumps(sig2)

        # submit!
        form_d = dict(signature=sig2_json)
        response = client.post('/sketch', data=form_d,
                               follow_redirects=True)

        print(response.data)
        assert b'sketch is empty' in response.data
        assert response.status_code == 404        
