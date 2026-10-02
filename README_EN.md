<p align="left">
  <img src="assets/readme/logos/zhejiang_university_horizontal_readme.png#gh-light-mode-only" width="106" align="middle" alt="Zhejiang University">
  <img src="assets/readme/logos/zhejiang_university_horizontal_dark.png#gh-dark-mode-only" width="106" align="middle" alt="Zhejiang University">
  &nbsp;&nbsp;&nbsp;
  <img src="assets/readme/logos/peking_university_horizontal_red.png#gh-light-mode-only" width="98" align="middle" alt="Peking University">
  <img src="assets/readme/logos/peking_university_horizontal_dark.png#gh-dark-mode-only" width="98" align="middle" alt="Peking University">
</p>

<p align="center">
  <img src="assets/readme/brand.png#gh-light-mode-only" width="640" alt="Easel">
  <img src="assets/readme/brand-dark.png#gh-dark-mode-only" width="640" alt="Easel">
  <br>
  <img src="assets/readme/logos/real_lab_horizontal_readme.png" width="74" alt="REAL Lab">&thinsp;&thinsp;<img src="assets/readme/logos/opendcai_lab_horizontal_readme.png#gh-light-mode-only" width="83" alt="OpenDCAI Lab"><img src="assets/readme/logos/opendcai_lab_horizontal_readme_dark.png#gh-dark-mode-only" width="83" alt="OpenDCAI Lab">
</p>

<p align="center">
  <a href="README.md">简体中文</a> · <strong>English</strong>
</p>

<p align="center">
  Your personal, continuously evolving social media content assistant.<br>
  Start with an idea, then discover, plan, create, publish, and learn.
</p>

<p align="center">
  <a href="https://zju-real.github.io/Easel/"><img src="https://img.shields.io/badge/Easel-Project_Page-F05A3C?style=flat-square&logo=googlechrome&logoColor=white" alt="Easel Project Page"></a>
  <img src="https://img.shields.io/badge/native-agent-runtime-111827?style=flat-square" alt="Native agent runtime">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <a href="docs/skill-function-mapping.md"><img src="https://img.shields.io/badge/Skills-113-0F9D8A?style=flat-square" alt="113 Skills"></a>
  <a href="https://github.com/ZJU-REAL/Easel/stargazers"><img src="https://img.shields.io/github/stars/ZJU-REAL/Easel?style=flat-square&color=F6C344" alt="GitHub Stars"></a>
  <a href="https://github.com/ZJU-REAL/Easel/releases/latest"><img src="https://img.shields.io/github/v/release/ZJU-REAL/Easel?style=flat-square&color=0F9D8A&label=release" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-2EA44F?style=flat-square" alt="License: Apache 2.0"></a>
  <a href="assets/readme/wechat-group.png"><img src="https://img.shields.io/badge/WeChat-Join_Group-07C160?style=flat-square&logo=wechat&logoColor=white" alt="WeChat Group"></a>
</p>

<p align="center">
  <a href="https://trendshift.io/repositories/195527?utm_source=trendshift-badge&utm_medium=badge&utm_campaign=badge-trendshift-195527" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/trendshift/repositories/195527/daily?language=Python" alt="ZJU-REAL%2FEasel | Trendshift" width="250" height="55"/></a>
</p>

![Easel product poster](assets/readme/poster.png)

## 🎨 What Is Easel?

Easel is an open-source content workspace for social media creators. It includes its own provider-backed text agent loop, account profiles, a library of content Skills, media utilities, and publishing workflows. The native agent can read Skills, create text artifacts, ask structured questions, and run a bounded novel-writer check; media generation and publishing remain user-operated workflows.

Use the Web workbench to manage accounts, content projects, publishing workflows, and profile data. The native text agent uses the selected profile and keeps its session history locally.

Easel promotional demo:

https://github.com/user-attachments/assets/4dd060dc-53dd-4bb2-99a3-e65ab6f65166

Easel organizes its product experience around five connected workflows: **Discover** relevant trends and opportunities, **Plan** topics, hooks, scripts, and schedules, **Produce** text, audio, and video, **Publish** checked and platform-ready content directly to the appropriate platforms, and **Attribute** performance insights back to the account profile.

#### 📌 Usage Notes and Research Vision

