import os

DB_HOST = os.environ.get('KTX_DB_HOST', 'mysql-fornewworkpy-syedafauzia71-da87.a.aivencloud.com')
DB_PORT = int(os.environ.get('KTX_DB_PORT', 11847))
DB_USER = os.environ.get('KTX_DB_USER', 'avnadmin')
DB_PASSWORD = os.environ.get('KTX_DB_PASSWORD', 'AVNS_KfUwf7Xx5RusmdWQvtM')
DB_NAME = os.environ.get('KTX_DB_NAME', 'toy_store')

USE_DATABASE = os.environ.get('KTX_USE_DB', '1') not in ('0', 'false', 'False')
