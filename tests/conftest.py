import os
import sys
from pathlib import Path

os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-0123456789"
os.environ["ADMIN_PASSWORD"] = "test-admin-password-123"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.admin import router as admin_module
from app.api import auth as auth_module
from app.api import cards as cards_module
from app.api import users as users_module
from app.api.router import api_router
from app.database import db_core


@pytest.fixture()
def client(tmp_path):
    db_core.init_db(f"sqlite:///{tmp_path / 'test.db'}")
    for limiter in (
        auth_module._login_by_ip,
        auth_module._login_by_pair,
        auth_module._register_by_ip,
        admin_module._admin_login_by_ip,
        cards_module._probe_limiter,
        users_module._delete_limiter,
    ):
        limiter._hits.clear()
    app = FastAPI()
    app.include_router(api_router, prefix="/api")
    app.include_router(admin_module.router, prefix="/admin")
    with TestClient(app) as test_client:
        yield test_client
