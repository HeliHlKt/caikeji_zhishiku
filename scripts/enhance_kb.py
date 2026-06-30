from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


BOOK_PAGE_OFFSET = 23


@dataclass(frozen=True)
class ChapterProfile:
    number: int
    book_start: int
    themes: list[str]
    question_focus: list[str]
    answer_lenses: list[str]


CHAPTER_PROFILES = [
    ChapterProfile(1, 1, ["crystallography", "lattice", "crystal plane", "crystal direction", "reciprocal lattice"], ["indexing crystal planes and directions", "FCC/BCC/HCP comparison", "Bravais lattice vs real structure"], ["definition", "geometry", "structure", "implication", "connections"]),
    ChapterProfile(2, 44, ["atomic structure", "bonding", "electronic structure", "solid solution", "ionic compounds", "intermetallics"], ["how bonding affects properties", "Hume-Rothery rules", "how compound structures are stabilized"], ["microstructure", "bonding", "stability", "property impact", "examples"]),
    ChapterProfile(3, 148, ["slip", "Schmid law", "twinning", "strain hardening", "texture", "fracture"], ["slip vs twinning", "single crystal vs polycrystal deformation", "mechanism of strain hardening"], ["driving force", "crystallographic condition", "deformation path", "microstructure evolution", "property effect"]),
    ChapterProfile(4, 203, ["point defects", "dislocations", "stress field", "dislocation interaction", "grain boundaries"], ["point defect vs dislocation", "how dislocations control strength and plasticity", "comparison of dislocation models"], ["defect type", "energy", "motion", "interaction", "material behavior"]),
    ChapterProfile(5, 316, ["thermodynamics", "Gibbs free energy", "chemical potential", "phase equilibrium"], ["how to use free energy to judge stability", "phase equilibrium criteria", "thermodynamic support for phase diagrams"], ["state function", "criterion", "diagram", "driving force", "processing link"]),
    ChapterProfile(6, 348, ["phase diagram", "phase rule", "lever rule", "Fe-C diagram", "ternary diagram"], ["how to read phase diagrams", "classic Fe-C questions", "non-equilibrium solidification analysis"], ["diagram", "phase region", "microstructure evolution", "process impact", "examples"]),
    ChapterProfile(7, 411, ["interface", "grain boundary", "interface energy", "segregation", "migration"], ["how interface energy changes microstructure", "segregation and migration driving force", "how interface types differ"], ["classification", "thermodynamics", "kinetics", "morphology", "measurement"]),
    ChapterProfile(8, 434, ["diffusion", "Fick laws", "Kirkendall effect", "reaction diffusion", "ionic diffusion", "sintering"], ["how to structure a diffusion solution", "what Kirkendall effect proves", "what controls diffusion coefficient"], ["governing equation", "boundary condition", "mechanism", "thermodynamic correction", "application"]),
    ChapterProfile(9, 486, ["solidification", "nucleation", "growth", "constitutional undercooling", "segregation", "eutectic growth"], ["homogeneous vs heterogeneous nucleation", "how undercooling controls morphology", "how ingot structure is controlled"], ["driving force", "kinetics", "growth mode", "segregation", "process control"]),
    ChapterProfile(10, 512, ["recovery", "recrystallization", "grain growth", "hot deformation", "superplasticity"], ["recovery vs recrystallization", "factors controlling recrystallization temperature and grain size", "hot-worked structure evolution"], ["stored energy", "restoration path", "kinetics", "property change", "industrial meaning"]),
    ChapterProfile(11, 549, ["diffusional phase transformation", "aging", "spinodal decomposition", "coarsening", "pearlite", "bainite", "ordering"], ["how to explain diffusional transformations", "pearlite vs bainite vs precipitation strengthening", "logic of age hardening"], ["transformation type", "nucleation and growth", "microstructure", "strengthening", "transformation curve"]),
    ChapterProfile(12, 627, ["martensitic transformation", "tempering", "shape memory", "stress-induced transformation", "maraging steel"], ["martensite vs pearlite and bainite", "tempering stage-by-stage changes", "how maraging steel strengthens"], ["diffusionless feature", "crystallography", "transformation temperature", "tempering decomposition", "alloy design"]),
]


