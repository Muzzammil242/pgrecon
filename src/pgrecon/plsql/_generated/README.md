# Generated PL/SQL parser

Machine-generated ANTLR parser for PL/SQL. Do not edit these files;
regenerate them instead.

Provenance:

- Grammar: PlSqlLexer.g4 and PlSqlParser.g4 from
  https://github.com/antlr/grammars-v4 (sql/plsql), commit
  e1c222f3f0e7 (2026-08-08), Apache-2.0, copyright 2009-2011
  Alexandre Porcelli, 2015-2019 Ivan Kochurkin, 2017-2018 Mark Adams.
- Base classes: PlSqlLexerBase.py and PlSqlParserBase.py from the same
  tree (sql/plsql/Python3). One adjustment: the lazy flat imports of
  PlSqlLexer inside PlSqlParserBase's predicate helpers are rewritten
  to the package path, because the upstream file assumes a flat
  sys.path. Reapply that rewrite when regenerating.
- Generator: ANTLR 4.13.2, Python3 target, with the visitor option.

To regenerate:

1. Fetch the four files above from grammars-v4 and note the commit.
2. Run the tree's transformGrammar.py over the .g4 files (rewrites
   the embedded actions from this. to self. for the Python target).
3. java -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor
   PlSqlLexer.g4 PlSqlParser.g4
4. Copy the generated .py files and the two base classes here, update
   the commit hash above, and keep the antlr4-python3-runtime pin in
   pyproject.toml in step with the generator version.

The lint, type, coverage, and ASCII gates all exclude this directory;
the generated code is exercised through pgrecon.plsql's own tests.
