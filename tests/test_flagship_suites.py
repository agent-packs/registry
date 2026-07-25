import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packs"
SUPERPOWERS_RELEASE = "6.1.1"
SUPERPOWERS_COMMIT = "d884ae04edebef577e82ff7c4e143debd0bbec99"


def load_pack(pack_id):
    return json.loads((PACKS / f"{pack_id}.json").read_text(encoding="utf-8"))


class FlagshipSuiteTest(unittest.TestCase):
    def test_engineering_leader_is_a_stable_evidence_backed_role_suite(self):
        pack = load_pack("eng-leader")

        self.assertEqual(pack["stability"], "stable")
        self.assertEqual(pack["reviewStatus"], "verified")
        self.assertEqual(pack["trust"], "verified")
        self.assertEqual(pack["recommendation"]["path"], "role")
        self.assertEqual(pack["compatibility"]["codex"]["status"], "verified")
        self.assertEqual(pack["compatibility"]["claude-code"]["status"], "verified")

        skill_ids = {
            ref if isinstance(ref, str) else ref["id"]
            for ref in pack["skills"]
        }
        self.assertIn("engineering-leadership-operating-system", skill_ids)

        capability_names = {capability["name"] for capability in pack["capabilities"]}
        for required in (
            "Engineering talent and succession review",
            "Technical debt and modernization portfolio review",
            "Engineering cost and vendor review",
            "Engineering change communication plan",
        ):
            with self.subTest(required=required):
                self.assertIn(required, capability_names)

    def test_superpowers_suite_tracks_the_complete_immutable_release(self):
        suite = load_pack("superpowers")

        self.assertEqual(suite["version"], "0.2.0")
        self.assertEqual(suite["stability"], "stable")
        self.assertEqual(suite["reviewStatus"], "verified")
        self.assertEqual(suite["trust"], "community")
        self.assertEqual(suite["recommendation"]["path"], "workflow")

        expected_skills = {
            "superpowers-using-superpowers",
            "superpowers-brainstorming",
            "superpowers-using-git-worktrees",
            "superpowers-writing-plans",
            "superpowers-executing-plans",
            "superpowers-subagent-driven-development",
            "superpowers-test-driven-development",
            "superpowers-systematic-debugging",
            "superpowers-verification-before-completion",
            "superpowers-dispatching-parallel-agents",
            "superpowers-requesting-code-review",
            "superpowers-receiving-code-review",
            "superpowers-finishing-a-development-branch",
            "superpowers-writing-skills",
        }
        actual_skills = set()
        for child_id in suite["packs"]:
            child = load_pack(child_id)
            for ref in child.get("skills", []):
                self.assertIsInstance(ref, dict)
                self.assertEqual(ref["version"], SUPERPOWERS_RELEASE)
                self.assertIn(SUPERPOWERS_COMMIT, ref["source"])
                actual_skills.add(ref["id"])
        self.assertEqual(actual_skills, expected_skills)

    def test_superpowers_distribution_covers_documented_agents(self):
        pack = load_pack("superpowers-distribution-plugins")

        self.assertEqual(pack["version"], "0.2.0")
        self.assertEqual(pack["trust"], "community")
        self.assertIn("codex", pack["compatibility"])
        self.assertIn("claude-code", pack["compatibility"])
        self.assertIn("cursor", pack["compatibility"])
        self.assertIn("gemini", pack["compatibility"])
        self.assertIn("opencode", pack["compatibility"])
        self.assertIn("copilot", pack["tools"])

        for ref in pack["plugins"]:
            self.assertEqual(ref["version"], SUPERPOWERS_RELEASE)
            self.assertIn(SUPERPOWERS_COMMIT, ref["source"])

    def test_registry_ci_runs_the_cli_contract(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        for required in (
            "repository: agent-packs/cli",
            "go build",
            "validate packs",
            "lint --all",
            "verify --all",
            "publish --check",
            "index --check",
            "install eng-leader",
            "install superpowers",
        ):
            with self.subTest(required=required):
                self.assertIn(required, workflow)


if __name__ == "__main__":
    unittest.main()
