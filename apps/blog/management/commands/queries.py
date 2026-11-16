from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Model, QuerySet
from django.test.utils import CaptureQueriesContext

from apps.blog.queries import QUERIES

CHANGING_QUERIES = frozenset(range(40, 45))
PREVIEW_ROWS = 5
INDENT = "  "

QUERY_ARGUMENTS: dict[int, dict[str, Any]] = {}


class Command(BaseCommand):
    help = "Run the homework queries."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--number", type=int, help="Run one query by its number")
        parser.add_argument("--sql", action="store_true", help="Show the SQL")

    def handle(self, *args: Any, **options: Any) -> None:
        number: int | None = options["number"]
        show_sql: bool = options["sql"]

        # no number = run everything except the ones that change data
        if number is None:
            numbers = [n for n in QUERIES if n not in CHANGING_QUERIES]
        elif number in QUERIES:
            numbers = [number]
        else:
            raise CommandError(f"No query #{number}. Use 1-{max(QUERIES)}.")

        for index, query_number in enumerate(numbers):
            # empty line between queries
            if index:
                self.stdout.write("")
            self._run(query_number, show_sql)

    def _run(self, number: int, show_sql: bool) -> None:
        function = QUERIES[number]
        arguments = QUERY_ARGUMENTS.get(number, {})

        with CaptureQueriesContext(connection) as context:
            result = function(**arguments)
            # querysets are lazy, so run it here or we count 0 queries
            rows = list(result) if isinstance(result, QuerySet) else None

        sql_count = len(context.captured_queries)
        word = "query" if sql_count == 1 else "queries"
        self.stdout.write(
            self.style.SUCCESS(f"#{number} {function.__name__} — {sql_count} SQL {word}")
        )
        if show_sql:
            for captured in context.captured_queries:
                self.stdout.write(self.style.SQL_KEYWORD(captured["sql"]))

        if rows is not None:
            self._write_rows(rows)
        elif isinstance(result, list):
            self._write_rows(result)
        elif isinstance(result, dict):
            self._write_rows([f"{key}: {value}" for key, value in result.items()])
        else:
            self.stdout.write(f"{INDENT}{self._format_row(result)}")

    def _write_rows(self, rows: list[Any]) -> None:

        for row in rows[:PREVIEW_ROWS]:
            self.stdout.write(f"{INDENT}{self._format_row(row)}")
        self.stdout.write(f"{INDENT}({len(rows)} {'row' if len(rows) == 1 else 'rows'})")

    def _format_row(self, row: Any) -> str:

        if isinstance(row, (Model, str)):
            return str(row)
        return repr(row)