> - **Use the Web workspace for the complete experience:** it includes conversations, assets, accounts, profiles, a content library, and publishing management beyond the CLI entry points, and it is our recommended way to use Easel; for terminal-only display quirks, see [Known Issues](docs/known-issues_EN.md).
> - **Be cautious with automated Xiaohongshu publishing:** automation may trigger verification, reach restrictions, or account risk. Use preview and preflight checks, and prefer human-confirmed publishing.
> - **Research applied to real life:** Easel brings our research into real social media workflows. We will continue exploring social intelligence for AI in social media, including a deeper understanding of creators, audiences, and authentic interaction.

## ✨ Why Easel?

- **A native text agent:** read and follow content Skills, create non-overwriting text artifacts, retain session history, and use the selected profile.
- **Profile-driven creation:** each account has its own positioning, style, audience, platforms, preferences, boundaries, and long-term memory.
- **A broad Skill library:** Easel includes writing, media, safety, and publishing guidance. Media-generation and publishing scripts remain direct user-operated workflows; the native text agent does not launch arbitrary skill scripts.
- **One source, many platforms:** adapt a single idea into Xiaohongshu cards, short video, a Zhihu article, or a short post while respecting platform conventions.
- **Project-based outputs:** source material, intermediate files, metadata, and final deliverables stay together for revision, retrying, and publishing.
- **Workbench publishing and analytics:** the existing account, publishing, calendar, and analytics pages remain available separately from the text agent loop.

## 🧭 Five-Layer Content Workflow

1. **Discover:** aggregate trending topics, industry news, competitors, and user conversations to identify relevant opportunities.
2. **Plan:** turn opportunities into topics, titles, scripts, content series, and calendar entries.
3. **Produce:** create copy, cards, posters, infographics, audio, video, short dramas, and paper explainers.
4. **Publish:** adapt titles, copy, aspect ratios, and media for each platform, run preflight checks, and publish through logged-in accounts.
5. **Attribute:** collect views, engagement, comments, and content performance, then preserve useful patterns in the account profile.

## 🧰 Implemented Capabilities

| Layer | Capabilities |
|---|---|
| **Discover** | Cross-platform trends, vertical research, content-gap analysis, event calendars, algorithm updates, competitor research, industry news, platform differences, RSS aggregation, and UGC discovery |
| **Plan** | Positioning, audience profiles, persona and voice, account diagnosis, content matrices, topic scoring, trend adaptation, series planning, hooks, outlines, storyboards, calendars, repurposing, livestreams, campaigns, and collaborations |
| **Text & Visual** | Social copy, video scripts, Xiaohongshu notes, long-form articles, novels, natural rewriting, style transfer, paper explainers, quote cards, knowledge cards, posters, infographics, charts, mind maps, comparison cards, product images, memes, AI images, enhancement, background removal, and batch processing |
| **Audio & Video** | Text-to-speech, multi-role dubbing, voice cloning, AI music, denoising, mixing, transcription, audio visualization, AI video, short drama, subtitles, translation, editing, clipping, highlights, format conversion, intros/outros, slideshows, beat sync, green screen, and video-to-article conversion |
| **Publish & Attribute** | Quality gates, risk checks, search optimization, publishing checklists, platform adaptation, seven-platform publishing workflows, calendar logging, account analytics, comment insights, postmortems, ROI, and profile memory |

## 🖥️ Workspace Examples

These are four representative examples, not the complete feature set. Explore the Skill library in the Web workspace or the [capability map](docs/skill-function-mapping.md) for more.

<table>
  <tr>
    <td width="50%" valign="top"><strong>🧬 Account Profiles</strong><br><sub>Build reusable account context from identity, social links, goals, preferences, and boundaries.</sub><br><br><img src="assets/readme/features/profile.png" width="100%" alt="Easel account profile"></td>
    <td width="50%" valign="top"><strong>🔥 Trend Radar</strong><br><sub>Aggregate real-time trends across major platforms and identify topics relevant to the current account.</sub><br><br><img src="assets/readme/features/discover.png" width="100%" alt="Easel trend radar"></td>
  </tr>
  <tr>
    <td width="50%" valign="top"><strong>📅 Content Calendar</strong><br><sub>Manage ideas, drafts, scheduled posts, published work, platform events, and daily plans.</sub><br><br><img src="assets/readme/features/calendar.png" width="100%" alt="Easel content calendar"></td>
    <td width="50%" valign="top"><strong>📣 Publishing Center</strong><br><sub>Generate platform-specific versions from one master asset, preview them, run checks, and publish.</sub><br><br><img src="assets/readme/features/publish.png" width="100%" alt="Easel publishing center"></td>
  </tr>
