import json
import unittest
from pathlib import Path

from qa.check_execution import check_execution
from qa.graph import load_workflow
from qa.registry import merge
from qa.rules import run_rules

FIXTURES = Path(__file__).parent / "fixtures"
ASSERTIONS = json.loads((Path(__file__).parent.parent / "assertions" / "AmVxMC4LmwWBMhev.json").read_text())


def by_rule(findings):
    out = {}
    for f in findings:
        out.setdefault(f.rule_id, []).append(f)
    return out


class LinterBuggyWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.findings = by_rule(run_rules(load_workflow(FIXTURES / "wf_df01.json")))

    def test_df01_detects_json_after_telegram_through_if(self):
        [f] = self.findings["DF-01"]
        self.assertEqual(f.node, "Append")
        self.assertIn("id", f.detail)
        self.assertIn("monto", f.detail)

    def test_df01_allows_mapped_columns_after_sheets_write(self):
        nodes = [f.node for f in self.findings["DF-01"]]
        self.assertNotIn("Usa salida del append", nodes)

    def test_sd02_null_spread(self):
        self.assertEqual([f.node for f in self.findings["SD-02"]], ["Recuperar"])

    def test_sf02_ignores_error_messages(self):
        [f] = self.findings["SF-02"]
        self.assertIn("Send Success", f.detail)
        self.assertNotIn("Send Error", f.detail)

    def test_tg01_markdown_dynamic(self):
        self.assertEqual([f.node for f in self.findings["TG-01"]], ["Respuesta"])

    def test_sd01_and_vd01(self):
        self.assertEqual([f.node for f in self.findings["SD-01"]], ["Guardar"])
        self.assertEqual(len(self.findings["VD-01"]), 1)

    def test_fingerprints_are_stable(self):
        again = run_rules(load_workflow(FIXTURES / "wf_df01.json"))
        self.assertEqual(
            sorted(f.fingerprint for f in again),
            sorted(f.fingerprint for fs in self.findings.values() for f in fs),
        )


class LinterCleanWorkflow(unittest.TestCase):
    def test_no_findings(self):
        self.assertEqual(run_rules(load_workflow(FIXTURES / "wf_clean.json")), [])


class LinterMitigations(unittest.TestCase):
    def test_guard_before_first_write_covers_chained_writes_and_fallback_covers_tg01(self):
        self.assertEqual(run_rules(load_workflow(FIXTURES / "wf_mitigated.json")), [])


class Forense(unittest.TestCase):
    def run_fixture(self, name):
        execution = json.loads((FIXTURES / name).read_text())
        return by_rule(check_execution(execution, ASSERTIONS))

    def test_sf01_empty_append_441(self):
        found = self.run_fixture("exec_441_empty_append.json")
        [f] = found["SF-01"]
        self.assertEqual(f.node, "Append Gastos")
        self.assertIn("ID", f.detail)

    def test_ag01_agent_gave_up_442(self):
        [f] = self.run_fixture("exec_442_agent_no_data.json")["AG-01"]
        self.assertIn("Consultar Gastos", f.detail)

    def test_ex01_error_execution(self):
        [f] = self.run_fixture("exec_error.json")["EX-01"]
        self.assertEqual(f.node, "Explotar Items")


class Registry(unittest.TestCase):
    def test_dedupe_and_regression(self):
        findings = [f.to_dict() for f in run_rules(load_workflow(FIXTURES / "wf_df01.json"))]
        registry = {}
        new, recurring = merge(registry, findings, "t1")
        self.assertEqual((len(new), len(recurring)), (len(findings), 0))
        registry[findings[0]["fingerprint"]]["status"] = "published"
        new, recurring = merge(registry, findings, "t2")
        self.assertEqual((len(new), len(recurring)), (0, len(findings)))
        self.assertEqual(registry[findings[0]["fingerprint"]]["status"], "regression")
        self.assertEqual(registry[findings[0]["fingerprint"]]["occurrences"], 2)


if __name__ == "__main__":
    unittest.main()
