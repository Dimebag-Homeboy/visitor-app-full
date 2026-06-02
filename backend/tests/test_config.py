import os
os.environ["ENVIRONMENT"] = "test"
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "admin123")
SECRETARY_PASSWORD = os.getenv("TEST_SECRETARY_PASSWORD", "secret123")
GUARD_PASSWORD = os.getenv("TEST_GUARD_PASSWORD", "guard123")