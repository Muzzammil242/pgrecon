"""Sequence, synonym, and database link emission."""

import re
import sqlite3

from pgrecon.convert.identifiers import ident
from pgrecon.convert.residue import Residue

_INTEGERISH = re.compile(r"^-?\d+$")
_PG_BIGINT_MAX = 9223372036854775807


def _emit_sequences(
    conn: sqlite3.Connection, out: list[str], residue: list[Residue]
) -> int:
    """Sequences restarted at their extracted position.

    Oracle bounds reach 1e28; a bound past bigint is treated as
    unbounded rather than declined, because that is what it means in
    practice. Anything else non-numeric declines.
    """
    rows = conn.execute(
        "SELECT owner, sequence_name, min_value, max_value, increment_by,"
        " cycle_flag, cache_size, last_number FROM sequences"
        " ORDER BY owner, sequence_name"
    ).fetchall()
    count = 0
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
        count += 1
    if count:
        out.append("")
    return count


def _emit_synonyms(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    created_views: set[str],
) -> int:
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
        count += 1
    if count:
        out.append("")
    return count


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
        if count == 0:
            out.append("CREATE EXTENSION IF NOT EXISTS oracle_fdw;")
        link = ident((r["db_link"] or "").split(".")[0])
        out.append(
            f"CREATE SERVER {link} FOREIGN DATA WRAPPER oracle_fdw"
            f" OPTIONS (dbserver '{(r['host'] or '').replace(chr(39), '')}');"
        )
        user = (r["username"] or "").replace("'", "")
        out.append(
            f"CREATE USER MAPPING FOR CURRENT_USER SERVER {link}"
            f" OPTIONS (\"user\" '{user}', password '');"
        )
        residue.append(
            Residue(
                r["owner"],
                r["db_link"],
                "note",
                "database link scaffolded as an oracle_fdw server;"
                " complete the credentials and define foreign tables"
                " for what the link serves",
            )
        )
        count += 1
    if count:
        out.append("")
    return count