TOPIC_ROUTES = [
    {"topic": "crystal structure and crystallography", "aliases": ["lattice", "Bravais", "crystal plane", "crystal direction", "FCC", "BCC", "HCP", "reciprocal lattice"], "chapters": [1]},
    {"topic": "bonding and structure stability", "aliases": ["ionic bond", "covalent bond", "metallic bond", "solid solution", "intermetallic", "Hume-Rothery"], "chapters": [2]},
    {"topic": "plastic deformation and fracture", "aliases": ["slip", "twinning", "Schmid", "work hardening", "texture", "fracture"], "chapters": [3]},
    {"topic": "defects and dislocations", "aliases": ["point defect", "dislocation", "Burgers vector", "grain boundary", "Peierls"], "chapters": [4]},
    {"topic": "thermodynamics and phase equilibrium", "aliases": ["Gibbs", "chemical potential", "phase equilibrium", "free energy"], "chapters": [5]},
    {"topic": "phase-diagram analysis", "aliases": ["Fe-C", "lever rule", "eutectic", "peritectic", "ternary phase diagram"], "chapters": [6]},
    {"topic": "interfaces and grain boundaries", "aliases": ["interface energy", "segregation", "interface migration", "grain boundary"], "chapters": [7]},
    {"topic": "diffusion and sintering", "aliases": ["Fick", "Kirkendall", "reaction diffusion", "ionic diffusion", "sintering"], "chapters": [8]},
    {"topic": "solidification and crystallization", "aliases": ["nucleation", "solidification", "constitutional undercooling", "segregation", "eutectic growth"], "chapters": [9]},
    {"topic": "recovery, recrystallization, hot deformation", "aliases": ["recovery", "recrystallization", "grain growth", "hot deformation", "superplasticity"], "chapters": [10]},
    {"topic": "diffusional solid-state transformations", "aliases": ["aging", "spinodal", "pearlite", "bainite", "ordering", "coarsening"], "chapters": [11]},
    {"topic": "martensite and tempering", "aliases": ["martensite", "tempering", "Ms", "Md", "shape memory", "maraging steel"], "chapters": [12]},
]


ANSWER_PATTERNS = [
    {"question_type": "mechanism explanation", "use_when": "The user asks why something happens or asks for the mechanism.", "steps": ["Define the object", "State the driving force", "List the required conditions", "Describe the stage-by-stage process", "Explain microstructure and property consequences", "Add a textbook example if available"]},
    {"question_type": "comparison", "use_when": "The user asks for similarities and differences.", "steps": ["Define each item", "Compare driving force and diffusion character", "Compare structure and morphology", "Compare property consequences", "Summarize memorable distinctions"]},
    {"question_type": "diagram analysis", "use_when": "The user asks how to analyze a phase diagram or transformation curve.", "steps": ["Identify axes and regions", "Mark key lines and points", "Trace the path with temperature or composition", "Translate the path into microstructure evolution", "Add lever-rule or free-energy reasoning if needed"]},
    {"question_type": "process to structure to property", "use_when": "The user asks what a process does to a material.", "steps": ["State what the process changes", "Explain the resulting structural evolution", "Connect the structure to property change", "Mention risks, limits, or industrial meaning"]},
]


CROSS_CHAPTER_ROUTES = [
    {
        "route": "strengthening mechanisms",
        "chapters": [3, 4, 11, 12],
        "why": "Connect deformation, defects, precipitation, and martensitic strengthening in one answer.",
    },
    {
        "route": "thermodynamics to phase diagram to transformation",
        "chapters": [5, 6, 11, 12],
        "why": "Useful when the question moves from free energy to phase stability and then to transformations.",
    },
    {
        "route": "processing -> structure -> property",
        "chapters": [3, 8, 9, 10, 11, 12],
        "why": "Useful for deformation, diffusion, solidification, heat treatment, and transformation questions.",
    },
    {
        "route": "defects and transport",
        "chapters": [4, 7, 8],
        "why": "Useful for questions linking defects, interfaces, and diffusion behavior.",
    },
    {
        "route": "structure and bonding foundation",
        "chapters": [1, 2, 5],
        "why": "Useful for questions that begin with crystallography or bonding and then ask about stability.",
    },
]


