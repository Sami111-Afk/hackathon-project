import os

from cryptography.fernet import Fernet

os.environ["ENV"] = "test"
os.environ["BANK_UI_TOKEN"] = "test-token"
os.environ["VAULT_KEY"] = Fernet.generate_key().decode()
os.environ["HMAC_SECRET"] = "test-hmac"
os.environ["ARENA_HMAC_SECRET"] = "test-arena-hmac"
os.environ["LLM_MODE"] = "mock"

AUTH = {"Authorization": "Bearer test-token"}
