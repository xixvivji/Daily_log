from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LOGS_DIR = ROOT / "logs"
START = "<!-- LOG_INDEX_START -->"
END = "<!-- LOG_INDEX_END -->"


def title_for(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def build_index() -> str:
    logs = sorted(LOGS_DIR.glob("*.md"), reverse=True)
    if not logs:
        return "- 아직 작성된 로그가 없습니다."

    lines = []
    for log in logs:
        rel = log.relative_to(ROOT).as_posix()
        lines.append(f"- [{title_for(log)}]({rel})")
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
