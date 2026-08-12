-- Synthetic assessment schema for pgrecon development and testing.
--
-- Creates the RECON_TEST schema and fills it with the constructs that
-- make Oracle to PostgreSQL migrations expensive: package state with
-- an initialization block, a compound trigger, an autonomous
-- transaction, CONNECT BY, interval partitioning, LONG and XMLTYPE
-- columns, a scheduler job, an object type with a body, a loopback
-- database link, and a materialized view. Every construct here should
-- eventually be caught by at least one assessment rule.
--
-- Run against a disposable database only:
--   sqlplus system/<password>@localhost/XEPDB1 @synthetic_schema.sql
--
-- The script drops and recreates the RECON_TEST user.

WHENEVER SQLERROR CONTINUE
SET ECHO ON

DROP USER recon_test CASCADE;

CREATE USER recon_test IDENTIFIED BY "ReconT3st_x" QUOTA UNLIMITED ON users;

GRANT CREATE SESSION,
      CREATE TABLE,
      CREATE VIEW,
      CREATE SEQUENCE,
      CREATE PROCEDURE,
      CREATE TRIGGER,
      CREATE TYPE,
      CREATE SYNONYM,
      CREATE MATERIALIZED VIEW,
      CREATE DATABASE LINK,
      CREATE JOB
   TO recon_test;

CONNECT recon_test/"ReconT3st_x"@localhost/XEPDB1

-- ---------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------

CREATE TABLE dept (
    deptno   NUMBER(2) CONSTRAINT pk_dept PRIMARY KEY,
    dname    VARCHAR2(14) NOT NULL,
    loc      VARCHAR2(13)
);

CREATE TABLE emp (
    empno    NUMBER(4) CONSTRAINT pk_emp PRIMARY KEY,
    ename    VARCHAR2(10) NOT NULL,
    job      VARCHAR2(9),
    mgr      NUMBER(4),
    hiredate DATE DEFAULT SYSDATE,
    sal      NUMBER(7,2) CONSTRAINT ck_emp_sal CHECK (sal > 0),
    comm     NUMBER(7,2),
    deptno   NUMBER(2) CONSTRAINT fk_emp_dept REFERENCES dept (deptno),
    CONSTRAINT fk_emp_mgr FOREIGN KEY (mgr) REFERENCES emp (empno)
);

COMMENT ON TABLE emp IS 'Employees, self-referencing via mgr';
COMMENT ON COLUMN emp.sal IS 'Monthly salary before commission';

-- Identity column plus a virtual column.
CREATE TABLE invoices (
    invoice_id  NUMBER GENERATED ALWAYS AS IDENTITY,
    customer    VARCHAR2(100) NOT NULL,
    net_amount  NUMBER(12,2) NOT NULL,
    vat_rate    NUMBER(4,2) DEFAULT 19,
    gross       NUMBER(14,2) GENERATED ALWAYS AS
                (ROUND(net_amount * (1 + vat_rate / 100), 2)) VIRTUAL,
    created_at  TIMESTAMP(6) WITH LOCAL TIME ZONE DEFAULT SYSTIMESTAMP,
    CONSTRAINT pk_invoices PRIMARY KEY (invoice_id)
);

-- Interval partitioning: partitions materialize as data arrives, a
-- scheme PostgreSQL has no declarative equivalent for.
CREATE TABLE sales (
    sale_id   NUMBER(10) NOT NULL,
    sale_date DATE NOT NULL,
    amount    NUMBER(10,2),
    region    VARCHAR2(20)
)
PARTITION BY RANGE (sale_date)
INTERVAL (NUMTOYMINTERVAL(1, 'MONTH'))
(
    PARTITION p_start VALUES LESS THAN (DATE '2025-01-01')
);

-- Legacy LONG column; only one is allowed per table and the type has
-- been deprecated since Oracle 8.
CREATE TABLE legacy_notes (
    note_id   NUMBER(10) CONSTRAINT pk_legacy_notes PRIMARY KEY,
    body      LONG
);

CREATE TABLE product_specs (
    product_id NUMBER(10) CONSTRAINT pk_product_specs PRIMARY KEY,
    spec       XMLTYPE,
    manual     CLOB,
    thumbnail  BLOB,
    checksum   RAW(32)
);

CREATE GLOBAL TEMPORARY TABLE staging_rows (
    row_id  NUMBER(10),
    payload VARCHAR2(4000)
) ON COMMIT DELETE ROWS;

