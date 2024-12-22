import os
import shutil

import pytest

from chill_filter_web import create_app, default_settings

# from: https://flask.palletsprojects.com/en/stable/testing/
TESTDATA_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__),
                                      'test-upload.d')

@pytest.fixture()
def app(tmp_path):
    app = create_app()

    upload_folder = tmp_path / 'upload'
    shutil.copytree(TESTDATA_UPLOAD_FOLDER, upload_folder)

    app.config.update(default_settings)
    app.config.update({
        "TESTING": True,
        "UPLOAD_FOLDER": str(upload_folder),
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