</table>

## 🖼️ Real Outputs

The following examples were produced by real Easel workflows. README media lives under `assets/readme/`; the project page uses lightweight six-second previews under `web/static/showcase/`.

### 📚 Paper Explainers and Knowledge Cards

<p align="center">
  <img src="assets/readme/showcase/spatialevo-cards-strip.jpg" width="49%" alt="SpatialEvo explainer cards">
  <img src="assets/readme/showcase/spatialladder-cards-strip.jpg" width="49%" alt="SpatialLadder explainer cards">
</p>
<p align="center">
  <img src="assets/readme/showcase/culture-mt-cards-strip.jpg" width="49%" alt="CULTURE-MT research cards">
  <img src="assets/readme/showcase/knowu-cards-strip.jpg" width="49%" alt="KnowU-Bench explainer cards">
</p>

### 📖 Novels and Stories

<p align="center">
  <img src="assets/readme/showcase/novel-xiuxian.png" width="24%" alt="Comedy cultivation story">
  <img src="assets/readme/showcase/novel-horror.png" width="24%" alt="Horror short story">
  <img src="assets/readme/showcase/novel-romance.png" width="24%" alt="Romantic comedy">
  <img src="assets/readme/showcase/novel-seventh.png" width="24%" alt="Suspense story">
</p>

### 🌿 Lifestyle and Meme Content

<p align="center">
  <img src="assets/readme/showcase/life-color-cards-strip.jpg" width="49%" alt="Colorful lifestyle cards">
  <img src="assets/readme/showcase/life-mountain-cards-strip.jpg" width="49%" alt="Nature cards">
</p>
<p align="center">
  <img src="assets/readme/showcase/life-chengdu-cards-strip.jpg" width="49%" alt="Chengdu lifestyle cards">
  <img src="assets/readme/showcase/jokes-cards-strip-wide.jpg" width="49%" alt="Meme cards">
</p>

### 🎬 Finished Videos

For faster browsing, each cover opens a lightweight preview of up to one minute. Use the links beneath each row for the full videos.

<p align="center">
  <a href="assets/readme/videos/preview/spatialladder-explainer.mp4"><img src="assets/readme/videos/thumbnails/spatialladder-explainer.jpg" width="49%" alt="Play SpatialLadder preview"></a>
  <a href="assets/readme/videos/preview/culture-mt-explainer.mp4"><img src="assets/readme/videos/thumbnails/culture-mt-explainer.jpg" width="49%" alt="Play CULTURE-MT preview"></a>
</p>
<p align="center"><sub>Full videos: <a href="assets/readme/videos/full/spatialladder-explainer.mp4">SpatialLadder</a> · <a href="assets/readme/videos/full/culture-mt-explainer.mp4">CULTURE-MT</a></sub></p>

<p align="center">
  <a href="assets/readme/videos/preview/ordinary-person.mp4"><img src="assets/readme/videos/thumbnails/ordinary-person.jpg" width="24%" alt="Play Ordinary Person preview"></a>
  <a href="assets/readme/videos/preview/hanako-change.mp4"><img src="assets/readme/videos/thumbnails/hanako-change.jpg" width="24%" alt="Play Hanako preview"></a>
  <a href="assets/readme/videos/preview/cyber-cultivation.mp4"><img src="assets/readme/videos/thumbnails/cyber-cultivation.jpg" width="24%" alt="Play cyber cultivation preview"></a>
  <a href="assets/readme/videos/preview/cyber-turtle.mp4"><img src="assets/readme/videos/thumbnails/cyber-turtle.jpg" width="24%" alt="Play cyber turtle preview"></a>
</p>
<p align="center"><sub>Full videos: <a href="assets/readme/videos/full/ordinary-person.mp4">Ordinary Person</a> · <a href="assets/readme/videos/full/hanako-change.mp4">Hanako's Change</a> · <a href="assets/readme/videos/full/cyber-cultivation.mp4">Cyber Cultivation</a> · <a href="assets/readme/videos/full/cyber-turtle.mp4">Cyber Turtle Mukbang</a></sub></p>