CREATE TABLE audit_log (
    audit_id   NUMBER GENERATED ALWAYS AS IDENTITY,
    table_name VARCHAR2(30),
    action     VARCHAR2(10),
    actor      VARCHAR2(30),
    logged_at  DATE DEFAULT SYSDATE
);

CREATE SEQUENCE seq_sale_id START WITH 1000 INCREMENT BY 1 CACHE 100;

-- ---------------------------------------------------------------
-- Seed data
-- ---------------------------------------------------------------

INSERT INTO dept VALUES (10, 'ACCOUNTING', 'NEW YORK');
INSERT INTO dept VALUES (20, 'RESEARCH', 'DALLAS');
INSERT INTO dept VALUES (30, 'SALES', 'CHICAGO');

INSERT INTO emp VALUES (7839, 'KING', 'PRESIDENT', NULL,
    DATE '2015-11-17', 5000, NULL, 10);
INSERT INTO emp VALUES (7566, 'JONES', 'MANAGER', 7839,
    DATE '2016-04-02', 2975, NULL, 20);
INSERT INTO emp VALUES (7788, 'SCOTT', 'ANALYST', 7566,
    DATE '2017-12-09', 3000, NULL, 20);
INSERT INTO emp VALUES (7654, 'MARTIN', 'SALESMAN', 7566,
    DATE '2018-09-28', 1250, 1400, 30);

INSERT INTO sales
    SELECT seq_sale_id.NEXTVAL,
           ADD_MONTHS(DATE '2025-01-15', MOD(LEVEL, 6)),
           ROUND(DBMS_RANDOM.VALUE(10, 5000), 2),
           CASE MOD(LEVEL, 3) WHEN 0 THEN 'NORTH'
                              WHEN 1 THEN 'SOUTH'
                              ELSE 'EAST' END
      FROM dual CONNECT BY LEVEL <= 50;

COMMIT;

-- ---------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------

-- Hierarchical query: CONNECT BY has no direct PostgreSQL equivalent
-- and must become a recursive CTE.
CREATE OR REPLACE VIEW v_org_chart AS
SELECT empno,
       ename,
       mgr,
       LEVEL AS depth,
       SYS_CONNECT_BY_PATH(ename, '/') AS chain
  FROM emp
 START WITH mgr IS NULL
CONNECT BY PRIOR empno = mgr;

-- Old-style outer join syntax.
CREATE OR REPLACE VIEW v_emp_dept AS
SELECT e.ename, e.sal, d.dname
  FROM emp e, dept d
 WHERE e.deptno = d.deptno (+);

CREATE MATERIALIZED VIEW mv_dept_salaries
REFRESH COMPLETE ON DEMAND AS
SELECT d.dname, COUNT(*) AS headcount, SUM(e.sal) AS total_sal
  FROM emp e JOIN dept d ON d.deptno = e.deptno
 GROUP BY d.dname;

CREATE SYNONYM staff FOR emp;

CREATE DATABASE LINK loopback
    CONNECT TO recon_test IDENTIFIED BY "ReconT3st_x"
    USING '//localhost:1521/XEPDB1';

-- ---------------------------------------------------------------
-- Object type with body
-- ---------------------------------------------------------------

CREATE OR REPLACE TYPE t_money AS OBJECT (
    amount   NUMBER(14,2),
    currency VARCHAR2(3),
    MEMBER FUNCTION in_currency (rate NUMBER) RETURN NUMBER
);
/

CREATE OR REPLACE TYPE BODY t_money AS
    MEMBER FUNCTION in_currency (rate NUMBER) RETURN NUMBER IS
    BEGIN
        RETURN ROUND(amount * rate, 2);
    END;
END;
/

-- ---------------------------------------------------------------
-- Package with global state and an initialization block
-- ---------------------------------------------------------------

CREATE OR REPLACE PACKAGE pkg_ledger AS
    g_run_id      NUMBER;
    g_batch_size  CONSTANT PLS_INTEGER := 500;

    PROCEDURE post_sale (p_amount NUMBER, p_region VARCHAR2);
    FUNCTION  run_total RETURN NUMBER;
    PROCEDURE rollup_day;
END pkg_ledger;
/

