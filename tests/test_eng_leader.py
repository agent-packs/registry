import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "packs" / "eng-leader.json"
LEADERSHIP_REVIEW_PATH = (
    ROOT
    / "plugins"
    / "eng-leader-workflows"
    / ".claude-plugin"
    / "skills"
    / "leadership-review"
    / "SKILL.md"
)
DECISIVE_SKILL_PATH = ROOT / "skills" / "decisive-decision-making" / "SKILL.md"


def load_pack():
    with PACK_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def capability_by_name(pack, name):
    return next(
        capability
        for capability in pack["capabilities"]
        if capability["name"] == name
    )


class EngineeringLeaderPackTest(unittest.TestCase):
    def setUp(self):
        self.pack = load_pack()

    def test_includes_portfolio_ai_adoption_and_decision_governance_workflows(self):
        capability_names = {
            capability["name"] for capability in self.pack["capabilities"]
        }

        self.assertIn("Engineering portfolio and capacity review", capability_names)
        self.assertIn("AI-assisted engineering adoption review", capability_names)
        self.assertIn("Engineering decision and risk register", capability_names)

    def test_includes_dedicated_decisive_skill(self):
        skill_ids = {
            skill if isinstance(skill, str) else skill["id"]
            for skill in self.pack["skills"]
        }
        self.assertIn("decisive-decision-making", skill_ids)

        skill = DECISIVE_SKILL_PATH.read_text(encoding="utf-8").lower()
        for step in (
            "widen your options",
            "reality-test your assumptions",
            "attain distance before deciding",
            "prepare to be wrong",
        ):
            with self.subTest(step=step):
                self.assertIn(step, skill)

    def test_monthly_retro_preserves_the_five_part_format(self):
        prompt = capability_by_name(
            self.pack, "Monthly engineering retrospective"
        )["content"].lower()

        expected_sections = (
            "appreciations",
            "what did we do well",
            "what can we improve by 10%",
            "people, product, and process",
            "action items",
            "follow-ups from the previous retrospective",
        )
        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, prompt)

        template = capability_by_name(
            self.pack, "Monthly engineering retrospective template"
        )["content"].lower()
        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, template)

    def test_dora_review_uses_current_five_metric_model(self):
        content = capability_by_name(
            self.pack, "DORA metrics leadership review"
        )["content"].lower()

        for metric in (
            "change lead time",
            "deployment frequency",
            "failed deployment recovery time",
            "change fail rate",
            "deployment rework rate",
        ):
            with self.subTest(metric=metric):
                self.assertIn(metric, content)

    def test_leadership_review_requires_evidence_decisions_and_follow_through(self):
        workflow = LEADERSHIP_REVIEW_PATH.read_text(encoding="utf-8").lower()

        for section in (
            "evidence and confidence",
            "decision log",
            "follow-through",
        ):
            with self.subTest(section=section):
                self.assertIn(section, workflow)


if __name__ == "__main__":
    unittest.main()