<p align="center">
  <a href="assets/readme/videos/preview/jilong-news.mp4"><img src="assets/readme/videos/thumbnails/jilong-news.jpg" width="32%" alt="Play Jilong news preview"></a>
  <a href="assets/readme/videos/preview/daomu-book.mp4"><img src="assets/readme/videos/thumbnails/daomu-book.jpg" width="32%" alt="Play Daomu Biji preview"></a>
  <a href="assets/readme/videos/preview/zju-intro.mp4"><img src="assets/readme/videos/thumbnails/zju-intro.jpg" width="32%" alt="Play Zhejiang University preview"></a>
</p>
<p align="center"><sub>Full videos: <a href="assets/readme/videos/full/jilong-news.mp4">Jilong Landslide News</a> · <a href="assets/readme/videos/full/daomu-book.mp4">Daomu Biji Introduction</a> · <a href="assets/readme/videos/full/zju-intro.mp4">Zhejiang University</a></sub></p>

## 🚀 Quick Start

Requirements: Linux or macOS, Python 3.10+, and Git. The installer checks Node.js 22.19+, FFmpeg, and Playwright/Chromium, and provides a platform-specific guide when Node.js is missing.

```bash
git clone https://github.com/ZJU-REAL/Easel.git
cd Easel
bash setup.sh
source .venv/bin/activate    # easel is installed in .venv; activate it first (Windows: .venv\Scripts\activate)
easel web
# Or: easel chat
```

> If you see `easel: command not found`, the virtual environment is not activated. You can also run it by full path without activating, e.g. `.venv/bin/easel doctor` (Windows: `.venv\Scripts\easel.exe doctor`).

`bash setup.sh` is a rerunnable guided installer. It creates Easel’s local runtime and does not install, launch, or configure OpenClaw. Configure a chat provider in Web model settings, or set model environment variables in `.env` for CLI use. Optional media providers remain configurable through `.env.example`.

Open `http://localhost:7860` for the Web workspace. Run `easel doctor` to check the environment and `easel ping` to inspect local provider configuration.

The installer installs the Python dependencies used by the Web UI, local media tools, and browser workflows:

```bash
pip install -e .
python -m playwright install chromium
# FFmpeg is also required on the system.
```

## ⚙️ Configuration

Configure the chat provider in the Web model settings or Easel's local provider store:

The Web model settings store credentials in `~/.easel/providers.json` with owner-only file permissions. `.env.example` remains available for CLI bootstrap and optional media skills; it also documents video, music, and voice provider settings. Configure only the capabilities you use. Missing media-provider credentials do not prevent chat, planning, or text creation.

| Capability | Configuration | Additional dependency |
|---|---|---|
| AI video | `VIDEO_PROVIDER` plus the provider key, URL, and model | A supported video service |
| AI music | `MUSIC_PROVIDER` plus provider settings | A supported music service |
| Cloud voice | `VOICE_PROVIDER` plus provider settings | A supported voice service |
| Local media processing | No model is required for supported local tools | FFmpeg |
| Browser publishing | Log in from the Web workspace's Accounts page | Playwright Chromium and valid platform accounts |

Never commit `.env`, cookies, or platform login state. Real publishing can be affected by verification, permissions, platform risk controls, and UI changes; use previews and checks for the first attempt.

## 🧩 Using Easel

| Command | Purpose |
|---|---|
| `easel web [--port 7860]` | Start the Web workspace |
| `easel chat` | Start a multi-turn terminal conversation and select an account profile |
| `easel skill <name> -i "..." [-p <profile>]` | Run a Skill directly; input may also be a file path |
| `easel doctor` | Check Python, Node.js, Skills, and essential configuration |
| `easel ping` | Check local provider configuration |


```bash
easel skill quality-gate -i "Review this social media post"
easel skill social-content -i "Write a post introducing spatial intelligence"
easel skill quality-gate -i "Review this draft" -p MyCreatorProfile
```

## 🧬 Account Profiles

Each profile is stored under `profiles/<name>/` and contains six dimensions: identity, style, audience, platforms, preferences and boundaries, and long-term memory.

