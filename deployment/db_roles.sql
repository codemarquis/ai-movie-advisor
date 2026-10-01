-- Least-privilege database roles for AI Movie Advisor.
-- Run once as a superuser / the RDS master user, then put the passwords in .env.
--   psql "$SUPERUSER_URL" -v app_password='…' -v admin_password='…' -f deployment/db_roles.sql

-- Owner of the schema: used only by admin scripts (ADMIN_DATABASE_URL).
CREATE ROLE movie_admin LOGIN PASSWORD :'admin_password';
GRANT CONNECT, CREATE ON DATABASE moviedb TO movie_admin;
GRANT CREATE, USAGE ON SCHEMA public TO movie_admin;

-- The web app (DATABASE_URL): may only read the two tables, and every
-- transaction is read-only even if a grant is added by mistake later.
CREATE ROLE ama_app LOGIN PASSWORD :'app_password';
ALTER ROLE ama_app SET default_transaction_read_only = on;
GRANT CONNECT ON DATABASE moviedb TO ama_app;
GRANT USAGE ON SCHEMA public TO ama_app;
ALTER DEFAULT PRIVILEGES FOR ROLE movie_admin IN SCHEMA public GRANT SELECT ON TABLES TO ama_app;

-- Nobody else gets anything by default.
REVOKE ALL ON DATABASE moviedb FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
