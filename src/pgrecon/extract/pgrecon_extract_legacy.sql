-- pgrecon offline extraction script, legacy variant
--
-- For Oracle 9.2 through 11.1, or any server whose only available
-- client is an old on-box SQL*Plus. Differences from the standard
-- script, all deliberate:
--
--   * CSV rows are built by hand with string concatenation, because
--     SET MARKUP CSV needs a 12.2+ client.
--   * DBMS_METADATA is not used at all. On old versions it is slow
--     and unreliable for tables, and the catalog views carry all the
--     facts an assessment needs. Table structure comes from
--     columns.csv; view text and sequence definitions are rebuilt
--     from ALL_VIEWS and ALL_SEQUENCES.
--   * Feature probes query only views that exist on 9.2 (no
--     DBA_SCHEDULER_JOBS; legacy DBMS_JOB is counted instead).
--
-- Known limits, accepted for this tier: view definitions longer than
-- 32000 characters are skipped with a note (PL/SQL cannot read a
-- larger LONG), and output lines are wrapped at 240 characters to
-- respect the 255-byte DBMS_OUTPUT limit of pre-10.2 servers.
--
-- Usage:
--   1. Create an empty working directory and cd into it.
--   2. Make the client spool UTF-8 so names in any language survive:
--        export NLS_LANG=.AL32UTF8      (Linux and macOS)
--        set NLS_LANG=.AL32UTF8         (Windows)
--   3. sqlplus readonly_user@service @pgrecon_extract_legacy.sql SCHEMA_NAME
--   4. Send the resulting folder of .csv and .sql files back.
--
-- Review notice: every statement below reads ALL_* dictionary views
-- or DUAL only. Nothing is written to the database.

WHENEVER OSERROR CONTINUE
WHENEVER SQLERROR CONTINUE

SET TERMOUT ON
PROMPT pgrecon legacy extraction starting for schema &1

SET ECHO OFF
SET VERIFY OFF
SET FEEDBACK OFF
SET TERMOUT OFF
SET TRIMSPOOL ON
SET PAGESIZE 0
SET LINESIZE 4000
SET LONG 100000
SET ARRAYSIZE 500

DEFINE schema = &1

-- ---------------------------------------------------------------
-- CSV section, hand built: quote every field, double embedded
-- quotes, strip line breaks out of free text.
-- ---------------------------------------------------------------

SPOOL meta.csv
SELECT '"KEY","VALUE"' FROM dual;
SELECT '"schema","' || UPPER('&schema') || '"' FROM dual;
SELECT '"extracted_at","' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') || '"'
  FROM dual;
SELECT '"product","' || REPLACE(product, '"', '""') || '"'
  FROM product_component_version
 WHERE product LIKE 'Oracle%' AND ROWNUM = 1;
SELECT '"version","' || version || '"'
  FROM product_component_version
 WHERE product LIKE 'Oracle%' AND ROWNUM = 1;
SPOOL OFF

