"""Run a documented Easel skill through the native agent runtime."""
from __future__ import annotations
import sys
from pathlib import Path
from easel.persona import profile_exists
PROJECT_ROOT=Path(__file__).resolve().parents[2]
SKILLS_DIR=PROJECT_ROOT/"skills"/"openclaw"
PROFILES_DIR=PROJECT_ROOT/"profiles"
def _list_all_skills():
    return [d.name for d in sorted(SKILLS_DIR.iterdir()) if d.is_dir() and (d/"SKILL.md").is_file()] if SKILLS_DIR.is_dir() else []
def _find_skill(name):
    for candidate in ([name,f"skill-{name}"] if not name.startswith("skill-") else [name]):
        if (SKILLS_DIR/candidate/"SKILL.md").is_file(): return candidate
    return None
def _resolve_input(raw):
    try: p=Path(raw); is_file=p.is_file()
    except OSError: return raw
    if not is_file: return raw
    suffix=p.suffix.lower()
    if suffix in {".jpg",".jpeg",".png",".gif",".webp",".bmp"}: return f"请处理这个图片：{p.resolve()}"
    if suffix in {".mp3",".mp4",".wav",".mov",".m4a",".flac",".aac",".ogg",".webm",".mkv",".avi",".pdf",".zip",".gz",".tar",".7z",".rar"}: return f"请处理这个文件：{p.resolve()}"
    try: return p.read_text(encoding="utf-8")
    except UnicodeDecodeError: return f"请处理这个文件：{p.resolve()}"
def _check_profile_exists(name):
    if profile_exists(name): return True
    available=[d.name for d in PROFILES_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")]
    print(f"[easel] ERROR: 画像 '{name}' 不存在",file=sys.stderr)
    if available: print(f"  可用画像: {', '.join(available)}",file=sys.stderr)
    return False
def cmd_skill(args):
    full=_find_skill(args.name)
    if not full:
        print(f"[easel] ERROR: SKILL '{args.name}' 不存在\n  可用 SKILL:\n"+"\n".join(f"    {s}" for s in _list_all_skills()),file=sys.stderr); return 1
    if args.profile and not _check_profile_exists(args.profile): return 1
    session=f"skill-{full}-{__import__('time').time_ns()}"
    message=f"请执行 Easel 技能 {full}。首先阅读该技能目录下的 SKILL.md 并遵循其流程。\n\n输入内容：\n{_resolve_input(args.input)}"
    print(f"[easel] SKILL: {full}")
    if args.profile: print(f"[easel] 画像: {args.profile}")
    print("─"*50)
    try:
        from easel.runtime import AgentRuntime
        for event in AgentRuntime().run(message,session_id=session,persona=args.profile):
            if event["event"]=="token": print(event["data"])
            elif event["event"]=="activity": print(f"  · {event['data']}")
        return 0
    except Exception as exc:
        print(f"❌ {exc}",file=sys.stderr); return 1
