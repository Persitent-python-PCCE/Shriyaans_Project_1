import pytest
from flask import Flask

import app as app_module
from config.database import db


@pytest.fixture
def app_client(monkeypatch):
    flask_app = app_module.app
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def api_controller():
    import controllers.api_controller as api
    return api