QUESTION_ENTRY_POINTS = [
    {
        "entry": "Explain a mechanism in full",
        "best_pattern": "mechanism explanation",
        "recommended_routes": ["strengthening mechanisms", "thermodynamics to phase diagram to transformation", "defects and transport"],
    },
    {
        "entry": "Compare two transformations or two structures",
        "best_pattern": "comparison",
        "recommended_routes": ["strengthening mechanisms", "thermodynamics to phase diagram to transformation"],
    },
    {
        "entry": "Analyze a phase diagram or transformation curve",
        "best_pattern": "diagram analysis",
        "recommended_routes": ["thermodynamics to phase diagram to transformation"],
    },
    {
        "entry": "Explain how a process changes material behavior",
        "best_pattern": "process to structure to property",
        "recommended_routes": ["processing -> structure -> property", "defects and transport"],
    },
    {
        "entry": "Build study notes or an exam-style summary",
        "best_pattern": "comparison",
        "recommended_routes": ["structure and bonding foundation", "processing -> structure -> property"],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate enhanced knowledge-base artifacts.")
    parser.add_argument("--root", required=True, help="Knowledge-base root directory.")
    return parser.parse_args()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_ocr_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("．", ".")
    text = text.replace("·", "·")
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[0-9A-Za-z])", "", text)
    text = re.sub(r"(?<=[0-9A-Za-z])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=第)\s+(?=[0-9一二三四五六七八九十])", "", text)
    text = re.sub(r"(?<=章)\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=\.)\s+(?=[0-9])", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_chapter_title(cleaned_line: str, chapter_number: int) -> str:
    pattern = rf"第{chapter_number}章(.+)"
    match = re.search(pattern, cleaned_line)
    if not match:
        return f"Chapter {chapter_number}"
    remainder = match.group(1)
    remainder = re.split(rf"{chapter_number}\.\d|引言|概述", remainder, maxsplit=1)[0]
    remainder = remainder.replace("材料科学基础", "").strip(" ·.-")
    return remainder or f"Chapter {chapter_number}"


def build_chapter_map(ocr_dir: Path) -> list[dict]:
    chapter_map = []
    for index, profile in enumerate(CHAPTER_PROFILES):
        next_profile = CHAPTER_PROFILES[index + 1] if index + 1 < len(CHAPTER_PROFILES) else None
        book_end = (next_profile.book_start - 1) if next_profile else 673
        pdf_start = profile.book_start + BOOK_PAGE_OFFSET
        pdf_end = book_end + BOOK_PAGE_OFFSET
        page_path = ocr_dir / f"page_{pdf_start:04d}.txt"
        first_line = ""
        title = f"Chapter {profile.number}"
        if page_path.exists():
            raw = page_path.read_text(encoding="utf-8", errors="ignore")
            cleaned = clean_ocr_text(raw)
            first_line = cleaned[:240]
            title = extract_chapter_title(cleaned, profile.number)
        chapter_map.append(
            {
                "chapter": profile.number,
                "title": title,
                "book_page_start": profile.book_start,
                "book_page_end": book_end,
                "pdf_page_start": pdf_start,
                "pdf_page_end": pdf_end,
                "themes": profile.themes,
                "question_focus": profile.question_focus,
                "answer_lenses": profile.answer_lenses,
                "chapter_opening_preview": first_line,
            }
        )
    return chapter_map


def build_clean_page_map(ocr_dir: Path, chapter_map: list[dict]) -> list[dict]:
    chapter_ranges = [(item["pdf_page_start"], item["pdf_page_end"], item["chapter"], item["title"]) for item in chapter_map]
    clean_pages = []
    for page_file in sorted(ocr_dir.glob("page_*.txt")):
        page_number = int(page_file.stem.split("_")[1])
        raw = page_file.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_ocr_text(raw)
        chapter_num = None
        chapter_title = None
        for start, end, num, title in chapter_ranges:
            if start <= page_number <= end:
                chapter_num = num
                chapter_title = title
                break
        clean_pages.append(
            {
                "page": page_number,
                "chapter": chapter_num,
                "chapter_title": chapter_title,
                "preview": cleaned[:240],
            }
        )
    return clean_pages


def build_chapter_guides(chapter_map: list[dict]) -> str:
    lines = ["# Chapter Guides", ""]
    for chapter in chapter_map:
        lines.append(f"## Chapter {chapter['chapter']} - {chapter['title']}")
        lines.append("")
        lines.append(f"- PDF page range: {chapter['pdf_page_start']}-{chapter['pdf_page_end']}")
        lines.append(f"- Book page range: {chapter['book_page_start']}-{chapter['book_page_end']}")
        lines.append(f"- Core themes: {', '.join(chapter['themes'])}")
        lines.append(f"- Typical questions: {'; '.join(chapter['question_focus'])}")
        lines.append(f"- Answer lenses: {' -> '.join(chapter['answer_lenses'])}")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_core_concepts(chapter_map: list[dict]) -> str:
    lines = ["# Core Concepts", ""]
    for chapter in chapter_map:
        lines.append(f"## Chapter {chapter['chapter']} - {chapter['title']}")
        lines.append("")
        for theme in chapter["themes"]:
            lines.append(f"### {theme}")
            lines.append(f"- Chapter anchor: Chapter {chapter['chapter']}")
            lines.append(f"- Start with: {chapter['answer_lenses'][0]} and {chapter['answer_lenses'][1]}")
            lines.append(f"- Then expand with: {chapter['answer_lenses'][2]} and {chapter['answer_lenses'][3]}")
            lines.append(f"- Example follow-up: {chapter['question_focus'][0]}")
            lines.append("")
    return "\n".join(lines)


def build_answer_playbook() -> str:
    lines = ["# Answer Playbook", ""]
    lines.append("## General Rules")
    lines.append("")
    lines.append("- Do not stop at a definition. Add mechanism, conditions, structure change, and property consequences.")
    lines.append("- When possible, anchor answers to chapter and page ranges.")
    lines.append("- For comparisons, use the same dimensions: driving force, diffusion character, structure, properties, applications.")
    lines.append("- For processing questions, answer in the order: condition change -> structure evolution -> property change.")
    lines.append("")
    for pattern in ANSWER_PATTERNS:
        lines.append(f"## {pattern['question_type']}")
        lines.append("")
        lines.append(f"- Use when: {pattern['use_when']}")
        lines.append(f"- Recommended steps: {' -> '.join(pattern['steps'])}")
        lines.append("")
    return "\n".join(lines)


def build_topic_routes_md(chapter_map: list[dict]) -> str:
    chapter_lookup = {item["chapter"]: item for item in chapter_map}
    lines = ["# Topic Routes", ""]
    for route in TOPIC_ROUTES:
        lines.append(f"## {route['topic']}")
        lines.append("")
        lines.append(f"- Search aliases: {', '.join(route['aliases'])}")
        refs = []
        for chapter_num in route["chapters"]:
            chapter = chapter_lookup[chapter_num]
            refs.append(f"Chapter {chapter_num} ({chapter['title']}, PDF {chapter['pdf_page_start']}-{chapter['pdf_page_end']})")
        lines.append(f"- Key chapters: {'; '.join(refs)}")
        lines.append("")
    return "\n".join(lines)


def build_ready_for_qa(chapter_map: list[dict]) -> str:
    lines = ["# Ready For QA", ""]
    lines.append("## What this enhanced layer supports")
    lines.append("")
    lines.append("- Mechanism questions that need more than a definition.")
    lines.append("- Comparison questions across two or more concepts.")
    lines.append("- Chapter-level summaries, exam-style prompts, and study guides.")
    lines.append("- Process -> structure -> property explanations.")
    lines.append("")
    lines.append("## Recommended files to consult first")
    lines.append("")
    lines.append("- `04_index/chapter_map.json`")
    lines.append("- `04_index/topic_routes.json`")
    lines.append("- `04_index/clean_page_map.json`")
    lines.append("- `06_topics/chapter_guides.md`")
    lines.append("- `07_qa/answer_playbook.md`")
    lines.append("")
    lines.append("## Chapter Overview")
    lines.append("")
    for chapter in chapter_map:
        lines.append(f"- Chapter {chapter['chapter']}: {chapter['title']} (PDF {chapter['pdf_page_start']}-{chapter['pdf_page_end']})")
    lines.append("")
    return "\n".join(lines)


def build_cross_chapter_routes_md(chapter_map: list[dict]) -> str:
    lookup = {item["chapter"]: item for item in chapter_map}
    lines = ["# Cross Chapter Routes", ""]
    for route in CROSS_CHAPTER_ROUTES:
        lines.append(f"## {route['route']}")
        lines.append("")
        refs = []
        for chapter_num in route["chapters"]:
            chapter = lookup[chapter_num]
            refs.append(f"Chapter {chapter_num} ({chapter['title']}, PDF {chapter['pdf_page_start']}-{chapter['pdf_page_end']})")
        lines.append(f"- Chapter chain: {'; '.join(refs)}")
        lines.append(f"- Why use it: {route['why']}")
        lines.append("")
    return "\n".join(lines)


def build_question_entry_points_md() -> str:
    lines = ["# Question Entry Points", ""]
    for item in QUESTION_ENTRY_POINTS:
        lines.append(f"## {item['entry']}")
        lines.append("")
        lines.append(f"- Best answer pattern: {item['best_pattern']}")
        lines.append(f"- Recommended routes: {', '.join(item['recommended_routes'])}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    ocr_dir = root / "02_ocr_pages"
    index_dir = root / "04_index"
    cards_dir = root / "05_cards"
    topics_dir = root / "06_topics"
    qa_dir = root / "07_qa"
    output_dir = root / "08_outputs"
    for path in (index_dir, cards_dir, topics_dir, qa_dir, output_dir):
        path.mkdir(parents=True, exist_ok=True)

    chapter_map = build_chapter_map(ocr_dir)
    clean_page_map = build_clean_page_map(ocr_dir, chapter_map)

    write_json(index_dir / "chapter_map.json", chapter_map)
    write_json(index_dir / "topic_routes.json", TOPIC_ROUTES)
    write_json(index_dir / "answer_patterns.json", ANSWER_PATTERNS)
    write_json(index_dir / "cross_chapter_routes.json", CROSS_CHAPTER_ROUTES)
    write_json(index_dir / "question_entry_points.json", QUESTION_ENTRY_POINTS)
    write_json(index_dir / "clean_page_map.json", clean_page_map)

    (topics_dir / "chapter_guides.md").write_text(build_chapter_guides(chapter_map), encoding="utf-8")
    (topics_dir / "topic_routes.md").write_text(build_topic_routes_md(chapter_map), encoding="utf-8")
    (topics_dir / "cross_chapter_routes.md").write_text(build_cross_chapter_routes_md(chapter_map), encoding="utf-8")
    (cards_dir / "core_concepts.md").write_text(build_core_concepts(chapter_map), encoding="utf-8")
    (qa_dir / "answer_playbook.md").write_text(build_answer_playbook(), encoding="utf-8")
    (qa_dir / "question_entry_points.md").write_text(build_question_entry_points_md(), encoding="utf-8")
    (output_dir / "ready_for_qa.md").write_text(build_ready_for_qa(chapter_map), encoding="utf-8")

    print("Enhanced artifacts generated.")


if __name__ == "__main__":
    main()
