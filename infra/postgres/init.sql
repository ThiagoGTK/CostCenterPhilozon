-- Script de inicialização do PostgreSQL
-- Executado apenas na PRIMEIRA criação do container (não roda em reinícios).
-- Para mudar senhas em produção: use ALTER ROLE dentro do psql.

-- Schemas do DW
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS app;

-- ── Usuário de leitura para o Metabase ────────────────────────────────────
-- ATENÇÃO: Altere a senha abaixo antes de usar em produção.
-- Em produção use: ALTER ROLE metabase_reader PASSWORD 'nova_senha_segura';
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'metabase_reader') THEN
        CREATE ROLE metabase_reader WITH LOGIN PASSWORD 'metabase_reader_changeme';
    END IF;
END
$$;

-- ── Usuário de metadados do Metabase ──────────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'metabase_user') THEN
        CREATE ROLE metabase_user WITH LOGIN PASSWORD 'metabase_user_changeme' CREATEDB;
    END IF;
END
$$;

-- Banco separado para metadados internos do Metabase
SELECT 'CREATE DATABASE metabase OWNER metabase_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase') \gexec

-- ── Permissões de leitura no DW para o metabase_reader ───────────────────
GRANT USAGE ON SCHEMA dw TO metabase_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA dw TO metabase_reader;
-- Aplica às futuras tabelas e views criadas pelo fpa_user
ALTER DEFAULT PRIVILEGES FOR ROLE fpa_user IN SCHEMA dw
    GRANT SELECT ON TABLES TO metabase_reader;