CREATE OR REPLACE PACKAGE BODY pkg_ledger AS
    g_total NUMBER := 0;

    PROCEDURE post_sale (p_amount NUMBER, p_region VARCHAR2) IS
    BEGIN
        INSERT INTO sales (sale_id, sale_date, amount, region)
        VALUES (seq_sale_id.NEXTVAL, SYSDATE, p_amount, p_region);
        g_total := g_total + p_amount;
    END post_sale;

    FUNCTION run_total RETURN NUMBER IS
    BEGIN
        RETURN g_total;
    END run_total;

    PROCEDURE rollup_day IS
        CURSOR c_regions IS
            SELECT region, SUM(amount) AS amt
              FROM sales GROUP BY region;
        TYPE t_rows IS TABLE OF c_regions%ROWTYPE;
        l_rows t_rows;
    BEGIN
        OPEN c_regions;
        FETCH c_regions BULK COLLECT INTO l_rows;
        CLOSE c_regions;
        FOR i IN 1 .. l_rows.COUNT LOOP
            EXECUTE IMMEDIATE
                'UPDATE staging_rows SET payload = :1 WHERE row_id = :2'
                USING l_rows(i).region, i;
        END LOOP;
    END rollup_day;

-- Package initialization: runs once per session on first reference,
-- a behavior PostgreSQL has no counterpart for.
BEGIN
    SELECT NVL(MAX(audit_id), 0) + 1 INTO g_run_id FROM audit_log;
END pkg_ledger;
/

-- Standalone procedure with OUT parameters and a GOTO.
CREATE OR REPLACE PROCEDURE find_manager (
    p_empno  IN  NUMBER,
    p_mgr    OUT VARCHAR2,
    p_depth  OUT PLS_INTEGER
) AS
    l_mgr NUMBER;
BEGIN
    p_depth := 0;
    l_mgr := p_empno;
    <<climb>>
    SELECT mgr INTO l_mgr FROM emp WHERE empno = l_mgr;
    IF l_mgr IS NOT NULL THEN
        p_depth := p_depth + 1;
        GOTO climb;
    END IF;
    SELECT ename INTO p_mgr FROM emp WHERE mgr IS NULL;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        p_mgr := NULL;
END find_manager;
/

CREATE OR REPLACE FUNCTION dept_headcount (p_deptno NUMBER)
    RETURN NUMBER DETERMINISTIC AS
    l_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO l_count FROM emp WHERE deptno = p_deptno;
    RETURN l_count;
END dept_headcount;
/

-- ---------------------------------------------------------------
-- Triggers
-- ---------------------------------------------------------------

-- Compound trigger: one body, four timing sections.
CREATE OR REPLACE TRIGGER trg_emp_sal_guard
FOR INSERT OR UPDATE OF sal ON emp
COMPOUND TRIGGER
    g_stmt_start DATE;

    BEFORE STATEMENT IS
    BEGIN
        g_stmt_start := SYSDATE;
    END BEFORE STATEMENT;

    BEFORE EACH ROW IS
    BEGIN
        IF :NEW.sal > 10000 THEN
            :NEW.comm := 0;
        END IF;
    END BEFORE EACH ROW;

    AFTER EACH ROW IS
    BEGIN
        NULL;
    END AFTER EACH ROW;

    AFTER STATEMENT IS
    BEGIN
        NULL;
    END AFTER STATEMENT;
END trg_emp_sal_guard;
/

-- Autonomous transaction: the audit row commits even when the
-- triggering transaction rolls back.
CREATE OR REPLACE TRIGGER trg_emp_audit
AFTER INSERT OR UPDATE OR DELETE ON emp
FOR EACH ROW
DECLARE
    PRAGMA AUTONOMOUS_TRANSACTION;
    l_action VARCHAR2(10);
BEGIN
    l_action := CASE
        WHEN INSERTING THEN 'INSERT'
        WHEN UPDATING  THEN 'UPDATE'
        ELSE 'DELETE'
    END;
    INSERT INTO audit_log (table_name, action, actor)
    VALUES ('EMP', l_action, USER);
    COMMIT;
END trg_emp_audit;
/

-- ---------------------------------------------------------------
-- Scheduler job (disabled; it exists to be inventoried, not to run)
-- ---------------------------------------------------------------

BEGIN
    DBMS_SCHEDULER.CREATE_JOB(
        job_name        => 'NIGHTLY_ROLLUP',
        job_type        => 'STORED_PROCEDURE',
        job_action      => 'PKG_LEDGER.ROLLUP_DAY',
        repeat_interval => 'FREQ=DAILY;BYHOUR=2',
        enabled         => FALSE,
        comments        => 'Synthetic job for assessment testing');
END;
/

PROMPT synthetic schema created

EXIT
