"""AGENTS.md (read by Codex and other agents) and CLAUDE.md (read by Claude Code) must carry the same rules.

Written with SI assistance (Claude Code).
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = "## Coordination"


def rules(name):
    text = io.open(os.path.join(ROOT, name), encoding="utf-8").read().replace("\r\n", "\n")
    assert START in text, "%s has no section %r" % (name, START)
    return text[text.index(START):].strip()


def test_agents_md_and_claude_md_hold_the_same_rules():
    assert rules("AGENTS.md") == rules("CLAUDE.md"), "AGENTS.md and CLAUDE.md differ: change both together"


def test_rules_hold_the_checks_before_done():
    text = rules("AGENTS.md")
    assert "## Before you report DONE" in text
    for n in range(1, 6):
        assert "\n%d. **" % n in text.split("## Before you report DONE")[1]
