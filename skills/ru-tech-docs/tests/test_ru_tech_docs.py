from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ru_tech_docs.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class RuTechDocsCliTests(unittest.TestCase):
    def test_lint_flags_latin_prose_but_ignores_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "Новый full backup готов. Запустите `RESTORE VERIFYONLY`.\n\n"
                "```powershell\n"
                "Move-MssqlFullSetsToCold.ps1 -Apply\n"
                "```\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        flagged = {(item["rule"], item["token"]) for item in findings}
        self.assertIn(("RTD001", "full"), flagged)
        self.assertIn(("RTD001", "backup"), flagged)
        self.assertNotIn(("RTD001", "RESTORE"), flagged)
        self.assertNotIn(("RTD001", "Move-MssqlFullSetsToCold"), flagged)

    def test_lint_ignores_yaml_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "---\n"
                "title: OMP skill ru-tech-docs\n"
                "tags:\n"
                "  - documentation\n"
                "---\n"
                "Документ проверен.\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_lint_ignores_obsidian_wikilinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "См. [[OMP — встроенные инструменты и плагины]].\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_lint_uses_glossary_for_protected_and_forbidden_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            glossary = Path(tmp) / "glossary.json"
            document.write_text(
                "MSSQL full backup готов для базы в состоянии ONLINE.\n",
                encoding="utf-8",
            )
            glossary.write_text(
                json.dumps(
                    {
                        "do_not_translate": ["MSSQL", "ONLINE"],
                        "terms": [
                            {
                                "preferred": "полная резервная копия",
                                "forbidden": ["full backup"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = run_cli(
                "lint",
                str(document),
                "--glossary",
                str(glossary),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        self.assertEqual(
            [
                {
                    "rule": item["rule"],
                    "token": item["token"],
                    "suggestion": item.get("suggestion"),
                }
                for item in findings
            ],
            [
                {
                    "rule": "RTD002",
                    "token": "full backup",
                    "suggestion": "полная резервная копия",
                }
            ],
        )

    def test_runbook_profile_has_stricter_sentence_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "Перед публикацией система повторно проверяет исходный каталог "
                "и промежуточную копию, сравнивает имена файлов, размеры и "
                "контрольные суммы, а затем удаляет только подтверждённый "
                "исходный каталог.\n",
                encoding="utf-8",
            )

            docs_result = run_cli(
                "lint", str(document), "--profile", "docs", "--format", "json"
            )
            runbook_result = run_cli(
                "lint", str(document), "--profile", "runbook", "--format", "json"
            )

        self.assertEqual(docs_result.returncode, 0, docs_result.stderr)
        self.assertEqual(json.loads(docs_result.stdout)["findings"], [])
        self.assertEqual(runbook_result.returncode, 1, runbook_result.stderr)
        self.assertEqual(
            [item["rule"] for item in json.loads(runbook_result.stdout)["findings"]],
            ["RTD003"],
        )

    def test_sentence_limit_counts_markdown_soft_wrapped_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                " ".join(["проверка"] * 12)
                + "\n"
                + " ".join(["каталога"] * 12)
                + ".\n",
                encoding="utf-8",
            )

            result = run_cli(
                "lint", str(document), "--profile", "runbook", "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        self.assertEqual([item["rule"] for item in findings], ["RTD003"])
        self.assertEqual(findings[0]["line"], 1)

    def test_sentence_limit_counts_soft_wrapped_blockquote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "> " + " ".join(["проверка"] * 12) + "\n"
                "> " + " ".join(["каталога"] * 12) + ".\n",
                encoding="utf-8",
            )

            result = run_cli(
                "lint", str(document), "--profile", "runbook", "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(
            [item["rule"] for item in json.loads(result.stdout)["findings"]],
            ["RTD003"],
        )

    def test_sentence_finding_column_includes_blockquote_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "> " + " ".join(["проверка"] * 21) + ".\n",
                encoding="utf-8",
            )

            result = run_cli(
                "lint", str(document), "--profile", "runbook", "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        finding = json.loads(result.stdout)["findings"][0]
        self.assertEqual(finding["rule"], "RTD003")
        self.assertEqual(finding["column"], 3)

    def test_sentence_limit_counts_lazy_blockquote_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "> " + " ".join(["проверка"] * 12) + "\n"
                + " ".join(["каталога"] * 12) + ".\n",
                encoding="utf-8",
            )

            result = run_cli(
                "lint", str(document), "--profile", "runbook", "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(
            [item["rule"] for item in json.loads(result.stdout)["findings"]],
            ["RTD003"],
        )

    def test_sentence_position_on_lazy_continuation_maps_to_source_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "> Коротко.\n" + " ".join(["проверка"] * 21) + ".\n",
                encoding="utf-8",
            )

            result = run_cli(
                "lint", str(document), "--profile", "runbook", "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        finding = json.loads(result.stdout)["findings"][0]
        self.assertEqual((finding["line"], finding["column"]), (2, 1))

    def test_sentence_limit_ignores_dots_inside_versions_and_decimals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            glossary = Path(tmp) / "glossary.json"
            document.write_text(
                "Система версии v1.2.3 обрабатывает порог 1.5 часа и "
                + " ".join(["проверяет"] * 16)
                + ".\n",
                encoding="utf-8",
            )
            glossary.write_text(
                json.dumps({"do_not_translate": ["v1.2.3"], "terms": []}),
                encoding="utf-8",
            )

            result = run_cli(
                "lint",
                str(document),
                "--profile",
                "runbook",
                "--glossary",
                str(glossary),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        rules = [item["rule"] for item in json.loads(result.stdout)["findings"]]
        self.assertIn("RTD003", rules)

    def test_guard_allows_prose_changes_when_invariants_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            glossary = Path(tmp) / "glossary.json"
            before.write_text(
                "Система создаёт `validation.ok.json` после 24 часов для MSSQL.\n",
                encoding="utf-8",
            )
            after.write_text(
                "После 24 часов MSSQL создаёт маркер `validation.ok.json`.\n",
                encoding="utf-8",
            )
            glossary.write_text(
                json.dumps({"do_not_translate": ["MSSQL"], "terms": []}),
                encoding="utf-8",
            )

            result = run_cli(
                "guard",
                str(before),
                str(after),
                "--glossary",
                str(glossary),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True, "changes": []})

    def test_guard_allows_translation_of_prose_units(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "Маркер должен быть не моложе 24 hours.\n", encoding="utf-8"
            )
            after.write_text(
                "Маркер должен быть не моложе 24 часов.\n", encoding="utf-8"
            )

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True, "changes": []})

    def test_guard_compares_structured_numeric_expressions(self) -> None:
        cases = [
            ("Порог < 10.\n", "Порог <= 10.\n", 1),
            ("Смещение -5 секунд.\n", "Смещение 5 секунд.\n", 1),
            ("Формат v2.\n", "Формат v3.\n", 1),
            ("Размер 10 MB.\n", "Размер 10 Mb.\n", 1),
            ("Интервал 10 ms.\n", "Интервал 10 Hz.\n", 1),
            ("Нужны две копии.\n", "Нужны три копии.\n", 1),
            ("Возраст 24 h.\n", "Возраст 24 ч.\n", 0),
            ("Возраст 1.5 hours.\n", "Возраст 1,5 часа.\n", 0),
        ]
        for before_text, after_text, expected_code in cases:
            with (
                self.subTest(before=before_text, after=after_text),
                tempfile.TemporaryDirectory() as tmp,
            ):
                before = Path(tmp) / "before.md"
                after = Path(tmp) / "after.md"
                before.write_text(before_text, encoding="utf-8")
                after.write_text(after_text, encoding="utf-8")

                result = run_cli(
                    "guard", str(before), str(after), "--format", "json"
                )

                self.assertEqual(result.returncode, expected_code, result.stdout)

    def test_guard_handles_soft_wrap_unicode_and_inflected_numeric_invariants(self) -> None:
        cases = [
            (
                "Не менее\n10 часов и не более\n20 часов.\n",
                "Не менее\n20 часов и не более\n10 часов.\n",
            ),
            ("Порог >=\u00a010.\n", "Порог 10.\n"),
            ("Нужно двух копий.\n", "Нужно трёх копий.\n"),
            ("Процесс выбирает одну базу.\n", "Процесс выбирает базы.\n"),
            ("Смещение −5 секунд.\n", "Смещение 5 секунд.\n"),
            ("Код ≠ 10.\n", "Код 10.\n"),
            ("Размер 10 B.\n", "Размер 10 b.\n"),
        ]
        for before_text, after_text in cases:
            with (
                self.subTest(before=before_text, after=after_text),
                tempfile.TemporaryDirectory() as tmp,
            ):
                before = Path(tmp) / "before.md"
                after = Path(tmp) / "after.md"
                before.write_text(before_text, encoding="utf-8")
                after.write_text(after_text, encoding="utf-8")

                result = run_cli(
                    "guard", str(before), str(after), "--format", "json"
                )

                self.assertEqual(result.returncode, 1, result.stdout)

    def test_guard_allows_translation_of_unit_abbreviations(self) -> None:
        cases = [("24 h", "24 ч"), ("10 min", "10 мин"), ("10 GB", "10 ГБ")]
        for before_value, after_value in cases:
            with self.subTest(before=before_value), tempfile.TemporaryDirectory() as tmp:
                before = Path(tmp) / "before.md"
                after = Path(tmp) / "after.md"
                before.write_text(
                    f"Значение должно быть {before_value}.\n", encoding="utf-8"
                )
                after.write_text(
                    f"Значение должно быть {after_value}.\n", encoding="utf-8"
                )

                result = run_cli(
                    "guard", str(before), str(after), "--format", "json"
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads(result.stdout), {"ok": True, "changes": []}
                )

    def test_guard_rejects_changed_code_numbers_and_protected_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            glossary = Path(tmp) / "glossary.json"
            before.write_text(
                "MSSQL запускает `Move.ps1 -MinimumAgeHours 24`.\n",
                encoding="utf-8",
            )
            after.write_text(
                "PostgreSQL запускает `Move.ps1 -MinimumAgeHours 12`.\n",
                encoding="utf-8",
            )
            glossary.write_text(
                json.dumps({"do_not_translate": ["MSSQL"], "terms": []}),
                encoding="utf-8",
            )

            result = run_cli(
                "guard",
                str(before),
                str(after),
                "--glossary",
                str(glossary),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(
            [change["kind"] for change in payload["changes"]],
            ["number", "numeric_expression", "protected_term"],
        )

    def test_guard_rejects_changed_fences_links_and_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "```powershell\nMove.ps1 -Apply\n```\n"
                "[Описание](docs/old.md)\n"
                "См. https://example.com/api\n",
                encoding="utf-8",
            )
            after.write_text(
                "```powershell\nMove.ps1\n```\n"
                "[Описание](docs/new.md)\n"
                "См. https://example.com/service\n",
                encoding="utf-8",
            )

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [change["kind"] for change in payload["changes"]],
            ["fenced_code", "link_target", "url"],
        )

    def test_guard_rejects_changed_requirement_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "Источник удаляется только после проверки. "
                "Набор не публикуется без маркера.\n",
                encoding="utf-8",
            )
            after.write_text(
                "Источник удаляется после проверки. "
                "Набор публикуется без маркера.\n",
                encoding="utf-8",
            )

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [change["kind"] for change in payload["changes"]],
            ["requirement_marker"],
        )

    def test_guard_rejects_changed_paths_keys_versions_bounds_units_and_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "Для sourceId в /etc/old.conf версии v1.2.3 требуется "
                "не менее 10 часов и не более 20 часов; нужна одна копия.\n",
                encoding="utf-8",
            )
            after.write_text(
                "Для targetId в /srv/new.yaml версии v9.2.3 требуется "
                "не менее 20 дней и не более 10 дней; нужны две копии.\n",
                encoding="utf-8",
            )

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertTrue(
            {"count_word", "identifier", "measurement", "path", "version"}
            <= kinds,
            kinds,
        )

    def test_guard_allows_reordering_independent_protected_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            first = "Настройка /etc/first.conf использует v1.2.3.\n"
            second = "Настройка /etc/second.conf использует v2.3.4.\n"
            before.write_text(first + "\n" + second, encoding="utf-8")
            after.write_text(second + "\n" + first, encoding="utf-8")

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout), {"ok": True, "changes": []})

    def test_guard_rejects_plain_filename_and_dotted_key_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "Описание находится в README.md; параметр restore.timeout задан.\n",
                encoding="utf-8",
            )
            after.write_text(
                "Описание находится в INSTALL.md; параметр restore.retries задан.\n",
                encoding="utf-8",
            )

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("filename_or_dotted_key", kinds)

    def test_guard_rejects_terminal_dotfile_and_numeric_extension_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "Откройте README.md. Ключ restore.timeout. Файлы .env.local и archive.7z.\n",
                encoding="utf-8",
            )
            after.write_text(
                "Откройте INSTALL.md. Ключ restore.retries. Файлы .env.production и archive.8z.\n",
                encoding="utf-8",
            )

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        changes = {
            change["kind"]: change
            for change in json.loads(result.stdout)["changes"]
        }
        self.assertIn("filename_or_dotted_key", changes)
        self.assertIn("README.md", changes["filename_or_dotted_key"]["before"])
        self.assertIn(".env.local", changes["filename_or_dotted_key"]["before"])
        self.assertIn("archive.7z", changes["filename_or_dotted_key"]["before"])

    def test_guard_rejects_changed_numeric_signs_and_operators(self) -> None:
        cases = [
            ("Задержка должна быть -5 секунд.\n", "Задержка должна быть 5 секунд.\n"),
            ("Значение должно быть < 10.\n", "Значение должно быть <= 10.\n"),
        ]
        for before_text, after_text in cases:
            with self.subTest(before=before_text), tempfile.TemporaryDirectory() as tmp:
                before = Path(tmp) / "before.md"
                after = Path(tmp) / "after.md"
                before.write_text(before_text, encoding="utf-8")
                after.write_text(after_text, encoding="utf-8")

                result = run_cli(
                    "guard", str(before), str(after), "--format", "json"
                )

                self.assertEqual(result.returncode, 1, result.stderr)
                kinds = {
                    change["kind"]
                    for change in json.loads(result.stdout)["changes"]
                }
                self.assertIn("numeric_expression", kinds)

    def test_guard_distinguishes_storage_bits_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text("Размер должен быть 10 MB.\n", encoding="utf-8")
            after.write_text("Размер должен быть 10 Mb.\n", encoding="utf-8")

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("numeric_expression", kinds)

    def test_guard_rejects_changed_short_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text("Используйте схему v2.\n", encoding="utf-8")
            after.write_text("Используйте схему v3.\n", encoding="utf-8")

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("version", kinds)

    def test_guard_allows_prose_pairs_and_inline_technical_token_formatting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "Сопоставьте age/retention, source/destination, manifest/stage, "
                "validator/scheduled-task, Export/review и /эквивалент для schema-v2.\n",
                encoding="utf-8",
            )
            after.write_text(
                "Сопоставьте возраст и срок хранения, источник и назначение, "
                "манифест и этап, валидатор и планировщик, экспорт и review, "
                "а также эквивалент для `schema-v2`.\n",
                encoding="utf-8",
            )

            result = run_cli("guard", str(before), str(after), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout), {"ok": True, "changes": []})

    def test_guard_rejects_changed_composite_identifier_without_version_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text("Используйте schema-v2.\n", encoding="utf-8")
            after.write_text("Используйте `schema-v3`.\n", encoding="utf-8")

            result = run_cli("guard", str(before), str(after), "--format", "json")

        self.assertEqual(result.returncode, 1, result.stdout)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("identifier", kinds)
        self.assertNotIn("version", kinds)

    def test_guard_rejects_changed_unambiguous_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                r"C:\backups\Full \\server\share\file.bak /var/lib/backups "
                r"./tests/file.ps1 tests/FullSetLifecycle.Tests.ps1" + "\n",
                encoding="utf-8",
            )
            after.write_text(
                r"C:\backups\Differential \\server\share\file.trn /var/lib/archive "
                r"./tests/other.ps1 tests/IncrementalLifecycle.Tests.ps1" + "\n",
                encoding="utf-8",
            )

            result = run_cli("guard", str(before), str(after), "--format", "json")

        self.assertEqual(result.returncode, 1, result.stdout)
        changes = {
            change["kind"]: change
            for change in json.loads(result.stdout)["changes"]
        }
        self.assertIn("path", changes)
        self.assertEqual(
            changes["path"]["before"],
            [
                r"C:\backups\Full",
                r"\\server\share\file.bak",
                "/var/lib/backups",
                "./tests/file.ps1",
                "tests/FullSetLifecycle.Tests.ps1",
            ],
        )

    def test_guard_preserves_before_glossary_protected_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            removed = Path(tmp) / "removed.md"
            before_glossary = Path(tmp) / "glossary.before.json"
            after_glossary = Path(tmp) / "glossary.after.json"
            before.write_text("MSSQL использует schema-v2.\n", encoding="utf-8")
            after.write_text("MSSQL использует `schema-v2`.\n", encoding="utf-8")
            removed.write_text("PostgreSQL использует `schema-v2`.\n", encoding="utf-8")
            before_glossary.write_text(
                json.dumps({"do_not_translate": ["MSSQL"], "terms": []}),
                encoding="utf-8",
            )
            after_glossary.write_text(
                json.dumps(
                    {"do_not_translate": ["MSSQL", "schema-v2"], "terms": []}
                ),
                encoding="utf-8",
            )

            unchanged = run_cli(
                "guard",
                str(before),
                str(after),
                "--before-glossary",
                str(before_glossary),
                "--glossary",
                str(after_glossary),
                "--format",
                "json",
            )
            deleted = run_cli(
                "guard",
                str(before),
                str(removed),
                "--before-glossary",
                str(before_glossary),
                "--glossary",
                str(after_glossary),
                "--format",
                "json",
            )

        self.assertEqual(unchanged.returncode, 0, unchanged.stdout)
        self.assertEqual(json.loads(unchanged.stdout), {"ok": True, "changes": []})
        self.assertEqual(deleted.returncode, 1, deleted.stdout)
        kinds = {change["kind"] for change in json.loads(deleted.stdout)["changes"]}
        self.assertIn("protected_term", kinds)

    def test_guard_detects_structured_command_changed_while_adding_backticks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text("Запустите Move.ps1 -Apply.\n", encoding="utf-8")
            after.write_text("Запустите `Move.ps1 -WhatIf`.\n", encoding="utf-8")

            result = run_cli("guard", str(before), str(after), "--format", "json")

        self.assertEqual(result.returncode, 1, result.stdout)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("identifier", kinds)

    def test_invalid_glossary_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            glossary = Path(tmp) / "glossary.json"
            document.write_text("Полная резервная копия готова.\n", encoding="utf-8")
            glossary.write_text(
                json.dumps({"terms": [{"forbidden": ["full backup"]}]}),
                encoding="utf-8",
            )

            result = run_cli(
                "lint", str(document), "--glossary", str(glossary)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Ошибка глоссария", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_glossary_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            glossary = Path(tmp) / "glossary.json"
            document.write_text("Проверка завершена.\n", encoding="utf-8")
            glossary.write_bytes(b"{\xff}")

            result = run_cli(
                "lint", str(document), "--glossary", str(glossary)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Ошибка глоссария", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_document_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid.md"
            valid = Path(tmp) / "valid.md"
            invalid.write_bytes(b"\xff")
            valid.write_text("Проверка завершена.\n", encoding="utf-8")

            results = [
                run_cli("lint", str(invalid)),
                run_cli("guard", str(invalid), str(valid)),
            ]

        for result in results:
            with self.subTest(args=result.args):
                self.assertEqual(result.returncode, 2)
                self.assertIn("Ошибка документа", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_conflicting_glossary_fails_cleanly(self) -> None:
        conflicts = [
            {
                "do_not_translate": ["full backup"],
                "terms": [
                    {
                        "preferred": "полная резервная копия",
                        "forbidden": ["full backup"],
                    }
                ],
            },
            {
                "terms": [
                    {
                        "preferred": "полная резервная копия",
                        "forbidden": ["full backup"],
                    },
                    {
                        "preferred": "полный бэкап",
                        "forbidden": ["full backup"],
                    },
                ]
            },
            {
                "terms": [
                    {
                        "preferred": "холодное хранилище",
                        "forbidden": ["cold storage"],
                    },
                    {
                        "preferred": "cold storage",
                        "forbidden": ["cold archive"],
                    },
                ]
            },
        ]
        for conflict in conflicts:
            with self.subTest(conflict=conflict), tempfile.TemporaryDirectory() as tmp:
                document = Path(tmp) / "sample.md"
                glossary = Path(tmp) / "glossary.json"
                document.write_text("Новый full backup готов.\n", encoding="utf-8")
                glossary.write_text(
                    json.dumps(conflict, ensure_ascii=False), encoding="utf-8"
                )

                result = run_cli(
                    "lint", str(document), "--glossary", str(glossary)
                )

                self.assertEqual(result.returncode, 2)
                self.assertIn("Ошибка глоссария", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_multiword_protected_term_is_not_flagged_as_latin_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            glossary = Path(tmp) / "glossary.json"
            document.write_text(
                "Команда RESTORE VERIFYONLY проверяет файл.\n",
                encoding="utf-8",
            )
            glossary.write_text(
                json.dumps(
                    {"do_not_translate": ["RESTORE VERIFYONLY"], "terms": []}
                ),
                encoding="utf-8",
            )

            result = run_cli(
                "lint",
                str(document),
                "--glossary",
                str(glossary),
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_lint_ignores_link_targets_and_bare_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "См. [документацию](https://example.com/api) и "
                "https://status.example.com.\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_lint_ignores_multi_backtick_code_spans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "Запустите ``RESTORE ` VERIFYONLY`` для проверки.\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_multiline_code_span_is_ignored_and_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "Запустите `GET\n/api` сейчас.\n", encoding="utf-8"
            )
            after.write_text(
                "Запустите `POST\n/api` сейчас.\n", encoding="utf-8"
            )

            lint_result = run_cli("lint", str(before), "--format", "json")
            guard_result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(lint_result.returncode, 0, lint_result.stdout)
        self.assertEqual(json.loads(lint_result.stdout)["findings"], [])
        self.assertEqual(guard_result.returncode, 1, guard_result.stdout)
        kinds = {change["kind"] for change in json.loads(guard_result.stdout)["changes"]}
        self.assertIn("inline_code", kinds)

    def test_backticks_do_not_span_blank_markdown_paragraphs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "Начало `open\n\nfull backup` завершение.\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 1, result.stdout)
        tokens = {item["token"] for item in json.loads(result.stdout)["findings"]}
        self.assertIn("full", tokens)
        self.assertIn("backup", tokens)

    def test_backticks_do_not_span_empty_blockquote_paragraphs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "Начало `open\n>\nfull backup` завершение.\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 1, result.stdout)
        tokens = {item["token"] for item in json.loads(result.stdout)["findings"]}
        self.assertIn("full", tokens)
        self.assertIn("backup", tokens)

    def test_indented_code_block_is_ignored_and_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text("    GET /api\n\nПроверка завершена.\n", encoding="utf-8")
            after.write_text("    POST /api\n\nПроверка завершена.\n", encoding="utf-8")

            lint_result = run_cli("lint", str(before), "--format", "json")
            guard_result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(lint_result.returncode, 0, lint_result.stdout)
        self.assertEqual(json.loads(lint_result.stdout)["findings"], [])
        self.assertEqual(guard_result.returncode, 1, guard_result.stdout)
        kinds = {change["kind"] for change in json.loads(guard_result.stdout)["changes"]}
        self.assertIn("indented_code", kinds)

    def test_nested_list_continuation_is_not_treated_as_indented_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "- Русский пункт\n"
                "\n"
                "    продолжает full backup описание.\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 1, result.stdout)
        tokens = {item["token"] for item in json.loads(result.stdout)["findings"]}
        self.assertIn("full", tokens)
        self.assertIn("backup", tokens)

    def test_list_contained_and_post_list_blockquote_code_are_guarded(self) -> None:
        cases = [
            ("- Пункт\n\n      GET /api\n", "- Пункт\n\n      POST /api\n"),
            ("- Пункт\n\n>     GET /api\n", "- Пункт\n\n>     POST /api\n"),
        ]
        for before_text, after_text in cases:
            with (
                self.subTest(before=before_text),
                tempfile.TemporaryDirectory() as tmp,
            ):
                before = Path(tmp) / "before.md"
                after = Path(tmp) / "after.md"
                before.write_text(before_text, encoding="utf-8")
                after.write_text(after_text, encoding="utf-8")

                lint_result = run_cli("lint", str(before), "--format", "json")
                guard_result = run_cli(
                    "guard", str(before), str(after), "--format", "json"
                )

                self.assertEqual(lint_result.returncode, 0, lint_result.stdout)
                self.assertEqual(guard_result.returncode, 1, guard_result.stdout)
                kinds = {
                    change["kind"]
                    for change in json.loads(guard_result.stdout)["changes"]
                }
                self.assertIn("indented_code", kinds)

    def test_blockquote_indented_code_is_ignored_and_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(">\n>     GET /api\n", encoding="utf-8")
            after.write_text(">\n>     POST /api\n", encoding="utf-8")

            lint_result = run_cli("lint", str(before), "--format", "json")
            guard_result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(lint_result.returncode, 0, lint_result.stdout)
        self.assertEqual(json.loads(lint_result.stdout)["findings"], [])
        self.assertEqual(guard_result.returncode, 1, guard_result.stdout)
        kinds = {change["kind"] for change in json.loads(guard_result.stdout)["changes"]}
        self.assertIn("indented_code", kinds)

    def test_lint_does_not_close_fence_with_trailing_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "~~~powershell\n"
                "Move-First.ps1\n"
                "~~~not-a-close\n"
                "Move-Second.ps1\n"
                "~~~\n"
                "Проверка завершена.\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_guard_rejects_code_change_with_longer_closing_fence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text("```text\nsourceId\n````\n", encoding="utf-8")
            after.write_text("```text\ntargetId\n````\n", encoding="utf-8")

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(
            [change["kind"] for change in json.loads(result.stdout)["changes"]],
            ["fenced_code"],
        )

    def test_lint_ignores_balanced_and_reference_link_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "sample.md"
            document.write_text(
                "См. [описание](docs/api(v2).md) и [справочник][ref].\n\n"
                "[ref]: <docs/reference(v2).md>\n",
                encoding="utf-8",
            )

            result = run_cli("lint", str(document), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_guard_rejects_balanced_and_reference_link_target_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            before.write_text(
                "[описание](docs/api(v2).md)\n[ref]: <docs/reference(v2).md>\n",
                encoding="utf-8",
            )
            after.write_text(
                "[описание](docs/api(v3).md)\n[ref]: <docs/reference(v3).md>\n",
                encoding="utf-8",
            )

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stderr)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("link_target", kinds)

    def test_guard_rejects_reference_use_that_resolves_to_another_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            definitions = (
                "\n[ref]: docs/one.md\n"
                "[other]: docs/two.md\n"
            )
            before.write_text("См. [описание][ref].\n" + definitions, encoding="utf-8")
            after.write_text("См. [описание][other].\n" + definitions, encoding="utf-8")

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("reference_target", kinds)

    def test_guard_resolves_shortcut_reference_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.md"
            after = Path(tmp) / "after.md"
            definitions = "\n[ref]: docs/one.md\n[other]: docs/two.md\n"
            before.write_text("См. [ref].\n" + definitions, encoding="utf-8")
            after.write_text("См. [other].\n" + definitions, encoding="utf-8")

            result = run_cli(
                "guard", str(before), str(after), "--format", "json"
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        kinds = {change["kind"] for change in json.loads(result.stdout)["changes"]}
        self.assertIn("reference_target", kinds)


if __name__ == "__main__":
    unittest.main()
