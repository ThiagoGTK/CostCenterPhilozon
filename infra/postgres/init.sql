-- Script de inicialização do PostgreSQL
-- Executado apenas na primeira criação do container.

-- Schema para o Data Warehouse (dimensões e fatos)
CREATE SCHEMA IF NOT EXISTS dw;

-- Schema para a aplicação (orçamento, workflow, mapeamentos)
CREATE SCHEMA IF NOT EXISTS app;

-- Usuário de leitura para o Metabase
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'metabase_reader') THEN
        CREATE ROLE metabase_reader WITH LOGIN PASSWORD 'metabase_reader_password';
    END IF;
END
$$;

-- Banco separado para metadados do Metabase
CREATE DATABASE metabase
    OWNER = fpa_user;

-- Permissões de leitura no DW para o Metabase
GRANT USAGE ON SCHEMA dw TO metabase_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA dw TO metabase_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA dw GRANT SELECT ON TABLES TO metabase_reader;
