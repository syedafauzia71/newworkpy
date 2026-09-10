import os

DB_HOST = os.environ.get('KTX_DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('KTX_DB_PORT', 3306))
DB_USER = os.environ.get('KTX_DB_USER', 'root')
DB_PASSWORD = os.environ.get('KTX_DB_PASSWORD', '')
DB_NAME = os.environ.get('KTX_DB_NAME', 'toy_store')

USE_DATABASE = os.environ.get('KTX_USE_DB', '1') not in ('0', 'false', 'False')
