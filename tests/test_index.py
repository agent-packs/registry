import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "index.json"
PACKS_PATH = ROOT / "packs"


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_index_packs():
    index = load_json(INDEX_PATH)
    return {entry["id"]: entry for entry in index["packs"]}


def load_manifests():
    manifests = {}
    for path in sorted(PACKS_PATH.glob("*.json")):
        manifest = load_json(path)
        manifests[manifest["id"]] = manifest
    return manifests


def agent_packs_binary():
    configured = os.environ.get("AGENT_PACKS_BIN")
    if configured:
        return configured
    sibling = ROOT.parent / "agent-packs" / "bin" / "agent-packs"
    if sibling.exists() and os.access(sibling, os.X_OK):
        return str(sibling)
    return shutil.which("agent-packs")


def manifest_skill_ids(manifest):
    ids = []
    for ref in manifest.get("skills", []) or []:
        ids.append(ref if isinstance(ref, str) else ref.get("id"))
    return ids


class IndexDriftTest(unittest.TestCase):
    """Guards that index.json stays in sync with packs/*.json."""

    @classmethod
    def setUpClass(cls):
        cls.index = load_index_packs()
        cls.manifests = load_manifests()

    def test_index_has_same_pack_ids_as_manifests(self):
        self.assertEqual(
            set(self.index.keys()),
            set(self.manifests.keys()),
            "index.json pack ids are out of sync with packs/*.json; "
            "regenerate with `agent-packs index -output index.json`",
        )

    def test_index_scalar_fields_match_manifests(self):
        for pack_id, manifest in self.manifests.items():
            entry = self.index[pack_id]
            for field in ("version", "description", "reviewStatus", "lastVerified"):
                with self.subTest(pack=pack_id, field=field):
                    self.assertEqual(
                        manifest.get(field),
                        entry.get(field),
                        f"{pack_id}.{field} differs between manifest and index",
                    )

    def test_index_skills_match_manifests(self):
        for pack_id, manifest in self.manifests.items():
            entry = self.index[pack_id]
            expected = manifest_skill_ids(manifest)
            with self.subTest(pack=pack_id):
                if expected:
                    self.assertEqual(
                        entry.get("skills"),
                        expected,
                        f"{pack_id} skills list differs between manifest and index",
                    )
                else:
                    # Packs without direct skill refs (e.g. composed packs)
                    # carry no skills array in the index.
                    self.assertIn(entry.get("skills"), (None, []))

    def test_index_capability_count_matches_manifests(self):
        # The index stores a capability COUNT, not the array. For packs with
        # inline capabilities or direct skill/plugin refs, that count is the
        # number of entries in the manifest. Composed packs (which use the
        # `packs` field) derive their count from recursive expansion that the
        # CLI performs, so they are covered by the full-regeneration guard
        # below rather than a direct count comparison here.
        for pack_id, manifest in self.manifests.items():
            if "packs" in manifest:
                continue
            entry = self.index[pack_id]
            if "capabilities" in manifest:
                expected = len(manifest["capabilities"])
            else:
                expected = len(manifest.get("skills", []) or []) + len(
                    manifest.get("plugins", []) or []
                )
            with self.subTest(pack=pack_id):
                self.assertEqual(
                    entry.get("capabilities"),
                    expected,
                    f"{pack_id} capability count differs between manifest and index",
                )

    def test_committed_index_matches_freshly_generated(self):
        binary = agent_packs_binary()
        if binary is None:
            self.skipTest("agent-packs binary not on PATH")

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "index.json"
            env = dict(os.environ, AGENT_PACKS_REGISTRY=str(PACKS_PATH))
            result = subprocess.run(
                [binary, "index", "-output", str(out_path)],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"agent-packs index failed: {result.stderr}",
            )
            generated = load_json(out_path)

        committed = load_json(INDEX_PATH)
        # generatedAt is a timestamp and is expected to differ.
        generated.pop("generatedAt", None)
        committed.pop("generatedAt", None)
        self.assertEqual(
            committed,
            generated,
            "index.json is stale; regenerate with "
            "`agent-packs index -output index.json`",
        )


if __name__ == "__main__":
    unittest.main()
