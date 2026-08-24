"""The shared map of names PostgreSQL folds emitted objects into.

PostgreSQL keeps tables, views, materialized views, sequences,
indexes, and the indexes backing PRIMARY KEY and UNIQUE constraints
in one namespace per schema (pg_class), and truncates every
identifier to 63 bytes at parse time. Oracle partitions its
namespaces differently and allows 128-byte names from 12.2, so a
legal source schema can hold pairs that fold to a single name on the
target - an index named after its table, or two long names agreeing
on their first 63 bytes. Emitting both would make the DDL fail, or
worse, let a CREATE OR REPLACE silently replace the earlier object.

One registry instance covers a conversion. The emission order in
schema.py decides who wins a name: the first claimant keeps it and
every later collider becomes a residue line naming the earlier
object. Routines live in their own namespace (pg_proc), and
constraints and triggers are per table (pg_constraint, pg_trigger);
scopes keep those apart.
"""

from pgrecon.convert.identifiers import over_limit, pg_truncate
from pgrecon.convert.residue import Residue

RELATIONS = ""
ROUTINES = "routines"


class NameRegistry:
    """First-claimant-wins bookkeeping over folded names."""

    def __init__(self) -> None:
        self._claimed: dict[tuple[str, str], tuple[str, str]] = {}

    def peek(self, name: str, scope: str = RELATIONS) -> tuple[str, str] | None:
        """The (name, kind) already holding this name, if any."""
        return self._claimed.get((scope, pg_truncate((name or "").lower())))

    def claim(
        self,
        name: str,
        kind: str,
        owner: str,
        residue: list[Residue],
        scope: str = RELATIONS,
        note: bool = True,
    ) -> bool:
        """Claim the name; on a collision, append the refusal instead.

        A name past the 63-byte limit that still claims cleanly gets a
        truncation note, because PostgreSQL will shorten it the same
        way everywhere it is referenced.
        """
        key = (scope, pg_truncate((name or "").lower()))
        prior = self._claimed.get(key)
        if prior is not None:
            prior_name, prior_kind = prior
            if (name or "").lower() == (prior_name or "").lower():
                reason = (
                    f"name collides with {prior_kind} {prior_name}: Oracle"
                    " keeps them in separate namespaces, PostgreSQL does"
                    " not - rename before migration"
                )
            else:
                reason = (
                    f"name collides with {prior_kind} {prior_name} within"
                    " PostgreSQL's 63-byte identifier limit; rename before"
                    " migration"
                )
            residue.append(Residue(owner, name, kind, reason))
            return False
        self._claimed[key] = (name, kind)
        if note and over_limit(name or ""):
            residue.append(
                Residue(
                    owner,
                    name,
                    "note",
                    "name exceeds PostgreSQL's 63-byte identifier limit"
                    " and will be truncated on apply",
                )
            )
        return True
