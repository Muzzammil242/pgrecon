-- pgrecon offline extraction script
--
-- Purpose: dump the metadata needed for a PostgreSQL migration
-- assessment of one schema into a folder of plain text files. The
-- script only reads the data dictionary. It does not read table data,
-- it does not write to the database, and it does not require SYSDBA.
--
-- Requirements:
--   * SQL*Plus 12.2 or newer (uses SET MARKUP CSV).
--   * An account with SELECT_CATALOG_ROLE, or any account that can see
--     the target schema's objects through the ALL_* views.
--
-- Usage:
--   1. Create an empty working directory and cd into it.
--   2. sqlplus readonly_user@service @pgrecon_extract.sql SCHEMA_NAME
--   3. Send the resulting folder of .csv and .sql files back for
--      assessment.
--
-- Review notice: this script is intentionally plain so that a DBA can
-- audit every statement before running it. Every query below selects
-- from ALL_* dictionary views or DUAL only.

WHENEVER OSERROR CONTINUE
WHENEVER SQLERROR CONTINUE

SET ECHO OFF
SET VERIFY OFF
SET FEEDBACK OFF
SET HEADING OFF
SET TERMOUT ON
PROMPT pgrecon extraction starting for schema &1

-- Runtime guards: stop with a readable message instead of spooling a
-- broken dump. The client check reads the predefined _SQLPLUS_RELEASE
-- variable (present since SQL*Plus 10.1; a 9i client should be using
-- the legacy variant to begin with).
PROMPT Checking client and server versions ...
PROMPT If the script stops below this line, use the legacy variant
PROMPT instead: pgrecon script --legacy
WHENEVER SQLERROR EXIT FAILURE
SELECT CASE WHEN TO_NUMBER('&_SQLPLUS_RELEASE') >= 1202000000
            THEN 'client ok'
            ELSE TO_CHAR(TO_NUMBER('client older than 12.2')) END
  FROM dual;
SELECT CASE WHEN TO_NUMBER(SUBSTR(version, 1, INSTR(version, '.') - 1)) * 100
            + TO_NUMBER(SUBSTR(version, INSTR(version, '.') + 1,
                        INSTR(version, '.', 1, 2) - INSTR(version, '.') - 1))
            >= 1102
            THEN 'server ok'
            ELSE TO_CHAR(TO_NUMBER('server older than 11.2')) END
  FROM product_component_version
 WHERE product LIKE 'Oracle%' AND ROWNUM = 1;
WHENEVER SQLERROR CONTINUE

SET HEADING ON
SET TERMOUT OFF
SET TRIMSPOOL ON
SET PAGESIZE 50000
SET LINESIZE 32767
SET LONG 20000000
SET LONGCHUNKSIZE 32767
-- Fetch in large batches; on big schemas the source and column spools
-- are dominated by round trips otherwise.
SET ARRAYSIZE 500

DEFINE schema = &1

-- ---------------------------------------------------------------
-- CSV section: catalog metadata
-- ---------------------------------------------------------------
SET MARKUP CSV ON QUOTE ON

SPOOL meta.csv
SELECT 'schema' AS key, UPPER('&schema') AS value FROM dual
UNION ALL
SELECT 'extracted_at', TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') FROM dual
UNION ALL
SELECT 'product', product FROM product_component_version
 WHERE product LIKE 'Oracle%' AND ROWNUM = 1
UNION ALL
SELECT 'version', version FROM product_component_version
 WHERE product LIKE 'Oracle%' AND ROWNUM = 1;
SPOOL OFF

