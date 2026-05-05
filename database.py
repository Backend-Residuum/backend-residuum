from sqlalchemy import create_engine # Importa função para criar conexão com banco
from sqlalchemy.orm import sessionmaker, declarative_base # Importa ferramenta para criar sessões (conexões com o banco)

DATABASE_URL = "sqlite:///./reciclagem.db" # Define o caminho do banco SQLite (arquivo local)

# Cria a conexão com o banco
# check_same_thread=False é necessário para SQLite funcionar com FastAPI
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine) # Cria uma "fábrica" de sessões (cada requisição usa uma sessão)

Base = declarative_base() # Base para criar os modelos (tabelas)

def get_db(): # Função que fornece uma conexão com o banco para cada requisição
    db = SessionLocal() # abre conexão
    try:
        yield db # entrega a conexão para quem chamou (FastAPI)
    finally:
        db.close() # fecha conexão após uso