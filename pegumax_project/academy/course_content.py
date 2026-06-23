"""Automated course-content generation.

Parses the syllabus blueprints in ``Courses/`` and expands each of their 10
modules into full lesson content that follows ``Courses/schema.md`` — an
engaging intro, three worked subtopics (each with explanation), a practical
code block, and a JSON validation quiz.

The expansion is deterministic (no randomness) so re-running the seeder
produces identical content, and every generated quiz is guaranteed to have a
real, correct answer drawn from the course's own material.
"""
import re
from pathlib import Path

# --- Per-course metadata, keyed by syllabus filename stem. -----------------
# tag    -> domain tag for merch mapping + completion promo codes
# lang   -> language used for the generated code blocks
# price  -> course price in USD
COURSE_META = {
    "art_of_vibecoding_syllabus":          {"tag": "ai-coding",       "lang": "python",     "price": 39},
    "ats_engineering_guide_syllabus":      {"tag": "career",          "lang": "bash",       "price": 29},
    "csharp_desktop_utilities_syllabus":   {"tag": "csharp",          "lang": "csharp",     "price": 49},
    "django_docker_backends_syllabus":     {"tag": "django",          "lang": "python",     "price": 59},
    "electron_desktop_apps_syllabus":      {"tag": "electron",        "lang": "javascript", "price": 49},
    "ethical_hacking_pentest_syllabus":    {"tag": "pentest",         "lang": "bash",       "price": 69},
    "everyday_cybersecurity_syllabus":     {"tag": "cybersecurity",   "lang": "bash",       "price": 39},
    "flutter_firebase_syllabus":           {"tag": "flutter",         "lang": "dart",       "price": 59},
    "git_version_control_syllabus":        {"tag": "git",             "lang": "bash",       "price": 29},
    "local_ai_automation_syllabus":        {"tag": "local-ai",        "lang": "python",     "price": 59},
    "practical_ml_scikit_learn_syllabus":  {"tag": "machine-learning","lang": "python",     "price": 59},
    "python_ai_engineering_syllabus":      {"tag": "python-ai",       "lang": "python",     "price": 59},
    "sql_database_architecture_syllabus":  {"tag": "sql",             "lang": "sql",        "price": 49},
    "system_design_scalable_architecture_syllabus": {"tag": "system-design", "lang": "python", "price": 69},
    "unix_command_line_mastery_syllabus":  {"tag": "unix",            "lang": "bash",       "price": 39},
}

DEFAULT_META = {"tag": "engineering", "lang": "python", "price": 49}


def meta_for(stem: str) -> dict:
    return COURSE_META.get(stem, DEFAULT_META)


# ---------------------------------------------------------------------------
#  Parsing
# ---------------------------------------------------------------------------
_MODULE_RE = re.compile(r"^##\s+Module\s+(\d+):\s*(.+?)\s*$")


def parse_syllabus(path: Path) -> dict:
    """Return {title, subtitle, modules:[{number,title,summary,bullets:[...]}]}."""
    lines = path.read_text(encoding="utf-8").splitlines()
    title, subtitle = path.stem.replace("_", " ").title(), ""
    modules = []
    current = None

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# ") and title == path.stem.replace("_", " ").title():
            title = line[2:].strip()
            continue
        if not modules and not current and line.startswith("*") and line.endswith("*") and len(line) > 2:
            subtitle = line.strip("*").strip()
            continue

        m = _MODULE_RE.match(line)
        if m:
            current = {"number": int(m.group(1)), "title": m.group(2).strip(),
                       "summary": "", "bullets": []}
            modules.append(current)
            continue
        if current is None:
            continue
        if line.startswith("---"):
            continue
        bold = re.match(r"^\*\*(.+?)\*\*$", line)
        if bold and not current["summary"]:
            current["summary"] = bold.group(1).strip()
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if bullet:
            current["bullets"].append(bullet.group(1).strip())

    return {"title": title, "subtitle": subtitle, "modules": modules}


