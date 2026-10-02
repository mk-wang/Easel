"""Easel CLI — native provider-backed content workflow."""
from __future__ import annotations
import argparse, os, subprocess, sys, time
from pathlib import Path
from easel.commands.doctor import cmd_doctor
from easel.commands.ping import cmd_ping
from easel.commands.skill import cmd_skill
from easel.persona import list_personas as _list_personas
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = PROJECT_ROOT / "profiles"
CYAN="\033[0;36m"; GREEN="\033[0;32m"; YELLOW="\033[0;33m"; RED="\033[0;31m"; DIM="\033[0;90m"; NC="\033[0m"
def _proxy_env():
    env=os.environ.copy(); env.setdefault("EASEL_ROOT",str(PROJECT_ROOT)); return env

def cmd_chat(_args):
    print(f"\n  {CYAN}Easel{NC} — 社媒内容工作流\n")
    personas=_list_personas(); selected=None
    if personas:
        print("  选择用户画像：")
        for i,name in enumerate(personas,1):
            identity=PROFILES_DIR/name/"identity.md"; desc=""
            if identity.is_file():
                for line in identity.read_text(encoding="utf-8").splitlines():
                    line=line.strip()
                    if line and not line.startswith(("#","<!--")): desc=f" — {line[:50]}"; break
            print(f"    {i}) {name}{desc}")
        print("    0) 不使用画像（通用模式）")
        try: choice=input("  请选择 [0]: ").strip()
        except (EOFError,KeyboardInterrupt): print(); return 0
        if choice and choice!="0":
            try:
                idx=int(choice)-1
                if 0<=idx<len(personas): selected=personas[idx]
            except ValueError:
                if choice in personas: selected=choice
    session=f"easel-{time.time_ns()}"
    print(f"\n  {GREEN+'✓'+NC if selected else YELLOW+'→'+NC} {'画像: '+selected if selected else '通用模式'}")
    print(f"  {DIM}会话: {session}{NC}\n  {DIM}/session 切换历史会话 · /new 新会话 · /quit 退出{NC}\n  {CYAN}Ctrl+C{NC} 退出\n")
    from easel.runtime import AgentRuntime, STATE
    runtime=AgentRuntime()
    while True:
        try: message=input("你> ").strip()
        except (EOFError,KeyboardInterrupt): print(); return 0
        if not message: continue
        if message.lower() in {"/quit","/exit","quit","exit"}: return 0
        if message == "/new":
            session=f"easel-{time.time_ns()}"
            print(f"  {DIM}新会话: {session}{NC}")
            continue
        if message == "/session":
            sessions=sorted((STATE/"sessions").glob("easel-*.json"),key=lambda p:p.stat().st_mtime,reverse=True) if (STATE/"sessions").is_dir() else []
            if not sessions: print("  暂无历史会话"); continue
            for i,path in enumerate(sessions[:50],1): print(f"  {i}) {path.stem}")
            try: choice=input("选择编号（回车取消）: ").strip()
            except (EOFError,KeyboardInterrupt): print(); continue
            if choice:
                try:
                    index=int(choice)-1
                    if 0<=index<min(50,len(sessions)):
                        session=sessions[index].stem
                        print(f"  {DIM}已切换: {session}{NC}")
                except ValueError: print("  请输入列表中的编号")
            continue
        try:
            for event in runtime.run(message,session_id=session,persona=selected):
                if event["event"]=="token": print(event["data"],flush=True)
                elif event["event"]=="activity": print(f"\n  · {event['data']}",flush=True)
                elif event["event"]=="question":
                    try:
                        from easel.native_settings import answer_question
                        card = __import__("json").loads(event["data"])
                        answers = {}
                        for item in card.get("questions", []):
                            print(f"\n{item.get('header') or 'Easel'}: {item.get('question', '')}")
                            options = item.get("options", [])
                            for i, option in enumerate(options, 1): print(f"  {i}) {option.get('label', '')} — {option.get('description', '')}")
                            choice = input("选择编号或输入自定义答案（回车取消）: ").strip()
                            selected = options[int(choice)-1]["label"] if choice.isdigit() and 1 <= int(choice) <= len(options) else ([choice] if choice else ["取消"])
                            answers[item["questionId"]] = selected
                        answer_question(session, card["id"], answers)
                    except (EOFError, KeyboardInterrupt):
                        print("\n已取消。")
        except Exception as exc:  # provider/network failures should not dump a traceback
            print(f"{RED}请求失败：{exc}{NC}",file=sys.stderr)

def cmd_web(args):
    port=getattr(args,"port",7860); env=_proxy_env(); env["EASEL_PORT"]=str(port)
    script=PROJECT_ROOT/"web"/"app.py"
    if not script.is_file(): print(f"{RED}未找到 web/app.py — 请重跑 setup。{NC}",file=sys.stderr); return 1
    return subprocess.run([sys.executable,str(script)],cwd=str(PROJECT_ROOT),env=env).returncode

def main(argv=None):
    parser=argparse.ArgumentParser(prog="easel",description="Easel — 社媒内容工作流 CLI")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("chat",help="交互对话（新会话）").set_defaults(func=cmd_chat)
    sub.add_parser("doctor",help="检查环境").set_defaults(func=cmd_doctor)
    sub.add_parser("ping",help="检查模型配置与运行时").set_defaults(func=cmd_ping)
    p=sub.add_parser("skill",help="运行 SKILL"); p.add_argument("name"); p.add_argument("--input","-i",required=True); p.add_argument("--profile","-p"); p.set_defaults(func=cmd_skill)
    p=sub.add_parser("web",help="启动 Web UI"); p.add_argument("--port",type=int,default=7860); p.set_defaults(func=cmd_web)
    args=parser.parse_args(argv); return args.func(args)
if __name__=="__main__": sys.exit(main())
