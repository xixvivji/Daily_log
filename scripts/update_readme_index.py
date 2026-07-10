from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
START = "<!-- NOTE_INDEX_START -->"
END = "<!-- NOTE_INDEX_END -->"
SECTIONS = [
    ("Infrastructure", ROOT / "infrastructure"),
    ("Backend", ROOT / "backend"),
]


def title_for(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def build_section(title: str, directory: Path) -> list[str]:
    lines = []
    reverse = title != "Backend"
    notes = [
        path for path in sorted(directory.glob("*.md"), reverse=reverse)
        if path.name.lower() != "readme.md"
    ]
    lines.append(f"### {title}")
    if not notes:
        lines.append("")
        lines.append("- 아직 작성된 노트가 없습니다.")
        return lines

    lines.append("")
    for log in notes:
        rel = log.relative_to(ROOT).as_posix()
        lines.append(f"- [{title_for(log)}]({rel})")
    return lines


def build_index() -> str:
    lines = []
    for title, directory in SECTIONS:
        if lines:
            lines.append("")
        lines.extend(build_section(title, directory))
    return "\n".join(lines)


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit(f"README.md must contain {START} and {END} markers")

    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    updated = f"{before}{START}\n{build_index()}\n{END}{after}"
    README.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