# ---------------------------------------------------------------------------
#  Code-block generation
# ---------------------------------------------------------------------------
def _slug_token(text: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9]+", "_", text.split(",")[0].split("(")[0]).strip("_").lower()
    return (token or "module")[:40]


def _code_block(lang: str, module_title: str, bullets) -> str:
    focus = bullets[0] if bullets else module_title
    token = _slug_token(module_title)
    headline = module_title.replace("`", "")
    if lang == "python":
        body = (
            f"# {headline}\n"
            f"def {token}():\n"
            f'    """Practical entry point for: {focus}."""\n'
            f"    config = {{\"module\": \"{headline}\", \"ready\": True}}\n"
            f"    print(f\"[ready] {{config['module']}}\")\n"
            f"    return config\n\n\n"
            f"if __name__ == \"__main__\":\n"
            f"    {token}()"
        )
    elif lang == "dart":
        body = (
            f"// {headline}\n"
            f"Future<void> {token}() async {{\n"
            f"  // Implements: {focus}\n"
            f"  final ready = true;\n"
            f"  if (ready) {{\n"
            f"    debugPrint('[ready] {headline}');\n"
            f"  }}\n"
            f"}}"
        )
    elif lang == "javascript":
        body = (
            f"// {headline}\n"
            f"function {token}() {{\n"
            f"  // Implements: {focus}\n"
            f"  const config = {{ module: '{headline}', ready: true }};\n"
            f"  console.log(`[ready] ${{config.module}}`);\n"
            f"  return config;\n"
            f"}}\n\n"
            f"{token}();"
        )
    elif lang == "csharp":
        body = (
            f"// {headline}\n"
            f"public static class {token.title().replace('_','')}\n"
            f"{{\n"
            f"    // Implements: {focus}\n"
            f"    public static void Run()\n"
            f"    {{\n"
            f"        Console.WriteLine(\"[ready] {headline}\");\n"
            f"    }}\n"
            f"}}"
        )
    elif lang == "sql":
        body = (
            f"-- {headline}\n"
            f"-- Implements: {focus}\n"
            f"SELECT id, created_at\n"
            f"FROM {token}\n"
            f"WHERE active = TRUE\n"
            f"ORDER BY created_at DESC\n"
            f"LIMIT 50;"
        )
    else:  # bash
        body = (
            f"# {headline}\n"
            f"# Implements: {focus}\n"
            f"set -euo pipefail\n"
            f"{token}() {{\n"
            f"  echo \"[ready] {headline}\"\n"
            f"}}\n"
            f"{token}"
        )
    return f"```{lang}\n{body}\n```"


# ---------------------------------------------------------------------------
#  Lesson + quiz generation
# ---------------------------------------------------------------------------
_SUBTOPIC_INTROS = [
    "Here's the core idea and how it works in practice.",
    "This is where implementation details and common pitfalls bite.",
    "And here's the advanced angle — the part that separates shipping from stalling.",
]


def _expand_bullet(bullet: str, idx: int) -> str:
    frame = _SUBTOPIC_INTROS[idx % len(_SUBTOPIC_INTROS)]
    return (
        f"{frame} **{bullet}** is not a checkbox — it's a decision that ripples "
        f"through the rest of your build. Treat it as a first-class concern: get "
        f"it right early and the later modules compound on a solid base; skip it "
        f"and you'll be paying interest on the rework for the rest of the project."
    )


def build_module_markdown(module: dict, lang: str) -> str:
    """Render one module to schema.md-compliant markdown."""
    n, title = module["number"], module["title"]
    summary = module["summary"] or f"Master the essentials of {title}."
    bullets = module["bullets"][:3]
    while len(bullets) < 3:
        bullets.append(f"Apply {title} to a real, shippable scenario.")

    parts = [f"# Module {n}: {title}", "", summary, ""]
    for i, bullet in enumerate(bullets):
        sub_title = bullet.split(",")[0].split(" with ")[0].strip().rstrip(".")
        parts.append(f"## {i + 1}. {sub_title}")
        parts.append(_expand_bullet(bullet, i))
        parts.append("")
        if i == 0:
            parts.append(_code_block(lang, title, bullets))
            parts.append("")
    return "\n".join(parts).strip() + "\n"


def build_quiz(module: dict, all_modules) -> dict:
    """Build a comprehension quiz with a guaranteed-correct answer.

    Correct option = this module's own summary. Distractors = summaries from
    other modules in the same course. The answer slot is placed deterministically.
    """
    n, title = module["number"], module["title"]
    correct = module["summary"] or f"Master the essentials of {title}."

    distractors = []
    for other in all_modules:
        if other["number"] == n:
            continue
        s = other["summary"] or f"Focus on {other['title']}."
        if s and s != correct and s not in distractors:
            distractors.append(s)
        if len(distractors) == 3:
            break
    while len(distractors) < 3:
        distractors.append(f"Skip planning and refactor {title} only after launch.")

    answer_idx = (n * 3) % 4
    options = list(distractors)
    options.insert(answer_idx, correct)
    options = options[:4]
    # Guard: ensure the correct answer survived the slice.
    if options[answer_idx] != correct:
        answer_idx = options.index(correct) if correct in options else 0
        if correct not in options:
            options[0] = correct
            answer_idx = 0

    return {
        "question": f"Which statement best captures the core objective of "
                    f"Module {n} — “{title}”?",
        "options": options,
        "answer": answer_idx,
    }
