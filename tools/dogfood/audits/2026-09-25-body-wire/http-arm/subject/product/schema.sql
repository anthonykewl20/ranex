CREATE ROLE authenticator LOGIN NOINHERIT PASSWORD 'experiment-api';
CREATE ROLE alice NOLOGIN; CREATE ROLE bob NOLOGIN; CREATE ROLE anon NOLOGIN;
GRANT alice,bob,anon TO authenticator;
CREATE SCHEMA api; GRANT USAGE ON SCHEMA api TO alice,bob,anon;
CREATE TABLE api.orders(id serial PRIMARY KEY,owner name NOT NULL DEFAULT current_user,item text NOT NULL);
ALTER TABLE api.orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY isolation ON api.orders USING(owner=current_user) WITH CHECK(owner=current_user);
GRANT SELECT,INSERT ON api.orders TO alice,bob;
GRANT USAGE ON SEQUENCE api.orders_id_seq TO alice,bob;