```bash
cp -r profiles/_template "profiles/MyCreatorProfile"
```

Profiles can also be created and edited from the Web workspace.

## 🏗️ Project Structure

```text
Easel/
├── easel/                    Python CLI
├── web/                      FastAPI backend and React workspace
├── skills/openclaw/          Easel content Skills (legacy directory name)
├── skills/shared/            Shared scripts and references
├── assets/                   Brand, README media, and imported assets
├── profiles/                 Account profiles
├── outputs/                  Content projects and final deliverables
├── prompts/                  Native system prompts
└── docs/                     Specifications, capability map, and architecture docs
```

Easel does not depend on OpenClaw. The Web workspace listens on loopback at `127.0.0.1:7860` by default; set `EASEL_HOST` explicitly to select another interface. Model providers and session data live under `~/.easel/`. See the [native runtime guide](docs/native-runtime.md).

## 📑 Documentation

- [Capability map](docs/skill-function-mapping.md)
- [SKILL interface specification](docs/SKILL-SPEC.md)
- [Prompt and architecture layers](docs/prompt-stack.md)
- [Known issues](docs/known-issues_EN.md)
- [Full acknowledgments](docs/ACKNOWLEDGMENTS.md)

## 🗺️ Roadmap

Ordered by priority — contributions welcome; feel free to claim or add items via Issues/PRs:

- [ ] **1. Windows support** — Complete native Windows compatibility across installation, paths/encoding, and browser publishing.
- [ ] **2. Simpler installation** — Lower the barrier to entry with fewer manual steps and a smoother one-click setup.
- [ ] **3. Better in-app Agent UX** — Improve the Web workbench's chat interaction, loading logic, and streaming feedback.
- [ ] **4. More model providers and local runtimes** — Expand provider compatibility and offline options.

## 🙏 Acknowledgments

Easel's Skill system and workflows benefit from many excellent open-source projects, tools, and content methodologies. We thank their original authors and contributors. See the [full acknowledgments](docs/ACKNOWLEDGMENTS.md) for projects, usage, and license information.

Contributions and discussion are welcome. If you have ideas, questions, or improvements, feel free to open an Issue or PR — or scan the QR code to join our WeChat group:

<p align="center">
  <img src="assets/readme/wechat-group.png" width="240" alt="Easel WeChat group QR code">
</p>
<p align="center"><sub>Easel WeChat group · the QR code is refreshed periodically; if it has expired, reach us via Issues</sub></p>

### 🤝 Contributors

<table>
  <tr>
    <td align="center" width="84"><a href="https://github.com/lidingm"><img src="https://github.com/lidingm.png?size=96" width="72" height="72" alt="lidingm"><br><strong>lidingm</strong></a></td>
    <td align="center" width="84"><a href="https://github.com/qywMichelle"><img src="https://github.com/qywMichelle.png?size=96" width="72" height="72" alt="qywMichelle"><br><strong>qywMichelle</strong></a></td>
    <td align="center" width="84"><a href="https://github.com/wulinjuan"><img src="https://github.com/wulinjuan.png?size=96" width="72" height="72" alt="wulinjuan"><br><strong>wulinjuan</strong></a></td>
    <td align="center" width="84"><a href="https://github.com/arctanxarc"><img src="https://github.com/arctanxarc.png?size=96" width="72" height="72" alt="arctanxarc"><br><strong>arctanxarc</strong></a></td>
    <td align="center" width="84"><a href="https://github.com/mengyuyuan"><img src="https://github.com/mengyuyuan.png?size=96" width="72" height="72" alt="mengyuyuan"><br><strong>mengyuyuan</strong></a></td>
    <td align="center" width="84"><a href="https://github.com/Dear47"><img src="https://github.com/Dear47.png?size=96" width="72" height="72" alt="Dear47"><br><strong>Dear47</strong></a></td>
  </tr>
</table>

## ⚖️ License

[Apache 2.0](LICENSE)

## 🌟 Star History

<p align="center">
  <a href="https://star-history.com/#ZJU-REAL/Easel&Date">
    <img src="https://api.star-history.com/svg?repos=ZJU-REAL/Easel&type=Date" width="720" alt="Easel Star History Chart">
  </a>
</p>
