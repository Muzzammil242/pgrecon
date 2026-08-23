"""Sequence, synonym, and database link emission."""

import re
import sqlite3

from pgrecon.convert.identifiers import ident
from pgrecon.convert.residue import Residue

_INTEGERISH = re.compile(r"^-?\d+$")
_PG_BIGINT_MAX = 9223372036854775807


def _emit_sequences(
    conn: sqlite3.Connection, out: list[str], residue: list[Residue]
) -> tuple[int, set[str]]:
    """Sequences restarted at their extracted position.

    Oracle bounds reach 1e28; a bound past bigint is treated as
    unbounded rather than declined, because that is what it means in
    practice. Anything else non-numeric declines. Returns the count
    and the emitted names, which the code lane validates NEXTVAL
    references against.
    """
    rows = conn.execute(
        "SELECT owner, sequence_name, min_value, max_value, increment_by,"
        " cycle_flag, cache_size, last_number FROM sequences"
        " ORDER BY owner, sequence_name"
    ).fetchall()
    count = 0
    created: set[str] = set()
    for r in rows:
        fields = {
            k: (r[k] or "").strip()
            for k in ("min_value", "max_value", "increment_by", "last_number")
        }
        if not all(
            _INTEGERISH.match(v) for k, v in fields.items() if k != "max_value"
        ) or not (_INTEGERISH.match(fields["max_value"]) or not fields["max_value"]):
            residue.append(
                Residue(
                    r["owner"],
                    r["sequence_name"],
                    "sequence",
                    "bounds did not extract as numbers; recreate by hand",
                )
            )
            continue
        parts = [f"CREATE SEQUENCE {ident(r['sequence_name'])}"]
        parts.append(f"INCREMENT BY {fields['increment_by']}")
        if abs(int(fields["min_value"])) <= _PG_BIGINT_MAX:
            parts.append(f"MINVALUE {fields['min_value']}")
        if fields["max_value"] and int(fields["max_value"]) <= _PG_BIGINT_MAX:
            parts.append(f"MAXVALUE {fields['max_value']}")
        start = int(fields["last_number"])
        if start > _PG_BIGINT_MAX:
            residue.append(
                Residue(
                    r["owner"],
                    r["sequence_name"],
                    "sequence",
                    "current value exceeds bigint; recreate by hand",
                )
            )
            continue
        parts.append(f"START WITH {start}")
        cache = (r["cache_size"] or "").strip()
        if _INTEGERISH.match(cache) and int(cache) > 1:
            parts.append(f"CACHE {cache}")
        if (r["cycle_flag"] or "N") == "Y":
            parts.append("CYCLE")
        out.append(" ".join(parts) + ";")
        created.add((r["sequence_name"] or "").upper())
        count += 1
    if count:
        out.append("")
    return count, created


def _emit_synonyms(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    created_views: set[str],
) -> tuple[int, set[str]]:
    """Schema-local synonyms over converted relations become views.

    A simple SELECT * view is updatable on PostgreSQL, which is as
    close to a synonym as vanilla PostgreSQL gets. Anything pointing
    at a database link, a public synonym, or an unconverted target
    declines with the reason.
    """
    rows = conn.execute(
        "SELECT owner, synonym_name, table_owner, table_name, db_link"
        " FROM synonyms ORDER BY owner, synonym_name"
    ).fetchall()
    known = {t for (_, t) in emitted} | created_views
    count = 0
    created: set[str] = set()
    for r in rows:
        if r["db_link"]:
            residue.append(
                Residue(
                    r["owner"],
                    r["synonym_name"],
                    "synonym",
                    "points through a database link; reach the remote"
                    " table with a foreign table instead",
                )
            )
            continue
        if (r["owner"] or "").upper() == "PUBLIC":
            residue.append(
                Residue(
                    r["owner"],
                    r["synonym_name"],
                    "synonym",
                    "public synonym; PostgreSQL resolves names through"
                    " search_path - decide placement by hand",
                )
            )
            continue
        target = (r["table_name"] or "").upper()
        if target not in known:
            residue.append(
                Residue(
                    r["owner"],
                    r["synonym_name"],
                    "synonym",
                    f"its target {target} is not in the converted set",
                )
            )
            continue
        out.append(
            f"CREATE OR REPLACE VIEW {ident(r['synonym_name'])}"
            f" AS SELECT * FROM {ident(r['table_name'])};"
        )
        created.add((r["synonym_name"] or "").upper())
        count += 1
    if count:
        out.append("")
    return count, created


def _emit_db_links(
    conn: sqlite3.Connection, out: list[str], residue: list[Residue]
) -> int:
    """Database links scaffold as oracle_fdw servers.

    The dictionary never yields the password, so the user mapping is
    emitted with an empty one and the residue says to complete the
    credentials and define foreign tables for whatever the link
    serves.
    """
    rows = conn.execute(
        "SELECT owner, db_link, username, host FROM db_links ORDER BY owner, db_link"
    ).fetchall()
    count = 0
    for r in rows:
        # The scaffold ships commented: it needs the oracle_fdw
        # extension, credentials, and foreign tables - a recipe to
        # complete, not DDL that applies on a vanilla server.
        if count == 0:
            out.append("-- CREATE EXTENSION IF NOT EXISTS oracle_fdw;")
        link = ident((r["db_link"] or "").split(".")[0])
        out.append(
            f"-- CREATE SERVER {link} FOREIGN DATA WRAPPER oracle_fdw"
            f" OPTIONS (dbserver '{(r['host'] or '').replace(chr(39), '')}');"
        )
        user = (r["username"] or "").replace("'", "")
        out.append(
            f"-- CREATE USER MAPPING FOR CURRENT_USER SERVER {link}"
            f" OPTIONS (\"user\" '{user}', password '');"
        )
        residue.append(
            Residue(
                r["owner"],
                r["db_link"],
                "note",
                "database link scaffolded as a commented oracle_fdw"
                " recipe; install the extension, complete the"
                " credentials, and define foreign tables for what the"
                " link serves",
            )
        )
        count += 1
    if count:
        out.append("")
    return count