-- Recycle-bin objects (BIN$), identity-column sequences (ISEQ$$) and
-- secondary objects (for example domain index internals) are noise for
-- an assessment and are excluded here.
SPOOL objects.csv
SELECT owner,
       object_name,
       object_type,
       status,
       TO_CHAR(created, 'YYYY-MM-DD HH24:MI:SS') AS created,
       TO_CHAR(last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') AS last_ddl_time
  FROM all_objects
 WHERE owner = UPPER('&schema')
   AND secondary = 'N'
   AND object_name NOT LIKE 'BIN$%'
   AND object_name NOT LIKE 'ISEQ$$%'
   AND object_type NOT IN (
       'LOB', 'TABLE PARTITION', 'TABLE SUBPARTITION',
       'INDEX PARTITION', 'INDEX SUBPARTITION', 'LOB PARTITION')
 ORDER BY object_type, object_name;
SPOOL OFF

-- NUM_ROWS and AVG_ROW_LEN come from optimizer statistics; they size
-- the data-migration estimate without counting rows in the tables.
SPOOL tables.csv
SELECT owner,
       table_name,
       num_rows,
       avg_row_len,
       partitioned,
       temporary
  FROM all_tables
 WHERE owner = UPPER('&schema')
   AND nested = 'NO'
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY table_name;
SPOOL OFF

SPOOL columns.csv
SELECT owner,
       table_name,
       column_name,
       column_id,
       data_type,
       data_length,
       data_precision,
       data_scale,
       nullable
  FROM all_tab_columns
 WHERE owner = UPPER('&schema')
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY table_name, column_id;
SPOOL OFF

SPOOL source.csv
SELECT owner, name, type, line, text
  FROM all_source
 WHERE owner = UPPER('&schema')
 ORDER BY owner, name, type, line;
SPOOL OFF

SPOOL dependencies.csv
SELECT owner,
       name,
       type,
       referenced_owner,
       referenced_name,
       referenced_type
  FROM all_dependencies
 WHERE owner = UPPER('&schema')
   AND referenced_owner NOT IN ('SYS', 'SYSTEM', 'PUBLIC')
 ORDER BY name, referenced_name;
SPOOL OFF

SPOOL constraints.csv
SELECT owner,
       constraint_name,
       table_name,
       constraint_type,
       status,
       r_owner,
       r_constraint_name,
       delete_rule
  FROM all_constraints
 WHERE owner = UPPER('&schema')
   AND constraint_type IN ('P', 'R', 'U', 'C')
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY table_name, constraint_name;
SPOOL OFF

SPOOL constraint_columns.csv
SELECT owner, constraint_name, column_name, position
  FROM all_cons_columns
 WHERE owner = UPPER('&schema')
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY constraint_name, position;
SPOOL OFF

SPOOL indexes.csv
SELECT owner,
       index_name,
       table_name,
       index_type,
       uniqueness,
       status,
       generated
  FROM all_indexes
 WHERE owner = UPPER('&schema')
   AND index_name NOT LIKE 'BIN$%'
 ORDER BY table_name, index_name;
SPOOL OFF

SPOOL index_columns.csv
SELECT index_owner AS owner, index_name, column_name, column_position
  FROM all_ind_columns
 WHERE index_owner = UPPER('&schema')
 ORDER BY index_name, column_position;
SPOOL OFF

SPOOL part_tables.csv
SELECT owner,
       table_name,
       partitioning_type,
       subpartitioning_type,
       partition_count,
       interval
  FROM all_part_tables
 WHERE owner = UPPER('&schema')
 ORDER BY table_name;
SPOOL OFF

SPOOL part_key_columns.csv
SELECT owner, name, column_name, column_position
  FROM all_part_key_columns
 WHERE owner = UPPER('&schema')
   AND object_type = 'TABLE'
 ORDER BY name, column_position;
SPOOL OFF

SPOOL synonyms.csv
SELECT owner, synonym_name, table_owner, table_name, db_link
  FROM all_synonyms
 WHERE owner = UPPER('&schema')
    OR (owner = 'PUBLIC' AND table_owner = UPPER('&schema'))
 ORDER BY owner, synonym_name;
SPOOL OFF

SPOOL triggers.csv
SELECT owner,
       trigger_name,
       trigger_type,
       triggering_event,
       table_name,
       status
  FROM all_triggers
 WHERE owner = UPPER('&schema')
 ORDER BY trigger_name;
SPOOL OFF

-- Feature probes: one row per feature with a count. Each of these
-- influences migration effort in a different way.
SPOOL features.csv
SELECT 'materialized_views' AS feature, 'schema total' AS detail, COUNT(*) AS cnt
  FROM all_mviews WHERE owner = UPPER('&schema')
UNION ALL
SELECT 'db_links', 'owned or public', COUNT(*)
  FROM all_db_links WHERE owner IN (UPPER('&schema'), 'PUBLIC')
UNION ALL
SELECT 'scheduler_jobs', 'schema total', COUNT(*)
  FROM all_scheduler_jobs WHERE owner = UPPER('&schema')
UNION ALL
SELECT 'legacy_jobs', 'dbms_job', COUNT(*)
  FROM all_jobs WHERE schema_user = UPPER('&schema')
UNION ALL
SELECT 'queues', 'advanced queuing', COUNT(*)
  FROM all_queues WHERE owner = UPPER('&schema')
UNION ALL
SELECT 'triggers', 'schema total', COUNT(*)
  FROM all_triggers WHERE owner = UPPER('&schema')
UNION ALL
SELECT 'object_types', 'user defined', COUNT(*)
  FROM all_types WHERE owner = UPPER('&schema')
UNION ALL
SELECT 'partitioned_tables', 'schema total', COUNT(*)
  FROM all_part_tables WHERE owner = UPPER('&schema')
UNION ALL
SELECT 'iot_tables', 'index organized', COUNT(*)
  FROM all_tables
 WHERE owner = UPPER('&schema') AND iot_type IS NOT NULL
UNION ALL
SELECT 'external_tables', 'schema total', COUNT(*)
  FROM all_external_tables WHERE owner = UPPER('&schema')
UNION ALL
SELECT 'temporary_tables', 'global temporary', COUNT(*)
  FROM all_tables
 WHERE owner = UPPER('&schema') AND temporary = 'Y';
SPOOL OFF

SET MARKUP CSV OFF

-- ---------------------------------------------------------------
-- DDL section: one statement per object, preceded by a marker line
-- the loader splits on. Storage clauses are suppressed because they
-- carry no meaning for a PostgreSQL assessment.
-- ---------------------------------------------------------------
SET HEADING OFF

BEGIN
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'STORAGE', FALSE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'TABLESPACE', FALSE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SEGMENT_ATTRIBUTES', FALSE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', TRUE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'PRETTY', TRUE);
END;
/

