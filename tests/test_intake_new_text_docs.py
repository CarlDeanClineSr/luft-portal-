from pathlib import Path

import yaml

from scripts.intake_new_text_docs import generate_intake


def test_generate_intake_creates_summary_and_index(tmp_path):
    (tmp_path / "configs").mkdir()

    doc_one = tmp_path / "New Text Document (351).txt"
    doc_one.write_text(
        "Chat backup result summary with chi=0.15 boundary and 20.55 Hz observations.\n"
        "Engine workflow report result result.\n",
        encoding="utf-8",
    )
    doc_two = tmp_path / "New Text Document (352).txt"
    doc_two.write_text(
        "Child file intake material with telemetry and CME data.\n"
        "Mode 8 fracture note with value 42.\n",
        encoding="utf-8",
    )

    manifest = {
        "documents": [
            {"path": doc_one.name, "type": "chat_backup", "role": "intake", "enabled": True},
            {"path": doc_two.name, "type": "child_file", "role": "intake", "enabled": True},
        ],
        "settings": {
            "output_markdown": "reports/intake/new_text_documents_summary.md",
            "output_json": "results/intake/new_text_documents_index.json",
            "summary_preview_chars": 300,
            "top_words_limit": 5,
            "numbers_preview_limit": 5,
            "repeated_numbers_limit": 5,
            "keyword_case_sensitive": False,
        },
        "keywords": ["chi", "chi=0.15", "20.55 hz", "engine", "result", "telemetry", "mode 8", "fracture"],
    }

    manifest_path = tmp_path / "configs" / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    payload = generate_intake(manifest_path=manifest_path, root_dir=tmp_path)

    assert payload["documents_processed"] == 2
    assert payload["aggregate"]["aggregate_keyword_hits"]["result"] == 3
    assert payload["documents"][0]["numbers"]["preview"][:2] == ["0.15", "20.55"]
    assert payload["documents"][1]["keyword_hits"]["mode 8"] == 1

    summary_path = tmp_path / "reports" / "intake" / "new_text_documents_summary.md"
    index_path = tmp_path / "results" / "intake" / "new_text_documents_index.json"

    assert summary_path.exists()
    assert index_path.exists()
    assert "New Text Document (351).txt" in summary_path.read_text(encoding="utf-8")