SPOOL objects.csv
SELECT '"OWNER","OBJECT_NAME","OBJECT_TYPE","STATUS","CREATED","LAST_DDL_TIME"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(object_name, '"', '""') || '","'
       || object_type || '","' || status || '","'
       || TO_CHAR(created, 'YYYY-MM-DD HH24:MI:SS') || '","'
       || TO_CHAR(last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') || '"'
  FROM all_objects
 WHERE owner = UPPER('&schema')
   AND secondary = 'N'
   AND object_name NOT LIKE 'BIN$%'
   AND object_type NOT IN (
       'LOB', 'TABLE PARTITION', 'TABLE SUBPARTITION',
       'INDEX PARTITION', 'INDEX SUBPARTITION', 'LOB PARTITION')
 ORDER BY object_type, object_name;
SPOOL OFF

SPOOL tables.csv
SELECT '"OWNER","TABLE_NAME","NUM_ROWS","AVG_ROW_LEN","PARTITIONED",'
       || '"TEMPORARY","DEGREE"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(table_name, '"', '""') || '",'
       || NVL(TO_CHAR(num_rows), '') || ','
       || NVL(TO_CHAR(avg_row_len), '') || ',"'
       || partitioned || '","' || temporary || '","'
       || TRIM(NVL(degree, '')) || '"'
  FROM all_tables
 WHERE owner = UPPER('&schema')
   AND nested = 'NO'
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY table_name;
SPOOL OFF

SPOOL columns.csv
SELECT '"OWNER","TABLE_NAME","COLUMN_NAME","COLUMN_ID","DATA_TYPE",'
       || '"DATA_LENGTH","DATA_PRECISION","DATA_SCALE","NULLABLE"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(table_name, '"', '""') || '","'
       || REPLACE(column_name, '"', '""') || '",'
       || NVL(TO_CHAR(column_id), '') || ',"'
       || data_type || '",'
       || NVL(TO_CHAR(data_length), '') || ','
       || NVL(TO_CHAR(data_precision), '') || ','
       || NVL(TO_CHAR(data_scale), '') || ',"'
       || nullable || '"'
  FROM all_tab_columns
 WHERE owner = UPPER('&schema')
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY table_name, column_id;
SPOOL OFF

SPOOL source.csv
SELECT '"OWNER","NAME","TYPE","LINE","TEXT"' FROM dual;
SELECT '"' || owner || '","' || REPLACE(name, '"', '""') || '","'
       || type || '",' || line || ',"'
       || REPLACE(REPLACE(REPLACE(text, '"', '""'), CHR(13), ''), CHR(10), '')
       || '"'
  FROM all_source
 WHERE owner = UPPER('&schema')
 ORDER BY owner, name, type, line;
SPOOL OFF

SPOOL dependencies.csv
SELECT '"OWNER","NAME","TYPE","REFERENCED_OWNER","REFERENCED_NAME",'
       || '"REFERENCED_TYPE"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(name, '"', '""') || '","'
       || type || '","' || referenced_owner || '","'
       || REPLACE(referenced_name, '"', '""') || '","'
       || referenced_type || '"'
  FROM all_dependencies
 WHERE owner = UPPER('&schema')
   AND referenced_owner NOT IN ('SYS', 'SYSTEM', 'PUBLIC')
 ORDER BY name, referenced_name;
SPOOL OFF

SPOOL constraints.csv
SELECT '"OWNER","CONSTRAINT_NAME","TABLE_NAME","CONSTRAINT_TYPE","STATUS",'
       || '"R_OWNER","R_CONSTRAINT_NAME","DELETE_RULE"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(constraint_name, '"', '""') || '","'
       || REPLACE(table_name, '"', '""') || '","' || constraint_type || '","'
       || status || '","' || NVL(r_owner, '') || '","'
       || NVL(r_constraint_name, '') || '","' || NVL(delete_rule, '') || '"'
  FROM all_constraints
 WHERE owner = UPPER('&schema')
   AND constraint_type IN ('P', 'R', 'U', 'C')
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY table_name, constraint_name;
SPOOL OFF

SPOOL constraint_columns.csv
SELECT '"OWNER","CONSTRAINT_NAME","COLUMN_NAME","POSITION"' FROM dual;
SELECT '"' || owner || '","' || REPLACE(constraint_name, '"', '""') || '","'
       || REPLACE(column_name, '"', '""') || '",'
       || NVL(TO_CHAR(position), '')
  FROM all_cons_columns
 WHERE owner = UPPER('&schema')
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY constraint_name, position;
SPOOL OFF

SPOOL indexes.csv
SELECT '"OWNER","INDEX_NAME","TABLE_NAME","INDEX_TYPE","UNIQUENESS",'
       || '"STATUS","GENERATED","DEGREE"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(index_name, '"', '""') || '","'
       || REPLACE(table_name, '"', '""') || '","' || index_type || '","'
       || uniqueness || '","' || status || '","' || generated || '","'
       || TRIM(NVL(degree, '')) || '"'
  FROM all_indexes
 WHERE owner = UPPER('&schema')
   AND index_name NOT LIKE 'BIN$%'
 ORDER BY table_name, index_name;
SPOOL OFF

SPOOL index_columns.csv
SELECT '"OWNER","INDEX_NAME","COLUMN_NAME","COLUMN_POSITION"' FROM dual;
SELECT '"' || index_owner || '","' || REPLACE(index_name, '"', '""') || '","'
       || REPLACE(column_name, '"', '""') || '",' || column_position
  FROM all_ind_columns
 WHERE index_owner = UPPER('&schema')
 ORDER BY index_name, column_position;
SPOOL OFF

-- No INTERVAL column here: it arrived with 11.1. The loader treats the
-- missing header as null.
SPOOL part_tables.csv
SELECT '"OWNER","TABLE_NAME","PARTITIONING_TYPE","SUBPARTITIONING_TYPE",'
       || '"PARTITION_COUNT"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(table_name, '"', '""') || '","'
       || partitioning_type || '","' || subpartitioning_type || '",'
       || partition_count
  FROM all_part_tables
 WHERE owner = UPPER('&schema')
 ORDER BY table_name;
SPOOL OFF

SPOOL part_key_columns.csv
SELECT '"OWNER","NAME","COLUMN_NAME","COLUMN_POSITION"' FROM dual;
SELECT '"' || owner || '","' || REPLACE(name, '"', '""') || '","'
       || REPLACE(column_name, '"', '""') || '",' || column_position
  FROM all_part_key_columns
 WHERE owner = UPPER('&schema')
   AND object_type = 'TABLE'
 ORDER BY name, column_position;
SPOOL OFF

SPOOL synonyms.csv
SELECT '"OWNER","SYNONYM_NAME","TABLE_OWNER","TABLE_NAME","DB_LINK"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(synonym_name, '"', '""') || '","'
       || NVL(table_owner, '') || '","'
       || REPLACE(NVL(table_name, ''), '"', '""') || '","'
       || NVL(db_link, '') || '"'
  FROM all_synonyms
 WHERE owner = UPPER('&schema')
    OR (owner = 'PUBLIC' AND table_owner = UPPER('&schema'))
 ORDER BY owner, synonym_name;
SPOOL OFF

-- Private database links are invisible through ALL_DB_LINKS to anyone
-- but their owner; DBA_DB_LINKS is readable with SELECT_CATALOG_ROLE,
-- which this script already requires.
SPOOL db_links.csv
SELECT '"OWNER","DB_LINK","USERNAME","HOST"' FROM dual;
SELECT '"' || owner || '","' || REPLACE(db_link, '"', '""') || '","'
       || NVL(username, '') || '","'
       || REPLACE(NVL(host, ''), '"', '""') || '"'
  FROM dba_db_links
 WHERE owner IN (UPPER('&schema'), 'PUBLIC')
 ORDER BY owner, db_link;
SPOOL OFF

SPOOL part_indexes.csv
SELECT '"OWNER","INDEX_NAME","TABLE_NAME","LOCALITY"' FROM dual;
SELECT '"' || owner || '","' || REPLACE(index_name, '"', '""') || '","'
       || REPLACE(table_name, '"', '""') || '","' || locality || '"'
  FROM all_part_indexes
 WHERE owner = UPPER('&schema')
 ORDER BY index_name;
SPOOL OFF

SPOOL mviews.csv
SELECT '"OWNER","MVIEW_NAME","REWRITE_ENABLED","REFRESH_METHOD"' FROM dual;
SELECT '"' || owner || '","' || REPLACE(mview_name, '"', '""') || '","'
       || rewrite_enabled || '","' || NVL(refresh_method, '') || '"'
  FROM all_mviews
 WHERE owner = UPPER('&schema')
 ORDER BY mview_name;
SPOOL OFF

-- No DBA_SQL_PLAN_BASELINES before 11.1; stored outlines are the
-- plan-stability mechanism of this era.
SPOOL plan_management.csv
SELECT '"KIND","NAME","ENABLED"' FROM dual;
SELECT '"OUTLINE","' || REPLACE(name, '"', '""') || '","'
       || NVL(enabled, '') || '"'
  FROM dba_outlines
 WHERE owner = UPPER('&schema')
 ORDER BY name;
SPOOL OFF

SPOOL triggers.csv
SELECT '"OWNER","TRIGGER_NAME","TRIGGER_TYPE","TRIGGERING_EVENT",'
       || '"TABLE_NAME","STATUS"'
  FROM dual;
SELECT '"' || owner || '","' || REPLACE(trigger_name, '"', '""') || '","'
       || trigger_type || '","'
       || REPLACE(REPLACE(triggering_event, CHR(13), ' '), CHR(10), ' ')
       || '","' || REPLACE(NVL(table_name, ''), '"', '""') || '","'
       || status || '"'
  FROM all_triggers
 WHERE owner = UPPER('&schema')
 ORDER BY trigger_name;
SPOOL OFF

-- Feature probes limited to views that exist on 9.2. DBMS_SCHEDULER
-- arrived in 10g, so on this tier only legacy DBMS_JOB is counted.
SPOOL features.csv
SELECT '"FEATURE","DETAIL","CNT"' FROM dual;
SELECT '"materialized_views","schema total",' || COUNT(*)
  FROM all_mviews WHERE owner = UPPER('&schema') UNION ALL
SELECT '"db_links","owned or public",' || COUNT(*)
  FROM dba_db_links WHERE owner IN (UPPER('&schema'), 'PUBLIC') UNION ALL
SELECT '"vpd_policies","row level security",' || COUNT(*)
  FROM all_policies WHERE object_owner = UPPER('&schema') UNION ALL
SELECT '"legacy_jobs","dbms_job",' || COUNT(*)
  FROM all_jobs WHERE schema_user = UPPER('&schema') UNION ALL
SELECT '"queues","advanced queuing",' || COUNT(*)
  FROM all_queues WHERE owner = UPPER('&schema') UNION ALL
SELECT '"triggers","schema total",' || COUNT(*)
  FROM all_triggers WHERE owner = UPPER('&schema') UNION ALL
SELECT '"object_types","user defined",' || COUNT(*)
  FROM all_types WHERE owner = UPPER('&schema') UNION ALL
SELECT '"partitioned_tables","schema total",' || COUNT(*)
  FROM all_part_tables WHERE owner = UPPER('&schema') UNION ALL
SELECT '"iot_tables","index organized",' || COUNT(*)
  FROM all_tables
 WHERE owner = UPPER('&schema') AND iot_type IS NOT NULL UNION ALL
SELECT '"temporary_tables","global temporary",' || COUNT(*)
  FROM all_tables
 WHERE owner = UPPER('&schema') AND temporary = 'Y';
SPOOL OFF

-- ---------------------------------------------------------------
-- DDL section, rebuilt from the catalog. Table structure needs no
-- DDL here: columns.csv already carries it.
-- ---------------------------------------------------------------

SPOOL ddl_sequences.sql
SELECT '-- PGRECON_OBJECT SEQUENCE ' || sequence_owner || '.' || sequence_name
       || CHR(10)
       || 'CREATE SEQUENCE "' || sequence_owner || '"."' || sequence_name
       || '" START WITH ' || last_number
       || ' INCREMENT BY ' || increment_by
       || ' MINVALUE ' || min_value
       || CASE WHEN cache_size > 0
               THEN ' CACHE ' || cache_size ELSE ' NOCACHE' END
       || CASE WHEN cycle_flag = 'Y' THEN ' CYCLE' ELSE '' END
       || ';'
  FROM all_sequences
 WHERE sequence_owner = UPPER('&schema')
 ORDER BY sequence_name;
SPOOL OFF

-- View text lives in a LONG column, which cannot be concatenated in
-- SQL. Read it in PL/SQL and print it under a marker line, wrapped to
-- stay inside the 255-byte DBMS_OUTPUT line limit of old servers.
SET SERVEROUTPUT ON SIZE 1000000

SPOOL ddl_views.sql
DECLARE
    l_text  VARCHAR2(32767);
    l_line  VARCHAR2(32767);
    l_pos   PLS_INTEGER;
BEGIN
    FOR v IN (SELECT owner, view_name, text_length, text
                FROM all_views
               WHERE owner = UPPER('&schema')
               ORDER BY view_name) LOOP
        DBMS_OUTPUT.PUT_LINE('-- PGRECON_OBJECT VIEW '
                             || v.owner || '.' || v.view_name);
        IF v.text_length > 32000 THEN
            DBMS_OUTPUT.PUT_LINE('-- view text longer than 32000'
                                 || ' characters, not extracted');
        ELSE
            l_text := 'CREATE OR REPLACE VIEW "' || v.owner || '"."'
                      || v.view_name || '" AS ' || CHR(10) || v.text || ';';
            WHILE l_text IS NOT NULL LOOP
                l_pos := INSTR(l_text, CHR(10));
                IF l_pos = 0 THEN
                    l_line := l_text;
                    l_text := NULL;
                ELSE
                    l_line := SUBSTR(l_text, 1, l_pos - 1);
                    l_text := SUBSTR(l_text, l_pos + 1);
                END IF;
                l_line := REPLACE(l_line, CHR(13), '');
                -- Wrap by bytes, not characters: the pre-10.2 output
                -- limit is 255 bytes and multibyte names count triple.
                -- SUBSTRB may pad a split character with spaces, which
                -- is acceptable for assessment text.
                WHILE LENGTHB(l_line) > 240 LOOP
                    DBMS_OUTPUT.PUT_LINE(SUBSTRB(l_line, 1, 240));
                    l_line := SUBSTRB(l_line, 241);
                END LOOP;
                DBMS_OUTPUT.PUT_LINE(NVL(l_line, ' '));
            END LOOP;
        END IF;
    END LOOP;
END;
/
SPOOL OFF

-- Check conditions and function-based index expressions live in LONG
-- columns; read them in PL/SQL. Values are cut at 200 characters so a
-- quoted CSV row stays inside the 255-byte DBMS_OUTPUT line limit of
-- pre-10.2 servers; anything cut is flagged as truncated.

SPOOL check_conditions.csv
DECLARE
    l_cond VARCHAR2(4000);
BEGIN
    DBMS_OUTPUT.PUT_LINE('"OWNER","CONSTRAINT_NAME","CONDITION","TRUNCATED"');
    FOR c IN (SELECT owner, constraint_name, search_condition
                FROM all_constraints
               WHERE owner = UPPER('&schema')
                 AND constraint_type = 'C'
                 AND table_name NOT LIKE 'BIN$%'
               ORDER BY constraint_name) LOOP
        l_cond := SUBSTRB(c.search_condition, 1, 180);
        l_cond := REPLACE(REPLACE(REPLACE(l_cond, '"', '""'),
                          CHR(13), ' '), CHR(10), ' ');
        DBMS_OUTPUT.PUT_LINE('"' || c.owner || '","' || c.constraint_name
            || '","' || l_cond || '",'
            || CASE WHEN LENGTHB(l_cond) >= 180 THEN 1 ELSE 0 END);
    END LOOP;
END;
/
SPOOL OFF

SPOOL index_expressions.csv
DECLARE
    l_expr VARCHAR2(4000);
BEGIN
    DBMS_OUTPUT.PUT_LINE('"OWNER","INDEX_NAME","COLUMN_POSITION",'
        || '"COLUMN_EXPRESSION","TRUNCATED"');
    FOR e IN (SELECT index_owner, index_name, column_position,
                     column_expression
                FROM all_ind_expressions
               WHERE index_owner = UPPER('&schema')
               ORDER BY index_name, column_position) LOOP
        l_expr := SUBSTRB(e.column_expression, 1, 180);
        l_expr := REPLACE(REPLACE(REPLACE(l_expr, '"', '""'),
                          CHR(13), ' '), CHR(10), ' ');
        DBMS_OUTPUT.PUT_LINE('"' || e.index_owner || '","' || e.index_name
            || '",' || e.column_position || ',"' || l_expr || '",'
            || CASE WHEN LENGTHB(l_expr) >= 180 THEN 1 ELSE 0 END);
    END LOOP;
END;
/
SPOOL OFF

SET TERMOUT ON
PROMPT pgrecon legacy extraction finished. Collect the .csv and .sql files.

EXIT