SPOOL ddl_tables.sql
SELECT '-- PGRECON_OBJECT TABLE ' || owner || '.' || table_name || CHR(10)
       || DBMS_METADATA.GET_DDL('TABLE', table_name, owner)
  FROM all_tables
 WHERE owner = UPPER('&schema')
   AND nested = 'NO'
   AND table_name NOT LIKE 'BIN$%'
 ORDER BY table_name;
SPOOL OFF

SPOOL ddl_views.sql
SELECT '-- PGRECON_OBJECT VIEW ' || owner || '.' || view_name || CHR(10)
       || DBMS_METADATA.GET_DDL('VIEW', view_name, owner)
  FROM all_views
 WHERE owner = UPPER('&schema')
 ORDER BY view_name;
SPOOL OFF

SPOOL ddl_sequences.sql
SELECT '-- PGRECON_OBJECT SEQUENCE ' || sequence_owner || '.' || sequence_name || CHR(10)
       || DBMS_METADATA.GET_DDL('SEQUENCE', sequence_name, sequence_owner)
  FROM all_sequences
 WHERE sequence_owner = UPPER('&schema')
   AND sequence_name NOT LIKE 'ISEQ$$%'
 ORDER BY sequence_name;
SPOOL OFF

-- Check conditions and function-based index expressions live in LONG
-- columns, which SQL cannot concatenate into CSV rows. Read them in
-- PL/SQL instead; 2000 characters is plenty for assessment purposes
-- and anything longer is flagged as truncated.
SET SERVEROUTPUT ON SIZE UNLIMITED

SPOOL check_conditions.csv
BEGIN
    DBMS_OUTPUT.PUT_LINE('"OWNER","CONSTRAINT_NAME","CONDITION","TRUNCATED"');
    FOR c IN (SELECT owner, constraint_name, search_condition
                FROM all_constraints
               WHERE owner = UPPER('&schema')
                 AND constraint_type = 'C'
                 AND table_name NOT LIKE 'BIN$%'
               ORDER BY constraint_name) LOOP
        DECLARE
            l_cond VARCHAR2(2000);
        BEGIN
            l_cond := SUBSTR(c.search_condition, 1, 2000);
            l_cond := REPLACE(REPLACE(REPLACE(l_cond, '"', '""'),
                              CHR(13), ' '), CHR(10), ' ');
            DBMS_OUTPUT.PUT_LINE('"' || c.owner || '","'
                || c.constraint_name || '","' || l_cond || '",'
                || CASE WHEN LENGTH(l_cond) >= 2000 THEN 1 ELSE 0 END);
        END;
    END LOOP;
END;
/
SPOOL OFF

SPOOL index_expressions.csv
BEGIN
    DBMS_OUTPUT.PUT_LINE('"OWNER","INDEX_NAME","COLUMN_POSITION",'
        || '"COLUMN_EXPRESSION","TRUNCATED"');
    FOR e IN (SELECT index_owner, index_name, column_position,
                     column_expression
                FROM all_ind_expressions
               WHERE index_owner = UPPER('&schema')
               ORDER BY index_name, column_position) LOOP
        DECLARE
            l_expr VARCHAR2(2000);
        BEGIN
            l_expr := SUBSTR(e.column_expression, 1, 2000);
            l_expr := REPLACE(REPLACE(REPLACE(l_expr, '"', '""'),
                              CHR(13), ' '), CHR(10), ' ');
            DBMS_OUTPUT.PUT_LINE('"' || e.index_owner || '","'
                || e.index_name || '",' || e.column_position || ',"'
                || l_expr || '",'
                || CASE WHEN LENGTH(l_expr) >= 2000 THEN 1 ELSE 0 END);
        END;
    END LOOP;
END;
/
SPOOL OFF

SET TERMOUT ON
PROMPT pgrecon extraction finished. Collect the .csv and .sql files.

EXIT
