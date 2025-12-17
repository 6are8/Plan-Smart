# tests/conftest.py

import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import create_app
from extensions import db


@pytest.fixture(scope="function")
def app():
    """إنشاء تطبيق للاختبار"""
    import os
    
    # تعيين متغيرات البيئة قبل إنشاء التطبيق
    os.environ["FLASK_SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    os.environ["FLASK_JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["FLASK_TESTING"] = "True"
    
    app = create_app()
    app.config["TESTING"] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # تنظيف متغيرات البيئة بعد الاختبار
    for key in ["FLASK_SQLALCHEMY_DATABASE_URI", "FLASK_JWT_SECRET_KEY", "FLASK_TESTING"]:
        os.environ.pop(key, None)


@pytest.fixture
def client(app):
    """إنشاء client للاختبار"""
    return app.test_client()