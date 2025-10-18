--
-- PostgreSQL database dump
--

\restrict lDveDQpNhUIqUpbEYhRrblWiBog68lgH7drRyiLsNvHgcaLhX8PJz8Ibewdm6xM

-- Dumped from database version 16.10 (Ubuntu 16.10-1.pgdg22.04+1)
-- Dumped by pg_dump version 16.10 (Ubuntu 16.10-1.pgdg22.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: market_ticks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.market_ticks (
    "time" timestamp with time zone NOT NULL,
    tick_id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id character varying(50) NOT NULL,
    symbol character varying(20) NOT NULL,
    bid numeric(18,5) NOT NULL,
    ask numeric(18,5) NOT NULL,
    mid numeric(18,5) NOT NULL,
    spread numeric(10,5) NOT NULL,
    exchange character varying(50),
    source character varying(50) NOT NULL,
    event_type character varying(20) NOT NULL,
    use_case character varying(50) DEFAULT ''::character varying,
    timestamp_ms bigint NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Data for Name: market_ticks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.market_ticks ("time", tick_id, tenant_id, symbol, bid, ask, mid, spread, exchange, source, event_type, use_case, timestamp_ms, ingested_at) FROM stdin;
\.


--
-- Name: market_ticks market_ticks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.market_ticks
    ADD CONSTRAINT market_ticks_pkey PRIMARY KEY ("time", tenant_id, symbol, tick_id);


--
-- Name: market_ticks_time_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX market_ticks_time_idx ON public.market_ticks USING btree ("time" DESC);


--
-- Name: market_ticks ts_insert_blocker; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON public.market_ticks FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();


--
-- PostgreSQL database dump complete
--

\unrestrict lDveDQpNhUIqUpbEYhRrblWiBog68lgH7drRyiLsNvHgcaLhX8PJz8Ibewdm6xM