def _emit_comments(
    conn: sqlite3.Connection,
    out: list[str],
    emitted: dict[tuple[str, str], set[str]],
    matviews: set[str],
    created_views: set[str],
) -> int:
    """COMMENT ON for surviving objects.

    A comment follows its object: comments on tables, columns, or
    views that did not convert vanish with them - their absence is
    already a named residue line, and a comment on nothing means
    nothing.
    """
    count = 0
    tables = {t for (_, t) in emitted}
    for r in conn.execute(
        "SELECT owner, table_name, comments FROM table_comments ORDER BY table_name"
    ):
        name = (r["table_name"] or "").upper()
        text = (r["comments"] or "").replace("'", "''")
        if name in matviews:
            kind = "MATERIALIZED VIEW"
        elif name in created_views:
            kind = "VIEW"
        elif name in tables:
            kind = "TABLE"
        else:
            continue
        out.append(f"COMMENT ON {kind} {ident(name.lower())} IS '{text}';")
        count += 1
    for r in conn.execute(
        "SELECT owner, table_name, column_name, comments FROM column_comments"
        " ORDER BY table_name, column_name"
    ):
        name = (r["table_name"] or "").upper()
        col = (r["column_name"] or "").upper()
        kept = emitted.get((r["owner"], name))
        if name in matviews or name in created_views:
            pass  # matview and view columns exist; comment applies
        elif kept is None or col not in kept:
            continue
        text = (r["comments"] or "").replace("'", "''")
        out.append(
            f"COMMENT ON COLUMN {ident(name.lower())}.{ident(col.lower())} IS '{text}';"
        )
        count += 1
    if count:
        out.append("")
    return count


# Oracle object privileges with a direct PostgreSQL counterpart, per
# relation kind. EXECUTE is absent on purpose: PostgreSQL grants on
# routines need the argument list, so they decline by name instead.
_RELATION_PRIVS = {
    "SELECT": "SELECT",
    "READ": "SELECT",
    "INSERT": "INSERT",
    "UPDATE": "UPDATE",
    "DELETE": "DELETE",
    "REFERENCES": "REFERENCES",
    "TRIGGER": "TRIGGER",
}
_SEQUENCE_PRIVS = {"SELECT": "USAGE, SELECT", "ALTER": "UPDATE"}


def _emit_grants(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    matviews: set[str],
    created_views: set[str],
    sequence_names: set[str],
) -> int:
    """Object grants, with the roles they need bootstrapped first.

    Grantees become roles created only if absent, so the script stays
    idempotent and never fights an existing user. PUBLIC stays
    PUBLIC. A privilege with no counterpart on the object's kind is a
    named residue line, never a dropped permission.
    """
    rows = conn.execute(
        "SELECT grantee, owner, table_name, privilege, grantable FROM grants"
        " ORDER BY table_name, grantee, privilege"
    ).fetchall()
    if not rows:
        return 0
    tables = {t for (_, t) in emitted}
    known = tables | matviews | created_views | sequence_names
    grantees = sorted(
        {
            (r["grantee"] or "").upper()
            for r in rows
            if (r["grantee"] or "").upper() != "PUBLIC"
            and (r["table_name"] or "").upper() in known
        }
    )
    for grantee in grantees:
        role = ident(grantee.lower())
        quoted = grantee.lower().replace("'", "''")
        out.append(
            "DO $$ BEGIN\n"
            f"  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{quoted}')"
            " THEN\n"
            f"    CREATE ROLE {role};\n"
            "  END IF;\n"
            "END $$;"
        )
    count = 0
    for r in rows:
        name = (r["table_name"] or "").upper()
        priv = (r["privilege"] or "").upper()
        grantee = (r["grantee"] or "").upper()
        if name not in known:
            continue  # the object's absence is already named
        if name in sequence_names:
            mapped = _SEQUENCE_PRIVS.get(priv)
            kind = "SEQUENCE "
        else:
            mapped = _RELATION_PRIVS.get(priv)
            kind = ""
        if mapped is None:
            residue.append(
                Residue(
                    r["owner"],
                    f"{name}.{priv}->{grantee}",
                    "grant",
                    f"{priv} has no direct PostgreSQL counterpart on this"
                    " object; grant an equivalent by hand",
                )
            )
            continue
        target = "PUBLIC" if grantee == "PUBLIC" else ident(grantee.lower())
        option = " WITH GRANT OPTION" if (r["grantable"] or "").upper() == "YES" else ""
        out.append(
            f"GRANT {mapped} ON {kind}{ident(name.lower())} TO {target}{option};"
        )
        count += 1
    if count or grantees:
        out.append("")
    return count
