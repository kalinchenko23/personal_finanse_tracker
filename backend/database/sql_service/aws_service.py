import json,sys
sys.path.insert(1,f'{pathlib.Path(__file__).parents[1]}')
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sql_db_service import DB_service
from db_service import banks
from session_sql import Session_aws

service=DB_service(banks,Session_aws)
# service.insert_transactions()
