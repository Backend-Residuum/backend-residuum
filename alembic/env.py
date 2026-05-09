import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from dotenv import load_dotenv

from alembic import context

# Garante que o pacote 'app' seja importável quando rodando alembic da raiz
sys.path.append(str(Path(__file__).resolve().parents[1]))

# --- ALTERAÇÃO 1: Comentamos o load_dotenv() para evitar conflito com o OneDrive ---
# load_dotenv()

# Importa Base e todos os modelos para que o autogenerate enxergue as tabelas
from app.database import Base  # noqa: E402
import app.models.usuario  # noqa: F401, E402
import app.models.endereco  # noqa: F401, E402
import app.models.descarte  # noqa: F401, E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- ALTERAÇÃO 2: Corrigida a sintaxe da URL e limpeza de caracteres ---
# Removido o os.getenv que estava com a string inteira dentro do parêntese.
# Definimos a URL diretamente para garantir que o Python não pegue lixo do Windows.
database_url = "postgresql://postgres:residum@localhost:5432/residuum"

if database_url:
    # O .encode().decode() remove bytes fantasmas (como o 0xe7) que causam erro de UTF-8
    clean_url = database_url.encode('utf-8').decode('utf-8').strip()
    config.set_main_option("sqlalchemy.url", clean_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata alvo para autogenerate
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # --- ALTERAÇÃO 3: Forçamos a URL limpa na criação do Engine ---
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()