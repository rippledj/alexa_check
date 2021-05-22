-- Alexa Check Database Initialization
--
-- Run this file in PostgreSQL before running main script
--$ psql -U postgres -d postgres -f postgres_setup.sql

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

-- -----------------------------------------------------
-- Create Databse alexa
-- -----------------------------------------------------

DROP DATABASE IF EXISTS alexa;
CREATE DATABASE alexa;

\c alexa;

DROP SCHEMA IF EXISTS alexa CASCADE;
CREATE SCHEMA IF NOT EXISTS alexa;

-- -----------------------------------------------------
-- Create Agency Tables
-- -----------------------------------------------------

-- This is not a standard UCR table but one derived from the reta_month/alexa_month
-- This code table is for files before 2016
CREATE TABLE alexa.headers (
  pos integer,
  tld character varying(100),
  url character varying(100),
  ip inet,
  ip_full text,
  http_code integer,
  header_string text,
  header_json text,
  scrape_date date default CURRENT_DATE
);

--
-- Add commends to all columns
--
comment on column alexa.headers.pos is 'The Alexa position at scrape-time';
comment on column alexa.headers.tld is 'The top level domain';
comment on column alexa.headers.url is 'The URL including the schema (http:// or https://)';
comment on column alexa.headers.ip is 'The IP address of the sub-domain and domain found using python nslookup';
comment on column alexa.headers.ip_full is 'The full string response of the sub-domain and domain from nslookup';
comment on column alexa.headers.http_code is 'The HTTP response status code 3 digit integer';
comment on column alexa.headers.header_string is 'The HTTP HEAD as a string including line-breaks';
comment on column alexa.headers.header_json is 'The HTTP HEAD in json format';
comment on column alexa.headers.scrape_date is 'The date of the header data collection';

-- This is not a standard UCR table but one derived from the reta_month/alexa_month
-- This code table is for files before 2016
CREATE TABLE alexa.mx (
  pos integer,
  domain character varying(100),
  mx text[],
  scrape_date date default CURRENT_DATE
);

comment on column alexa.headers.pos is 'The Alexa position at scrape-time';
comment on column alexa.headers.tld is 'The top level domain';
comment on column alexa.headers.url is 'The MX records found for the sub-domain and domain';
comment on column alexa.headers.scrape_date is 'The date of the header data collection';

-- -----------------------------------------------------
-- Create PostgreSQL Users
-- -----------------------------------------------------

-- Drop user if exists and create a new user with password
DROP USER IF EXISTS alexa;
CREATE USER alexa LOGIN PASSWORD 'n4T8tejYMmCHHbpn6s92V';
ALTER USER alexa WITH SUPERUSER;

-- Change the owner of uspto database to alexa user
ALTER DATABASE alexa OWNER TO alexa;
ALTER SCHEMA alexa OWNER to alexa;
ALTER DATABASE alexa SET search_path TO alexa;

-- Grant privileges to all corresponding databases
GRANT USAGE ON SCHEMA alexa TO alexa;
GRANT ALL ON ALL TABLES IN SCHEMA alexa TO alexa;
