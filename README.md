<div align="center">

# ⃤ H A C K E D ⃤

### ✦ The Massive Tools Installer for Termux & Linux ✦

![Version](https://img.shields.io/badge/Version-2.0-198c6c?style=for-the-badge&logo=python&logoColor=white)
![Tools](https://img.shields.io/badge/Tools-919%20verified-2d4a2d?style=for-the-badge&logo=github&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Termux-ab3737?style=for-the-badge&logo=linux&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-8a6d3b?style=for-the-badge&logo=open-source-initiative&logoColor=white)

**Nine hundred nineteen tools. One installer. Zero dead links.**

Hacked turns 19,000 lines of copy-pasted shell menus into a clean catalog:
every repository verified live, every redirect followed, one generic install
engine — browse A–Z, by category, or search, and install with a single keypress.

</div>

---

## 📋 Table of Contents

- [🎯 Why Hacked?](#-why-hacked)
- [🧭 Tool Purpose](#-tool-purpose)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [✨ Features](#-features)
- [🔄 What Changed in v2.0](#-what-changed-in-v20)
- [🖥️ Preview](#️-preview)
- [🧰 Tech Stack](#-tech-stack)
- [⚠️ Disclaimer](#️-disclaimer)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [👨‍💻 Developer](#-developer)

---

## 🎯 Why Hacked?

> The original Hacked was a 19,000-line wall of ASCII art with ~1,000 raw
> `git clone` commands frozen in 2021. Today, 64 of those repositories are
> dead and 53 more have moved — v1 would silently fail or clone abandoned,
> unmaintained code.
>
> **Hacked v2.0 is the same idea, engineered properly.** Every URL was
> re-verified live before shipping, moved repositories were followed to their
> new homes, dead ones were dropped, and the whole thing runs on one generic
> install engine instead of a thousand copy-pasted functions.

---

## 🧭 Tool Purpose

Hacked exists to solve one problem well: **installing third-party security
tools without the homework**.

1. **A verified catalog** — 919 GitHub repositories, each checked live during
   the v2.0 build; redirects followed to current owners, dead links removed.
2. **Three ways to find a tool** — browse alphabetically (A–Z), browse by
   category (Wi-Fi, web, recon, passwords, exploitation, and more), or search
   by name with instant results.
3. **One consistent installer** — shallow clones into `~/Hacked-tools`,
   optional `install.sh`/`setup.sh` detection per tool, no duplicated logic.
4. **Batch operations** — install every tool in a filtered list with one
   confirmation, skip what's already present, and get a summary at the end.
5. **Stay current** — `Update installed tools` pulls the latest changes for
   everything you've cloned.

> **What it deliberately is not:** Hacked installs tools, it does not vouch
> for them. Each tool keeps its own license, quality level, and legal status —
> you choose what to run.

---

## 🚀 Quick Start

```bash
git clone https://github.com/MrHacker-X/Hacked.git
cd Hacked
bash setup.sh
python3 hacked.py
```

First run? Type `7` for the built-in **Doctor** — it verifies Python,
colorama, git and your network in one shot.

```bash
python3 hacked.py --doctor        # environment check
python3 hacked.py -v              # version
python3 hacked.py -s nmap         # search the catalog
python3 hacked.py -i Nikto        # install by exact name
```

---

## 📦 Installation

```bash
git clone https://github.com/MrHacker-X/Hacked.git
cd Hacked
bash setup.sh
python3 hacked.py
```

`setup.sh` detects your package manager automatically.

| Platform  | Status       | Notes                                   |
|-----------|--------------|-----------------------------------------|
| Kali      | ✅ Supported | apt detected natively                   |
| Ubuntu    | ✅ Supported | apt detected natively                   |
| Debian    | ✅ Supported | apt detected natively                   |
| Parrot    | ✅ Supported | apt detected natively                   |
| Arch      | ✅ Supported | pacman                                  |
| Fedora    | ✅ Supported | dnf                                     |
| openSUSE  | ✅ Supported | zypper                                  |
| Alpine    | ✅ Supported | apk                                     |
| Termux    | ✅ Supported | pkg, no root needed                     |
| Windows   | ⚠️ Partial   | script works; git installs vary         |

<details>
<summary><b>🔍 Manual installation (no script)</b></summary>

<br>

```bash
git clone https://github.com/MrHacker-X/Hacked.git
cd Hacked
python3 -m pip install --user colorama
python3 hacked.py
```

One Python dependency: `colorama`. Everything else is the standard library.
Without colorama the UI degrades to plain text instead of crashing.

</details>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗂️ **919 verified tools** | Every repository checked live at build time — 53 moved repos followed, 64 dead dropped |
| 🔤 **A–Z browsing** | All 26 letters populated, paginated 30-per-page with next/previous |
| 🏷️ **Category browse** | Wi-Fi, web, recon, passwords, exploitation, phishing, anonymity, forensics, social, utility |
| 🔎 **Instant search** | Substring match across the whole catalog, from the menu or `-s` flag |
| ⚙️ **One install engine** | Single generic `git clone --depth 1` path into `~/Hacked-tools` — no 1,000 copy-pasted functions |
| 📦 **Batch install** | `'all'` on any filtered list with one confirmation, per-tool progress, final summary |
| 🔄 **Update command** | Pulls latest for every installed tool in one pass |
| 🩺 **Doctor** | `--doctor` verifies python, colorama, git, package manager and network |
| 🛡️ **Safe exit** | Ctrl+C, EOF or `q` anywhere exits cleanly (code 130) — no tracebacks, no self-recursion |
| 🎨 **Typographic UI** | Block-letter banner, colorama palette, options-only menus — no ASCII-art escape hazards |

<details>
<summary><b>📖 Category breakdown</b></summary>

<br>

| Category | Tools |
|----------|-------|
| Web exploitation | 67 |
| Utility & environment | 63 |
| Exploitation | 51 |
| Social & bots | 50 |
| Password & hash | 44 |
| Phishing (authorized testing) | 24 |
| Wi-Fi & wireless | 23 |
| Recon & OSINT | 23 |
| Anonymity & tunneling | 23 |
| Forensics | 7 |
| General / uncategorized | 544 |

Categories are a navigation aid — search always covers all 919 tools.

</details>

---

## 🔄 What Changed in v2.0

| | v1.0 (0.98) | v2.0 |
|---|-------------|------|
| **Codebase** | 19,384 lines of menus + 1,011 copy-paste install functions | ~670 lines, one generic install engine + data table |
| **Catalog** | ~1,000 raw entries, 64 dead + 53 moved + 1 DMCA-blocked by 2026 | **919 verified live**, redirects followed, deduped |
| **Install-all** | 3,000-line sequential loop cloning everything unattended | Per-list batch with confirmation, progress and summary |
| **Navigation** | Only A–Z menus, one dead "[soon]" category menu | A–Z + 11 categories + search + pagination (n/p) |
| **Crash safety** | `os.system("python hacked.py")` self-recursion, `exit()` scattered | Central SafeExit, Ctrl+C/EOF/`q` clean (exit 130), errors caught per-screen |
| **Update support** | None — re-clone by hand | Built-in update pass over `~/Hacked-tools` |
| **UI** | Box-drawing ASCII art with broken escape mixtures | Block-letter wordmark, colorama palette, clean menus |
| **Setup** | None shipped | `setup.sh` with package-manager detection + verification |
| **CLI** | None | `-v/--version`, `--doctor`, `-s search`, `-i install` |
| **Social links** | "Connect With Us" menu | Removed — no Telegram/Instagram/YouTube links |

---

## 🖥️ Preview

<div align="center">
<img src="https://i.ibb.co/dJKpD6Yh/Screenshot-From-2026-09-30-23-54-36.png" alt="Hacked v2.0 main menu and doctor check" width="760">
</div>

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.8+ (standard library only) |
| Install engine | `subprocess` + `git clone --depth 1` |
| UI | colorama palette, auto-disabled on pipes/NO_COLOR |
| Catalog | Embedded verified JSON (919 entries) |
| Setup | Bash with pkg/apt/dnf/yum/pacman/zypper/apk detection |

---

## ⚠️ Disclaimer

> **1.** Hacked is an **installer**. It distributes third-party tools written
> by other authors and carries no warranty for any of them.
>
> **2.** You are responsible for what you install and run. Many bundled
> tools are for **authorized testing only** — attacking systems without
> explicit written permission is illegal almost everywhere.
>
> **3.** Review each tool's repository, license and purpose before use.
> Inclusion in this catalog is not an endorsement.
>
> **4.** The developer is not affiliated with the upstream tool authors and
> does not maintain their code.
>
> **5.** The developer assumes **no liability** for misuse or damage caused
> by this program. By using Hacked you accept full responsibility for your
> actions.

---

## 🤝 Contributing

Contributions are welcome — especially verified tool URLs for the catalog.

```bash
# 1. Fork the repository
# 2. Create your branch
git checkout -b feature/awesome-addition
# 3. Commit and push
git commit -m "Add: awesome addition"
git push origin feature/awesome-addition
# 4. Open a Pull Request
```

Found a dead tool URL or a bug? Open an [issue](https://github.com/MrHacker-X/Hacked/issues).

---

## 📜 License

This project is licensed under the **MIT License** — see
[LICENSE](LICENSE) for details.

---

## 👨‍💻 Developer

| | |
|---|---|
| **Developer** | MrHacker-X |
| **GitHub** | [github.com/MrHacker-X](https://github.com/MrHacker-X) |
| **Email** | contact@vritrasec.com |
| **Website** | [vritrasec.com](https://vritrasec.com) |
| **Network** | [link.vritrasec.com](https://link.vritrasec.com) |

---

<div align="center">

**⃤ Hacked ⃤** — *One installer. Every tool. Verified.*

⭐ **Found it useful? Star the repo — it keeps the catalog maintained.** ⭐

</div>
