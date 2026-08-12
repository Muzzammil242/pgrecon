"""Rules over column data types."""

from pgrecon.rules import Rule, Severity, sql_detector

RULES = [
    Rule(
        id="R-TYPE-01",
        title="LONG or LONG RAW column",
        category="data types",
        severity=Severity.HIGH,
        effort=4.0,
        remedy=(
            "LONG has been deprecated since Oracle 8. Map LONG to text and"
            " LONG RAW to bytea; any code reading the column piecewise must"
            " be rewritten, and only one LONG per table exists to find."
        ),
        detector=sql_detector(
            "SELECT owner, table_name || '.' || column_name, 'COLUMN',"
            " data_type FROM columns WHERE data_type IN ('LONG', 'LONG RAW')"
        ),
    ),
    Rule(
        id="R-TYPE-02",
        title="XMLTYPE column",
        category="data types",
        severity=Severity.MEDIUM,
        effort=3.0,
        remedy=(
            "PostgreSQL xml stores documents but has no XML index type and"
            " none of the XMLType member functions; XQuery support differs."
            " Inventory how the application queries the XML before mapping."
        ),
        detector=sql_detector(
            "SELECT owner, table_name || '.' || column_name, 'COLUMN',"
            " data_type FROM columns WHERE data_type LIKE '%XMLTYPE%'"
        ),
    ),
    Rule(
        id="R-TYPE-03",
        title="TIMESTAMP WITH LOCAL TIME ZONE column",
        category="data types",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "Values are normalized to the session time zone on read, which"
            " timestamptz does not replicate exactly. Verify every reader"
            " assumes UTC or one fixed zone before mapping to timestamptz."
        ),
        detector=sql_detector(
            "SELECT owner, table_name || '.' || column_name, 'COLUMN',"
            " data_type FROM columns"
            " WHERE data_type LIKE '%WITH LOCAL TIME ZONE%'"
        ),
    ),
    Rule(
        id="R-TYPE-05",
        title="Column named after a PostgreSQL reserved word",
        category="data types",
        severity=Severity.INFO,
        effort=0.2,
        remedy=(
            "Legal in Oracle, but in PostgreSQL the name must be quoted"
            " everywhere or renamed once during migration. Renaming is"
            " cheaper than a lifetime of quoting."
        ),
        detector=sql_detector(
            "SELECT owner, table_name || '.' || column_name, 'COLUMN',"
            " 'reserved word in PostgreSQL' FROM columns"
            " WHERE UPPER(column_name) IN ("
            "'ALL','ANALYSE','ANALYZE','AND','ANY','ARRAY','AS','ASC',"
            "'BOTH','CASE','CAST','CHECK','COLLATE','COLUMN','CONSTRAINT',"
            "'DEFAULT','DEFERRABLE','DESC','DISTINCT','DO','ELSE','END',"
            "'EXCEPT','FOR','FOREIGN','FROM','GRANT','GROUP','HAVING',"
            "'IN','INITIALLY','INTERSECT','INTO','LATERAL','LEADING',"
            "'LIMIT','LOCALTIME','NOT','NULL','OFFSET','ON','ONLY','OR',"
            "'ORDER','PLACING','PRIMARY','REFERENCES','RETURNING',"
            "'SELECT','SOME','SYMMETRIC','TABLE','THEN','TO','TRAILING',"
            "'UNION','UNIQUE','USER','USING','VARIADIC','WHEN','WHERE',"
            "'WINDOW','WITH')"
        ),
    ),
    Rule(
        id="R-TYPE-04",
        title="NUMBER without precision",
        category="data types",
        severity=Severity.LOW,
        effort=0.2,
        remedy=(
            "Bare NUMBER accepts up to 38 significant digits. Map to"
            " numeric, and check whether application code assumes integer"
            " behavior that a typed bigint would express better."
        ),
        detector=sql_detector(
            "SELECT owner, table_name || '.' || column_name, 'COLUMN',"
            " 'NUMBER with no precision' FROM columns"
            " WHERE data_type = 'NUMBER' AND data_precision IS NULL"
        ),
    ),
]
