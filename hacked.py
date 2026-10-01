#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hacked v2.0 - The Massive Tools Installer for Termux & Linux
Author  : MrHacker-X
Website : https://vritrasec.com
License : Boost Software License 1.0
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

try:
    from colorama import Fore, Style, init as colorama_init
except ImportError:
    Fore = Style = colorama_init = None

__version__ = "2.0"

# ============================================================
#  Appearance - colorama house palette
# ============================================================


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return os.environ.get("TERM") != "dumb"


try:
    HAVE_COLORAMA = colorama_init is not None
except NameError:
    HAVE_COLORAMA = False

COLOR = _supports_color() and HAVE_COLORAMA

if COLOR:
    colorama_init()

WH = Style.BRIGHT + Fore.WHITE if COLOR else ""
YL = Fore.LIGHTYELLOW_EX if COLOR else ""
GR = Fore.LIGHTGREEN_EX if COLOR else ""
DM = Style.DIM + Fore.WHITE if COLOR else ""
RD = Fore.LIGHTRED_EX if COLOR else ""
XX = Style.RESET_ALL if COLOR else ""


def _c(token: str, text: str) -> str:
    return f"{token}{text}{XX}" if token else text


PROG = os.path.basename(sys.argv[0]) or "hacked.py"
RULE = "─" * 62

EXIT_WORDS = {"q", "quit", "exit", "back"}
EXIT_HINT = "q to go back"


class SafeExit(Exception):
    """Raised when the user backs out of a prompt (EOF or exit keyword)."""


# ============================================================
#  UI helpers
# ============================================================


def rule():
    print(_c(DM, RULE))


def header(text: str):
    print()
    rule()
    print(_c(YL, f"  {text}"))
    rule()


def kv(key: str, val: str, width: int = 22):
    print(f"  {_c(YL, key.ljust(width))}{_c(WH, str(val))}")


def item(num: str, label: str, numw: int = 2):
    numcell = f"[{num}]".ljust(numw + 2)
    print(f"  {numcell} {_c(WH, label)}")


def say(text: str):
    print(f"  {_c(GR, '›')} {_c(WH, text)}")


def note(text: str):
    print(f"  {_c(DM, '·')} {_c(DM, text)}")


def err(text: str):
    print(f"  {_c(RD, '✗')} {_c(RD, text)}")


def warn(text: str):
    print(f"  {_c(YL, '!')} {_c(YL, text)}")


def ok(text: str):
    print(f"  {_c(GR, '✓')} {_c(GR, text)}")


def _clear():
    if sys.stdout.isatty():
        os.system("clear" if os.name != "nt" else "cls")


def ask(prompt: str, *, allow_empty: bool = False) -> str:
    while True:
        print()
        try:
            raw = input(f"  {_c(YL, '?')} {_c(WH, prompt)}: ")
        except (EOFError, KeyboardInterrupt):
            raise SafeExit
        val = raw.strip()
        if val.lower() in EXIT_WORDS:
            raise SafeExit
        if val or allow_empty:
            return val
        err("a value is required - type q to go back")


def confirm(prompt: str, *, default: bool = False) -> bool:
    try:
        raw = input(f"  {_c(YL, '?')} {_c(WH, prompt)} {_c(DM, '[y/N]' if not default else '[Y/n]')}: ")
    except (EOFError, KeyboardInterrupt):
        raise SafeExit
    val = raw.strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def pause(msg: str = "press enter to continue"):
    try:
        input(f"\n  {_c(DM, msg)}")
    except (EOFError, KeyboardInterrupt):
        raise SafeExit


# ============================================================
#  Block-letter wordmark
# ============================================================

_BLOCK_FONT = {
    "A": ["█▀█", "█▀█", "▀ ▀"],
    "B": ["██▄", "██▀", "▀▀▀"],
    "C": ["█▀▀", "█  ", "▀▀▀"],
    "D": ["█▄▀", "█ █", "▀▀▀"],
    "E": ["█▀▀", "█▀ ", "▀▀▀"],
    "F": ["█▀▀", "█▀ ", "▀  "],
    "G": ["█▀▀", "█ █", "▀▀▀"],
    "H": ["█ █", "█▀█", "▀ ▀"],
    "I": ["█", "█", "▀"],
    "J": [" █", " █", "▀▀"],
    "K": ["█ █", "██ ", "▀ ▀"],
    "L": ["█  ", "█  ", "▀▀▀"],
    "M": ["█▄█", "█ █", "▀ ▀"],
    "N": ["█▄ █", "█ ▀█", "▀  ▀"],
    "O": ["█▀█", "█ █", "▀▀▀"],
    "P": ["█▀█", "██▀", "▀  "],
    "Q": ["█▀█", "█▄█", "  ▀"],
    "R": ["█▀█", "██ ", "▀ ▀"],
    "S": ["█▀▀", "▀▀█", "▀▀▀"],
    "T": ["▀█▀", " █ ", " ▀ "],
    "U": ["█ █", "█ █", "▀▀▀"],
    "V": ["█ █", "█ █", " ▀ "],
    "W": ["█ █", "█▄█", "▀ ▀"],
    "X": ["█ █", " █ ", "▀ ▀"],
    "Y": ["█ █", " █ ", " ▀ "],
    "Z": ["▀▀█", " █ ", "▀▀▀"],
    " ": ["  ", "  ", "  "],
}


def _wordmark_rows(word: str) -> list:
    rows = ["", "", ""]
    for ch in word.upper():
        glyph = _BLOCK_FONT.get(ch, _BLOCK_FONT[" "])
        for i in range(3):
            rows[i] += glyph[i] + " "
    return rows  # uniform width - keeps centering aligned


BANNER_WIDTH = 62


def _center(text: str, width: int = BANNER_WIDTH) -> str:
    return text.center(width)


def banner():
    print()
    for row in _wordmark_rows("HACKED"):
        print(_c(YL, _center(row)))
    print()
    print(_c(WH, _center("The Massive Tools Installer for Termux & Linux")))
    print(_c(DM, _center("v2.0  ·  vritrasec.com")))
    print()
    print(_c(DM, RULE))
    print(_c(RD, _center("⚠  AUTHORIZED USE ONLY")))
    print(_c(DM, _center("review every tool's license & purpose before installing")))


# ============================================================
#  Tool catalog - verified dataset injected at build time
# ============================================================

TOOLS = json.loads(r"""[{"name":"-Mirai-Iot-BotNet","repo":"https://github.com/ruCyberPoison/-Mirai-Iot-BotNet","cat":"social"},{"name":"4nonimizer","repo":"https://github.com/Hackplayers/4nonimizer","cat":"anonymity"},{"name":"4wsectools","repo":"https://github.com/aryanrtm/4wsectools","cat":"utility"},{"name":"A-Rat","repo":"https://github.com/RexTheGod/A-Rat","cat":"exploit"},{"name":"A-xex","repo":"https://github.com/farinap5/A-xex","cat":"other"},{"name":"a2sv","repo":"https://github.com/hahwul/a2sv","cat":"other"},{"name":"ADB-Toolkit","repo":"https://github.com/ASHWIN990/ADB-Toolkit","cat":"other"},{"name":"admin-finder","repo":"https://github.com/the-c0d3r/admin-finder","cat":"other"},{"name":"admin-panel-finder","repo":"https://github.com/bdblackhat/admin-panel-finder","cat":"other"},{"name":"AdvPhishing","repo":"https://github.com/Ignitetch/AdvPhishing","cat":"phishing"},{"name":"afgcrack","repo":"https://github.com/htr-tech/afgcrack","cat":"password"},{"name":"air-hammer","repo":"https://github.com/Wh1t3Rh1n0/air-hammer","cat":"other"},{"name":"airgeddon","repo":"https://github.com/v1s1t0r1sh3r3/airgeddon","cat":"wifi"},{"name":"ajs2","repo":"https://github.com/arifistifik/ajs2","cat":"other"},{"name":"AndroBugs_Framework","repo":"https://github.com/AndroBugs/AndroBugs_Framework","cat":"other"},{"name":"android-malware","repo":"https://github.com/ashishb/android-malware","cat":"other"},{"name":"android-netspoof","repo":"https://github.com/w-shackleton/android-netspoof","cat":"other"},{"name":"AndroidBottomSheet","repo":"https://github.com/michael-rapp/AndroidBottomSheet","cat":"social"},{"name":"AndroidPINCrack","repo":"https://github.com/jselvi/AndroidPINCrack","cat":"password"},{"name":"Androspy","repo":"https://github.com/Cyb0r9/Androspy","cat":"other"},{"name":"Andspoilt","repo":"https://github.com/sundaysec/Andspoilt","cat":"other"},{"name":"angryFuzzer","repo":"https://github.com/ihebski/angryFuzzer","cat":"web"},{"name":"Anonymous","repo":"https://github.com/H1R0GH057/Anonymous","cat":"anonymity"},{"name":"ANRspam","repo":"https://github.com/Amriez/ANRspam","cat":"social"},{"name":"AOCDEFACE","repo":"https://github.com/Amriez/AOCDEFACE","cat":"other"},{"name":"aoctools","repo":"https://github.com/klittlepage/aoctools","cat":"utility"},{"name":"AOXdeface","repo":"https://github.com/Ranginang67/AOXdeface","cat":"other"},{"name":"apache2","repo":"https://github.com/ceph/apache2","cat":"other"},{"name":"Apk-Binder","repo":"https://github.com/kinghacker0/Apk-Binder","cat":"other"},{"name":"Apktool","repo":"https://github.com/iBotPeaches/Apktool","cat":"other"},{"name":"apm-agent-dotnet","repo":"https://github.com/elastic/apm-agent-dotnet","cat":"other"},{"name":"apsca","repo":"https://github.com/BlackHoleSecurity/apsca","cat":"other"},{"name":"apt2","repo":"https://github.com/tatanus/apt2","cat":"other"},{"name":"archcraft","repo":"https://github.com/archcraft-os/archcraft","cat":"utility"},{"name":"arp-scan","repo":"https://github.com/royhills/arp-scan","cat":"web"},{"name":"Artemis","repo":"https://github.com/ls1intum/Artemis","cat":"other"},{"name":"ASKT-AutoScriptKiddiesTool-","repo":"https://github.com/b3-v3r/ASKT-AutoScriptKiddiesTool-","cat":"other"},{"name":"AstraNmap","repo":"https://github.com/Gameye98/AstraNmap","cat":"recon"},{"name":"ASU","repo":"https://github.com/LOoLzeC/ASU","cat":"other"},{"name":"atlas","repo":"https://github.com/apache/atlas","cat":"other"},{"name":"atscan","repo":"https://github.com/MbarkT3STO/atscan","cat":"web"},{"name":"attifyos","repo":"https://github.com/adi0x90/attifyos","cat":"other"},{"name":"audit_couchdb","repo":"https://github.com/jhs/audit_couchdb","cat":"other"},{"name":"auto-ig","repo":"https://github.com/BladeKnife/auto-ig","cat":"other"},{"name":"auto-report-fb","repo":"https://github.com/jainudin01/auto-report-fb","cat":"other"},{"name":"Auto-Sender","repo":"https://github.com/mostafa272/Auto-Sender","cat":"other"},{"name":"autobackup","repo":"https://github.com/sbusso/autobackup","cat":"other"},{"name":"autoreaction-fb-android","repo":"https://github.com/HadiKhoirudin/autoreaction-fb-android","cat":"anonymity"},{"name":"AutoSploit","repo":"https://github.com/NullArray/AutoSploit","cat":"exploit"},{"name":"autotweet","repo":"https://github.com/JavedNissar/autotweet","cat":"other"},{"name":"AUXILE","repo":"https://github.com/0xlousie/AUXILE","cat":"other"},{"name":"Auxscan","repo":"https://github.com/Gameye98/Auxscan","cat":"web"},{"name":"avet","repo":"https://github.com/govolution/avet","cat":"other"},{"name":"awesome-docker","repo":"https://github.com/veggiemonk/awesome-docker","cat":"utility"},{"name":"Awesome-Hacking","repo":"https://github.com/Hack-with-Github/Awesome-Hacking","cat":"utility"},{"name":"awesome-termux-hacking","repo":"https://github.com/may215/awesome-termux-hacking","cat":"utility"},{"name":"awesome-web-hacking","repo":"https://github.com/infoslack/awesome-web-hacking","cat":"utility"},{"name":"b11","repo":"https://github.com/BotolMehedi/b11","cat":"other"},{"name":"BabyMux","repo":"https://github.com/syno3/BabyMux","cat":"other"},{"name":"backdoor-apk","repo":"https://github.com/dana-at-cp/backdoor-apk","cat":"exploit"},{"name":"BackTrack","repo":"https://github.com/swerdog/BackTrack","cat":"other"},{"name":"BAJINGANv6","repo":"https://github.com/DarknessCyberTeam/BAJINGANv6","cat":"other"},{"name":"BannerX","repo":"https://github.com/MrHacker-X/BannerX","cat":"utility"},{"name":"bash-ransomware","repo":"https://github.com/SubtleScope/bash-ransomware","cat":"other"},{"name":"bash2mp4","repo":"https://github.com/htr-tech/bash2mp4","cat":"other"},{"name":"BasicX","repo":"https://github.com/MrHacker-X/BasicX","cat":"other"},{"name":"battack","repo":"https://github.com/BotolMehedi/battack","cat":"other"},{"name":"bbqsql","repo":"https://github.com/CiscoCXSecurity/bbqsql","cat":"web"},{"name":"BCHackTool","repo":"https://github.com/ByCh4n/BCHackTool","cat":"other"},{"name":"bed","repo":"https://github.com/crunchsec/bed","cat":"other"},{"name":"beef","repo":"https://github.com/beefproject/beef","cat":"exploit"},{"name":"BeeLogger","repo":"https://github.com/4w4k3/BeeLogger","cat":"other"},{"name":"bettercap","repo":"https://github.com/bettercap/bettercap","cat":"other"},{"name":"BForce","repo":"https://github.com/YukersCreew/BForce","cat":"other"},{"name":"Binary-Exploitation","repo":"https://github.com/CodeMaxx/Binary-Exploitation","cat":"exploit"},{"name":"bing-ip2hosts","repo":"https://github.com/urbanadventurer/bing-ip2hosts","cat":"other"},{"name":"BinGoo","repo":"https://github.com/Hood3dRob1n/BinGoo","cat":"other"},{"name":"binwalk","repo":"https://github.com/ReFirmLabs/binwalk","cat":"other"},{"name":"bioinformatics-hacks","repo":"https://github.com/audy/bioinformatics-hacks","cat":"recon"},{"name":"bitcoin-all-key-generator","repo":"https://github.com/saracen/bitcoin-all-key-generator","cat":"anonymity"},{"name":"bitcoin-hacking-tools","repo":"https://github.com/SMH17/bitcoin-hacking-tools","cat":"utility"},{"name":"bitcoin-wallet","repo":"https://github.com/bitcoin-wallet/bitcoin-wallet","cat":"other"},{"name":"BitcoinUnlimited","repo":"https://github.com/BitcoinUnlimited/BitcoinUnlimited","cat":"other"},{"name":"Black-Hydra","repo":"https://github.com/Gameye98/Black-Hydra","cat":"password"},{"name":"blackarch","repo":"https://github.com/BlackArch/blackarch","cat":"utility"},{"name":"blackbox","repo":"https://github.com/StackExchange/blackbox","cat":"other"},{"name":"blackeye","repo":"https://github.com/An0nUD4Y/blackeye","cat":"phishing"},{"name":"BlackHydra","repo":"https://github.com/cyb3rt3ch/BlackHydra","cat":"password"},{"name":"blackmail","repo":"https://github.com/erenakkaya/blackmail","cat":"other"},{"name":"Blazy","repo":"https://github.com/s0md3v/Blazy","cat":"other"},{"name":"bleachbit","repo":"https://github.com/bleachbit/bleachbit","cat":"other"},{"name":"bluemaho","repo":"https://github.com/zenware/bluemaho","cat":"wifi"},{"name":"bluepot","repo":"https://github.com/andrewmichaelsmith/bluepot","cat":"wifi"},{"name":"Bolang","repo":"https://github.com/Amriez/Bolang","cat":"other"},{"name":"Bom","repo":"https://github.com/fab2s/Bom","cat":"other"},{"name":"Bom-Sms","repo":"https://github.com/zahidin/Bom-Sms","cat":"other"},{"name":"Bombers","repo":"https://github.com/bhattsameer/Bombers","cat":"other"},{"name":"BomberWhole","repo":"https://github.com/palahsu/BomberWhole","cat":"other"},{"name":"bombila","repo":"https://github.com/Snekyy/bombila","cat":"other"},{"name":"Boomhash","repo":"https://github.com/NixploitNexus/Boomhash","cat":"password"},{"name":"botline","repo":"https://github.com/treerachai/botline","cat":"social"},{"name":"Botnet","repo":"https://github.com/malwares/Botnet","cat":"social"},{"name":"BotTroxSelf","repo":"https://github.com/rhaiia/BotTroxSelf","cat":"social"},{"name":"BoxCoder","repo":"https://github.com/Xeit666h05t/BoxCoder","cat":"other"},{"name":"BoxCoderV.2","repo":"https://github.com/Xeit666h05t/BoxCoderV.2","cat":"other"},{"name":"BoxSpam","repo":"https://github.com/Xeit666h05t/BoxSpam","cat":"social"},{"name":"braa","repo":"https://github.com/mteg/braa","cat":"other"},{"name":"Breacher","repo":"https://github.com/s0md3v/Breacher","cat":"other"},{"name":"browser","repo":"https://github.com/dothq/browser","cat":"other"},{"name":"brut3k1t","repo":"https://github.com/Pedrowang/brut3k1t","cat":"password"},{"name":"Brutal","repo":"https://github.com/Screetsec/Brutal","cat":"password"},{"name":"Brute-force-gmail","repo":"https://github.com/0xfff0800/Brute-force-gmail","cat":"password"},{"name":"brutecms","repo":"https://github.com/moli1369/brutecms","cat":"web"},{"name":"brutespray","repo":"https://github.com/x90skysn3k/brutespray","cat":"password"},{"name":"BruteX","repo":"https://github.com/1N3/BruteX","cat":"password"},{"name":"BruteXSS-1","repo":"https://github.com/shawarkhanethicalhacker/BruteXSS-1","cat":"web"},{"name":"BTC-INR-live-chart","repo":"https://github.com/codeword7/BTC-INR-live-chart","cat":"other"},{"name":"bughunter","repo":"https://github.com/thehackingsage/bughunter","cat":"other"},{"name":"build-tools","repo":"https://github.com/weaveworks/build-tools","cat":"utility"},{"name":"bulk_extractor","repo":"https://github.com/simsong/bulk_extractor","cat":"anonymity"},{"name":"Bulltools","repo":"https://github.com/Bhai4You/Bulltools","cat":"utility"},{"name":"BW_Hacks","repo":"https://github.com/attilathedud/BW_Hacks","cat":"other"},{"name":"cameradar","repo":"https://github.com/Ullaakut/cameradar","cat":"other"},{"name":"CamPhish","repo":"https://github.com/techchipnet/CamPhish","cat":"phishing"},{"name":"CamStream-V3","repo":"https://github.com/SixQuant/CamStream-V3","cat":"other"},{"name":"CANtools","repo":"https://github.com/obrien28/CANtools","cat":"utility"},{"name":"capbreaker","repo":"https://github.com/ghsi10/capbreaker","cat":"other"},{"name":"capstone","repo":"https://github.com/capstone-engine/capstone","cat":"other"},{"name":"CapTipper","repo":"https://github.com/omriher/CapTipper","cat":"other"},{"name":"CarHackingTools","repo":"https://github.com/jgamblin/CarHackingTools","cat":"utility"},{"name":"catphish","repo":"https://github.com/ring0lab/catphish","cat":"phishing"},{"name":"cdpsnarf","repo":"https://github.com/Zapotek/cdpsnarf","cat":"other"},{"name":"CeWL","repo":"https://github.com/digininja/CeWL","cat":"other"},{"name":"CHAOS","repo":"https://github.com/tiagorlampert/CHAOS","cat":"exploit"},{"name":"ChatterBot","repo":"https://github.com/gunthercox/ChatterBot","cat":"social"},{"name":"choicebot","repo":"https://github.com/sreeram1211/choicebot","cat":"social"},{"name":"chrome-password-hacking","repo":"https://github.com/ronnieyego/chrome-password-hacking","cat":"password"},{"name":"chrooted-termux","repo":"https://github.com/Neo-Oli/chrooted-termux","cat":"exploit"},{"name":"CIAHackingTools","repo":"https://github.com/xiaoyanguoke/CIAHackingTools","cat":"utility"},{"name":"Cl0neMast3r","repo":"https://github.com/Abdulrah33m/Cl0neMast3r","cat":"other"},{"name":"cli","repo":"https://github.com/httpie/cli","cat":"other"},{"name":"Clickjacking-Tester","repo":"https://github.com/D4Vinci/Clickjacking-Tester","cat":"web"},{"name":"ClickNRoot","repo":"https://github.com/evait-security/ClickNRoot","cat":"exploit"},{"name":"CloneWeb","repo":"https://github.com/MrHacker-X/CloneWeb","cat":"other"},{"name":"CMSeeK","repo":"https://github.com/Tuhinshubhra/CMSeeK","cat":"web"},{"name":"CMSmap","repo":"https://github.com/Dionach/CMSmap","cat":"web"},{"name":"CNK-SPAM","repo":"https://github.com/hatakecnk/CNK-SPAM","cat":"social"},{"name":"CoD4_Hacks","repo":"https://github.com/attilathedud/CoD4_Hacks","cat":"other"},{"name":"codebreaker","repo":"https://github.com/babakhanov/codebreaker","cat":"other"},{"name":"commix","repo":"https://github.com/commixproject/commix","cat":"other"},{"name":"contexploit","repo":"https://github.com/BlackHoleSecurity/contexploit","cat":"exploit"},{"name":"cooker","repo":"https://github.com/genericmilk/cooker","cat":"other"},{"name":"Cookie-stealer","repo":"https://github.com/Xyl2k/Cookie-stealer","cat":"other"},{"name":"corner-shop","repo":"https://github.com/xpsurgery/corner-shop","cat":"other"},{"name":"COVID19-SIR","repo":"https://github.com/Lewuathe/COVID19-SIR","cat":"other"},{"name":"covid19-tracker-cli","repo":"https://github.com/OSSPhilippines/covid19-tracker-cli","cat":"other"},{"name":"cowpatty","repo":"https://github.com/joswr1ght/cowpatty","cat":"other"},{"name":"cpscan","repo":"https://github.com/SusmithKrishnan/cpscan","cat":"web"},{"name":"crackle","repo":"https://github.com/mikeryan/crackle","cat":"password"},{"name":"CrackMapExec","repo":"https://github.com/byt3bl33d3r/CrackMapExec","cat":"password"},{"name":"CrawlBox","repo":"https://github.com/abaykan/CrawlBox","cat":"web"},{"name":"CreaterVirus","repo":"https://github.com/runthee/CreaterVirus","cat":"other"},{"name":"creddump","repo":"https://github.com/moyix/creddump","cat":"forensics"},{"name":"credmap","repo":"https://github.com/lightos/credmap","cat":"other"},{"name":"CredSniper","repo":"https://github.com/ustayready/CredSniper","cat":"other"},{"name":"crewbot","repo":"https://github.com/marklarr/crewbot","cat":"social"},{"name":"Crips","repo":"https://github.com/Manisso/Crips","cat":"other"},{"name":"crowbar","repo":"https://github.com/galkan/crowbar","cat":"other"},{"name":"crunch","repo":"https://github.com/crunchsec/crunch","cat":"password"},{"name":"crydroid-1","repo":"https://github.com/rc-chuah/crydroid-1","cat":"other"},{"name":"csrf-poc-creator","repo":"https://github.com/rammarj/csrf-poc-creator","cat":"web"},{"name":"CTF-All-In-One","repo":"https://github.com/firmianay/CTF-All-In-One","cat":"other"},{"name":"ctfr","repo":"https://github.com/UnaPibaGeek/ctfr","cat":"other"},{"name":"cuckoo","repo":"https://github.com/cuckoosandbox/cuckoo","cat":"other"},{"name":"cupp","repo":"https://github.com/Mebus/cupp","cat":"password"},{"name":"CyberScan","repo":"https://github.com/medbenali/CyberScan","cat":"web"},{"name":"D-TECT","repo":"https://github.com/hudacbr/D-TECT","cat":"other"},{"name":"Daijoubu","repo":"https://github.com/nvaldeziii/Daijoubu","cat":"other"},{"name":"DarkFly-Tool","repo":"https://github.com/Ranginang67/DarkFly-Tool","cat":"other"},{"name":"DarkFly7","repo":"https://github.com/P3RT4M4/DarkFly7","cat":"other"},{"name":"DarkSploit","repo":"https://github.com/ykankaya/DarkSploit","cat":"exploit"},{"name":"darktile","repo":"https://github.com/liamg/darktile","cat":"other"},{"name":"datasploit","repo":"https://github.com/dvopsway/datasploit","cat":"exploit"},{"name":"dave","repo":"https://github.com/micromata/dave","cat":"other"},{"name":"dbd","repo":"https://github.com/gitdurandal/dbd","cat":"other"},{"name":"DbDat","repo":"https://github.com/foospidy/DbDat","cat":"other"},{"name":"ddos-hammer","repo":"https://github.com/rifandani/ddos-hammer","cat":"other"},{"name":"debian-server-tools","repo":"https://github.com/szepeviktor/debian-server-tools","cat":"utility"},{"name":"deblaze","repo":"https://github.com/SpiderLabs/deblaze","cat":"other"},{"name":"Decodify","repo":"https://github.com/s0md3v/Decodify","cat":"other"},{"name":"decompile","repo":"https://github.com/RANDIOLOY/decompile","cat":"other"},{"name":"deface","repo":"https://github.com/BDQ/deface","cat":"other"},{"name":"demiguise","repo":"https://github.com/nccgroup/demiguise","cat":"other"},{"name":"deployer","repo":"https://github.com/deployphp/deployer","cat":"other"},{"name":"deskcon-android","repo":"https://github.com/screenfreeze/deskcon-android","cat":"other"},{"name":"Devploit","repo":"https://github.com/GhettoCole/Devploit","cat":"other"},{"name":"devscripts","repo":"https://github.com/Debian/devscripts","cat":"other"},{"name":"dhcpdorf","repo":"https://github.com/mulbc/dhcpdorf","cat":"other"},{"name":"DHCPig","repo":"https://github.com/kamorin/DHCPig","cat":"other"},{"name":"Diamorphine","repo":"https://github.com/m0nad/Diamorphine","cat":"other"},{"name":"dirsearch","repo":"https://github.com/maurosoria/dirsearch","cat":"web"},{"name":"dirstalk","repo":"https://github.com/stefanoj3/dirstalk","cat":"other"},{"name":"distorm","repo":"https://github.com/gdabah/distorm","cat":"anonymity"},{"name":"Distributed-BitCoin-Miner","repo":"https://github.com/jahin07/Distributed-BitCoin-Miner","cat":"other"},{"name":"djangohunter","repo":"https://github.com/jimywork/djangohunter","cat":"other"},{"name":"DKMC","repo":"https://github.com/Mr-Un1k0d3r/DKMC","cat":"other"},{"name":"dmitry","repo":"https://github.com/jaygreig86/dmitry","cat":"recon"},{"name":"dnschef","repo":"https://github.com/iphelix/dnschef","cat":"web"},{"name":"dnsenum","repo":"https://github.com/fwaeytens/dnsenum","cat":"web"},{"name":"dnsmap","repo":"https://github.com/makefu/dnsmap","cat":"web"},{"name":"dnsrecon","repo":"https://github.com/darkoperator/dnsrecon","cat":"web"},{"name":"dnstwist","repo":"https://github.com/elceef/dnstwist","cat":"web"},{"name":"docker-vernemq","repo":"https://github.com/vernemq/docker-vernemq","cat":"other"},{"name":"dockerlabs","repo":"https://github.com/collabnix/dockerlabs","cat":"other"},{"name":"dockerscan","repo":"https://github.com/cr0hn/dockerscan","cat":"web"},{"name":"doona","repo":"https://github.com/wireghoul/doona","cat":"other"},{"name":"doork","repo":"https://github.com/AeonDave/doork","cat":"other"},{"name":"dos2unix","repo":"https://github.com/TizenTeam/dos2unix","cat":"other"},{"name":"dotdotpwn","repo":"https://github.com/wireghoul/dotdotpwn","cat":"other"},{"name":"dpgen","repo":"https://github.com/Venen0/dpgen","cat":"other"},{"name":"Dr0p1t-Framework","repo":"https://github.com/D4Vinci/Dr0p1t-Framework","cat":"other"},{"name":"Dracnmap","repo":"https://github.com/Screetsec/Dracnmap","cat":"recon"},{"name":"dronesploit","repo":"https://github.com/dronesploit/dronesploit","cat":"exploit"},{"name":"DSSS","repo":"https://github.com/stamparm/DSSS","cat":"other"},{"name":"DSVW","repo":"https://github.com/stamparm/DSVW","cat":"other"},{"name":"DSXS","repo":"https://github.com/stamparm/DSXS","cat":"other"},{"name":"dumpzilla","repo":"https://github.com/Busindre/dumpzilla","cat":"forensics"},{"name":"EagleEye","repo":"https://github.com/ThoughtfulDev/EagleEye","cat":"recon"},{"name":"eaphammer","repo":"https://github.com/s0lst1c3/eaphammer","cat":"wifi"},{"name":"EasY_HaCk","repo":"https://github.com/sabri-zaki/EasY_HaCk","cat":"other"},{"name":"EasyMap","repo":"https://github.com/iammert/EasyMap","cat":"other"},{"name":"EggShell","repo":"https://github.com/lucasjacks0n/EggShell","cat":"exploit"},{"name":"ehtools","repo":"https://github.com/ezequiel-ares1/ehtools","cat":"utility"},{"name":"elb-log-analyzer","repo":"https://github.com/ozantunca/elb-log-analyzer","cat":"other"},{"name":"elixir-tips","repo":"https://github.com/blackode/elixir-tips","cat":"other"},{"name":"elpscrk","repo":"https://github.com/D4Vinci/elpscrk","cat":"other"},{"name":"Email-Bomber","repo":"https://github.com/mohinparamasivam/Email-Bomber","cat":"other"},{"name":"Email-Spammer","repo":"https://github.com/complexpotato/Email-Spammer","cat":"social"},{"name":"Empire","repo":"https://github.com/EmpireProject/Empire","cat":"other"},{"name":"entropy","repo":"https://github.com/raphaelvallat/entropy","cat":"other"},{"name":"enum4linux","repo":"https://github.com/CiscoCXSecurity/enum4linux","cat":"recon"},{"name":"EQGRP","repo":"https://github.com/x0rz/EQGRP","cat":"other"},{"name":"eternal_scanner","repo":"https://github.com/peterpt/eternal_scanner","cat":"web"},{"name":"ettercap","repo":"https://github.com/Ettercap/ettercap","cat":"other"},{"name":"Evil-create-framework","repo":"https://github.com/LOoLzeC/Evil-create-framework","cat":"other"},{"name":"evilginx","repo":"https://github.com/kgretzky/evilginx","cat":"phishing"},{"name":"EvilURL","repo":"https://github.com/UndeadSec/EvilURL","cat":"other"},{"name":"evote","repo":"https://github.com/IBM/evote","cat":"other"},{"name":"exiftool","repo":"https://github.com/exiftool/exiftool","cat":"forensics"},{"name":"exploit-database","repo":"https://github.com/nsxz/exploit-database","cat":"exploit"},{"name":"exploitdb","repo":"https://github.com/offensive-security/exploitdb","cat":"exploit"},{"name":"ExploitOnCLI","repo":"https://github.com/r00tmars/ExploitOnCLI","cat":"exploit"},{"name":"exploits","repo":"https://github.com/bitsadmin/exploits","cat":"exploit"},{"name":"extra-phishing-pages","repo":"https://github.com/wifiphisher/extra-phishing-pages","cat":"phishing"},{"name":"extractTVpasswords","repo":"https://github.com/vah13/extractTVpasswords","cat":"password"},{"name":"extundelete","repo":"https://github.com/cherojeong/extundelete","cat":"forensics"},{"name":"EyeWitness","repo":"https://github.com/RedSiege/EyeWitness","cat":"other"},{"name":"ezsploit","repo":"https://github.com/rand0m1ze/ezsploit","cat":"exploit"},{"name":"F-Tools","repo":"https://github.com/FajarTheGGman/F-Tools","cat":"utility"},{"name":"fabrik","repo":"https://github.com/Fabrik/fabrik","cat":"other"},{"name":"Face-Hack","repo":"https://github.com/fcatae/Face-Hack","cat":"other"},{"name":"Facebook-BruteForce","repo":"https://github.com/IAmBlackHacker/Facebook-BruteForce","cat":"password"},{"name":"facebook-cracker","repo":"https://github.com/Ha3MrX/facebook-cracker","cat":"password"},{"name":"Facebook-Video-Downloader","repo":"https://github.com/vikas5914/Facebook-Video-Downloader","cat":"social"},{"name":"facenotify","repo":"https://github.com/cyweb/facenotify","cat":"other"},{"name":"fade","repo":"https://github.com/m-r-s/fade","cat":"other"},{"name":"fake-mailer","repo":"https://github.com/htr-tech/fake-mailer","cat":"phishing"},{"name":"FakeImageExploiter","repo":"https://github.com/r00t-3xp10it/FakeImageExploiter","cat":"exploit"},{"name":"faraday","repo":"https://github.com/infobyte/faraday","cat":"other"},{"name":"FastFileFinder","repo":"https://github.com/Wintellect/FastFileFinder","cat":"other"},{"name":"fb-bot-python","repo":"https://github.com/FBDevCLagos/fb-bot-python","cat":"social"},{"name":"fbht","repo":"https://github.com/chinoogawa/fbht","cat":"social"},{"name":"FBUPv2.0","repo":"https://github.com/Hendriyawan/FBUPv2.0","cat":"social"},{"name":"fbvid","repo":"https://github.com/Tuhinshubhra/fbvid","cat":"social"},{"name":"fern-wifi-cracker","repo":"https://github.com/savio-code/fern-wifi-cracker","cat":"wifi"},{"name":"FHX-Hash-Killer","repo":"https://github.com/FajriHidayat088/FHX-Hash-Killer","cat":"password"},{"name":"fi-cyberspace-scan","repo":"https://github.com/rtcrowley/fi-cyberspace-scan","cat":"web"},{"name":"fierce","repo":"https://github.com/mschwager/fierce","cat":"other"},{"name":"FiercePhish","repo":"https://github.com/Raikia/FiercePhish","cat":"phishing"},{"name":"FileVaultCracker","repo":"https://github.com/macmade/FileVaultCracker","cat":"password"},{"name":"fim","repo":"https://github.com/evrignaud/fim","cat":"other"},{"name":"findmyhash","repo":"https://github.com/frdmn/findmyhash","cat":"password"},{"name":"Findsploit","repo":"https://github.com/1N3/Findsploit","cat":"exploit"},{"name":"firefox-plugin-popup-logout","repo":"https://github.com/iniqua/firefox-plugin-popup-logout","cat":"other"},{"name":"FireWalk","repo":"https://github.com/mart1n/FireWalk","cat":"other"},{"name":"flood","repo":"https://github.com/jesec/flood","cat":"other"},{"name":"fluxion","repo":"https://github.com/FluxionNetwork/fluxion","cat":"wifi"},{"name":"FMD","repo":"https://github.com/riderkick/FMD","cat":"other"},{"name":"fonts","repo":"https://github.com/opensourcedesign/fonts","cat":"utility"},{"name":"foremost","repo":"https://github.com/jonstewart/foremost","cat":"other"},{"name":"found","repo":"https://github.com/4Catalyzer/found","cat":"other"},{"name":"foxcontact","repo":"https://github.com/demis-palma/foxcontact","cat":"other"},{"name":"fragroute","repo":"https://github.com/ajkeeton/fragroute","cat":"other"},{"name":"FragRouter","repo":"https://github.com/foxbunny/FragRouter","cat":"other"},{"name":"FRat","repo":"https://github.com/raxorend/FRat","cat":"exploit"},{"name":"Free-Security-eBooks","repo":"https://github.com/Hack-with-Github/Free-Security-eBooks","cat":"other"},{"name":"fsociety","repo":"https://github.com/Manisso/fsociety","cat":"other"},{"name":"fuckshitup","repo":"https://github.com/Smaash/fuckshitup","cat":"other"},{"name":"fuxploider","repo":"https://github.com/almandin/fuxploider","cat":"other"},{"name":"GadoGado","repo":"https://github.com/pratamawijaya/GadoGado","cat":"other"},{"name":"games","repo":"https://github.com/leereilly/games","cat":"other"},{"name":"gasmask","repo":"https://github.com/twelvesec/gasmask","cat":"other"},{"name":"gcat","repo":"https://github.com/byt3bl33d3r/gcat","cat":"other"},{"name":"gcc","repo":"https://github.com/gcc-mirror/gcc","cat":"other"},{"name":"gcospam","repo":"https://github.com/Amriez/gcospam","cat":"social"},{"name":"gdog","repo":"https://github.com/maldevel/gdog","cat":"other"},{"name":"Gemail-Hack","repo":"https://github.com/Ha3MrX/Gemail-Hack","cat":"other"},{"name":"generatorktpkk","repo":"https://github.com/aayid/generatorktpkk","cat":"anonymity"},{"name":"GenVirus","repo":"https://github.com/sowmiksudo/GenVirus","cat":"other"},{"name":"ghost-phisher","repo":"https://github.com/savio-code/ghost-phisher","cat":"phishing"},{"name":"ghost-updater","repo":"https://github.com/ziggornif/ghost-updater","cat":"other"},{"name":"GINF","repo":"https://github.com/Gameye98/GINF","cat":"other"},{"name":"giskismet","repo":"https://github.com/xtr4nge/giskismet","cat":"other"},{"name":"git_psibot_hacking","repo":"https://github.com/psibot/git_psibot_hacking","cat":"social"},{"name":"GitDorker","repo":"https://github.com/obheda12/GitDorker","cat":"recon"},{"name":"github-email","repo":"https://github.com/paulirish/github-email","cat":"other"},{"name":"githubstats","repo":"https://github.com/akerl/githubstats","cat":"other"},{"name":"givemeakey","repo":"https://github.com/geovedi/givemeakey","cat":"other"},{"name":"Gloom-Framework","repo":"https://github.com/StreetSec/Gloom-Framework","cat":"other"},{"name":"GLTools","repo":"https://github.com/HazimGazov/GLTools","cat":"utility"},{"name":"go-btn","repo":"https://github.com/KnutZuidema/go-btn","cat":"other"},{"name":"go-exploitdb","repo":"https://github.com/vulsio/go-exploitdb","cat":"exploit"},{"name":"GoblinWordGenerator","repo":"https://github.com/UndeadSec/GoblinWordGenerator","cat":"anonymity"},{"name":"GoBot2","repo":"https://github.com/SaturnsVoid/GoBot2","cat":"social"},{"name":"gobuster","repo":"https://github.com/OJ/gobuster","cat":"web"},{"name":"GoldenEye","repo":"https://github.com/jseidl/GoldenEye","cat":"other"},{"name":"golismero","repo":"https://github.com/golismero/golismero","cat":"other"},{"name":"goofile","repo":"https://github.com/sosukeinu/goofile","cat":"other"},{"name":"gps","repo":"https://github.com/cbfinn/gps","cat":"other"},{"name":"grab","repo":"https://github.com/lorien/grab","cat":"other"},{"name":"grabcam","repo":"https://github.com/noob-hackers/grabcam","cat":"other"},{"name":"graphql-platform","repo":"https://github.com/ChilliCream/graphql-platform","cat":"other"},{"name":"GreenReaper","repo":"https://github.com/Amriez/GreenReaper","cat":"other"},{"name":"grepmail","repo":"https://github.com/coppit/grepmail","cat":"other"},{"name":"h4rpy","repo":"https://github.com/MS-WEB-BN/h4rpy","cat":"wifi"},{"name":"HAC","repo":"https://github.com/kaskr/HAC","cat":"other"},{"name":"hack-tools","repo":"https://github.com/hacktoolspack/hack-tools","cat":"utility"},{"name":"hack-typeracer","repo":"https://github.com/nwochaadim/hack-typeracer","cat":"other"},{"name":"HackBar","repo":"https://github.com/d3vilbug/HackBar","cat":"other"},{"name":"hacker-roadmap","repo":"https://github.com/sundowndev/hacker-roadmap","cat":"utility"},{"name":"hacker101","repo":"https://github.com/Hacker0x01/hacker101","cat":"other"},{"name":"Hacking","repo":"https://github.com/Ha3MrX/Hacking","cat":"utility"},{"name":"Hacking-Tools-Repository","repo":"https://github.com/Gexos/Hacking-Tools-Repository","cat":"anonymity"},{"name":"hackingtool","repo":"https://github.com/Z4nzu/hackingtool","cat":"other"},{"name":"HackingTools","repo":"https://github.com/Laxa/HackingTools","cat":"utility"},{"name":"hacklock","repo":"https://github.com/noob-hackers/hacklock","cat":"other"},{"name":"hacktronian","repo":"https://github.com/thehackingsage/hacktronian","cat":"other"},{"name":"hakkuframework","repo":"https://github.com/4shadoww/hakkuframework","cat":"other"},{"name":"hale","repo":"https://github.com/halestudio/hale","cat":"other"},{"name":"hammer","repo":"https://github.com/cyweb/hammer","cat":"other"},{"name":"Hash-Buster","repo":"https://github.com/s0md3v/Hash-Buster","cat":"password"},{"name":"hash-generator","repo":"https://github.com/0xlousie/hash-generator","cat":"password"},{"name":"hashcat","repo":"https://github.com/hashcat/hashcat","cat":"password"},{"name":"hasher","repo":"https://github.com/0xlousie/hasher","cat":"password"},{"name":"hasherdotid","repo":"https://github.com/galauerscrew/hasherdotid","cat":"password"},{"name":"hashID","repo":"https://github.com/psypanda/hashID","cat":"password"},{"name":"hat.sh","repo":"https://github.com/sh-dv/hat.sh","cat":"other"},{"name":"Hatch","repo":"https://github.com/zshell/Hatch","cat":"other"},{"name":"HatCloud","repo":"https://github.com/HatBashBR/HatCloud","cat":"other"},{"name":"haxorbd","repo":"https://github.com/htr-tech/haxorbd","cat":"other"},{"name":"haxRat","repo":"https://github.com/Hax4us/haxRat","cat":"exploit"},{"name":"hbxss","repo":"https://github.com/hahwul/hbxss","cat":"web"},{"name":"Heartbleed","repo":"https://github.com/FiloSottile/Heartbleed","cat":"other"},{"name":"HERCULES","repo":"https://github.com/EgeBalci/HERCULES","cat":"other"},{"name":"hhvm","repo":"https://github.com/facebook/hhvm","cat":"other"},{"name":"HiddenEye","repo":"https://github.com/yevgen2020/HiddenEye","cat":"phishing"},{"name":"Hijacker","repo":"https://github.com/chrisk44/Hijacker","cat":"wifi"},{"name":"host","repo":"https://github.com/htr-tech/host","cat":"other"},{"name":"hostchecker","repo":"https://github.com/h5vx/hostchecker","cat":"other"},{"name":"HPAS1369","repo":"https://github.com/DedSecCyber/HPAS1369","cat":"other"},{"name":"hping","repo":"https://github.com/antirez/hping","cat":"other"},{"name":"HT-WPS-Breaker","repo":"https://github.com/SilentGhostX/HT-WPS-Breaker","cat":"wifi"},{"name":"htools","repo":"https://github.com/htools/htools","cat":"utility"},{"name":"https-github.com-cr4shcod3-pureblood","repo":"https://github.com/ChesZy2810/https-github.com-cr4shcod3-pureblood","cat":"web"},{"name":"httptunnel","repo":"https://github.com/larsbrinkhoff/httptunnel","cat":"web"},{"name":"hue","repo":"https://github.com/cloudera/hue","cat":"other"},{"name":"hugo","repo":"https://github.com/gohugoio/hugo","cat":"other"},{"name":"hulk","repo":"https://github.com/grafov/hulk","cat":"other"},{"name":"Hunner","repo":"https://github.com/b3-v3r/Hunner","cat":"other"},{"name":"hurl","repo":"https://github.com/Orange-OpenSource/hurl","cat":"other"},{"name":"hydra","repo":"https://github.com/hydra-ecosystem/hydra","cat":"password"},{"name":"I-See-You","repo":"https://github.com/Viralmaniar/I-See-You","cat":"other"},{"name":"icebreaker","repo":"https://github.com/icebreaker-fpga/icebreaker","cat":"other"},{"name":"ICG-AutoExploiterBoT","repo":"https://github.com/IO1337/ICG-AutoExploiterBoT","cat":"exploit"},{"name":"iconv","repo":"https://github.com/processone/iconv","cat":"other"},{"name":"iesDEFACE","repo":"https://github.com/ALX-04/iesDEFACE","cat":"other"},{"name":"iesInstall","repo":"https://github.com/ALX-04/iesInstall","cat":"social"},{"name":"IFC","repo":"https://github.com/buildingSMART/IFC","cat":"other"},{"name":"ig-spammer","repo":"https://github.com/thebashfile/ig-spammer","cat":"social"},{"name":"ighack","repo":"https://github.com/noob-hackers/ighack","cat":"other"},{"name":"IGP","repo":"https://github.com/cran/IGP","cat":"other"},{"name":"igtools","repo":"https://github.com/arief125/igtools","cat":"utility"},{"name":"imgui","repo":"https://github.com/ocornut/imgui","cat":"other"},{"name":"indi_bidsification","repo":"https://github.com/FCP-INDI/indi_bidsification","cat":"other"},{"name":"indonesian-nlp-playground","repo":"https://github.com/phillette/indonesian-nlp-playground","cat":"other"},{"name":"indonesian-wordlist","repo":"https://github.com/geovedi/indonesian-wordlist","cat":"password"},{"name":"infect","repo":"https://github.com/noob-hackers/infect","cat":"other"},{"name":"Infosec_Reference","repo":"https://github.com/rmusser01/Infosec_Reference","cat":"recon"},{"name":"inmux","repo":"https://github.com/Amriez/inmux","cat":"other"},{"name":"inshackle","repo":"https://github.com/xd20111/inshackle","cat":"other"},{"name":"InSpy","repo":"https://github.com/jobroche/InSpy","cat":"other"},{"name":"instabot.py","repo":"https://github.com/jaguar754/instabot.py","cat":"social"},{"name":"InstaBrute","repo":"https://github.com/Ha3MrX/InstaBrute","cat":"password"},{"name":"instagram_private_api","repo":"https://github.com/ping/instagram_private_api","cat":"social"},{"name":"instahack","repo":"https://github.com/evildevill/instahack","cat":"social"},{"name":"instainsane","repo":"https://github.com/umeshshinde19/instainsane","cat":"social"},{"name":"instashell","repo":"https://github.com/maxrooted/instashell","cat":"exploit"},{"name":"inther","repo":"https://github.com/Gameye98/inther","cat":"other"},{"name":"intrace","repo":"https://github.com/robertswiecki/intrace","cat":"other"},{"name":"inurlbr-scanner","repo":"https://github.com/MrMugiwara/inurlbr-scanner","cat":"web"},{"name":"ip-thrower","repo":"https://github.com/UmutAlihan/ip-thrower","cat":"other"},{"name":"IP-Tracker","repo":"https://github.com/anonymousproo/IP-Tracker","cat":"other"},{"name":"ipdrone","repo":"https://github.com/noob-hackers/ipdrone","cat":"other"},{"name":"IPGeoLocation","repo":"https://github.com/maldevel/IPGeoLocation","cat":"other"},{"name":"IPLocator","repo":"https://github.com/MichaelDim02/IPLocator","cat":"anonymity"},{"name":"ipmux","repo":"https://github.com/Amriez/ipmux","cat":"other"},{"name":"ipscan","repo":"https://github.com/angryip/ipscan","cat":"web"},{"name":"ismtp","repo":"https://github.com/crunchsec/ismtp","cat":"other"},{"name":"iwmap","repo":"https://github.com/guelfoweb/iwmap","cat":"other"},{"name":"jack","repo":"https://github.com/uclnlp/jack","cat":"other"},{"name":"jadwal-sholat","repo":"https://github.com/nmfzone/jadwal-sholat","cat":"other"},{"name":"jboss-autopwn","repo":"https://github.com/SpiderLabs/jboss-autopwn","cat":"other"},{"name":"jdvd","repo":"https://github.com/telekomancer/jdvd","cat":"other"},{"name":"jexboss","repo":"https://github.com/joaomatosf/jexboss","cat":"other"},{"name":"john","repo":"https://github.com/openwall/john","cat":"password"},{"name":"johnny","repo":"https://github.com/openwall/johnny","cat":"password"},{"name":"joomscan","repo":"https://github.com/OWASP/joomscan","cat":"web"},{"name":"jsql-injection","repo":"https://github.com/ron190/jsql-injection","cat":"web"},{"name":"JTRE","repo":"https://github.com/ASHWIN990/JTRE","cat":"other"},{"name":"jwt-cracker","repo":"https://github.com/lmammino/jwt-cracker","cat":"password"},{"name":"K8CScan","repo":"https://github.com/k8gege/K8CScan","cat":"web"},{"name":"kali-nethunter","repo":"https://github.com/offensive-security/kali-nethunter","cat":"utility"},{"name":"kalibrate-rtl","repo":"https://github.com/steve-m/kalibrate-rtl","cat":"utility"},{"name":"kalimux","repo":"https://github.com/noob-hackers/kalimux","cat":"utility"},{"name":"kalin-test","repo":"https://github.com/knikolov-at-paypal/kalin-test","cat":"utility"},{"name":"Katak","repo":"https://github.com/Gameye98/Katak","cat":"other"},{"name":"KatanaFramework","repo":"https://github.com/PowerScript/KatanaFramework","cat":"other"},{"name":"katoolin","repo":"https://github.com/LionSec/katoolin","cat":"other"},{"name":"Kawai-Botnet","repo":"https://github.com/Gameye98/Kawai-Botnet","cat":"social"},{"name":"keimpx","repo":"https://github.com/nccgroup/keimpx","cat":"other"},{"name":"kekescan","repo":"https://github.com/v1cker/kekescan","cat":"web"},{"name":"KFC","repo":"https://github.com/Malfoy/KFC","cat":"other"},{"name":"kickthemout","repo":"https://github.com/k4m4/kickthemout","cat":"other"},{"name":"killchain","repo":"https://github.com/ruped24/killchain","cat":"other"},{"name":"killer-sudoku","repo":"https://github.com/amnn/killer-sudoku","cat":"other"},{"name":"killerbee","repo":"https://github.com/riverloopsec/killerbee","cat":"other"},{"name":"killr","repo":"https://github.com/whackashoe/killr","cat":"other"},{"name":"killshot","repo":"https://github.com/bahaabdelwahed/killshot","cat":"other"},{"name":"king-phisher","repo":"https://github.com/CrimsonForge-io/king-phisher","cat":"phishing"},{"name":"KitHack","repo":"https://github.com/AdrMXR/KitHack","cat":"other"},{"name":"kitty-cat","repo":"https://github.com/adi1090x/kitty-cat","cat":"other"},{"name":"KnockMail","repo":"https://github.com/4w4k3/KnockMail","cat":"web"},{"name":"knockpy","repo":"https://github.com/guelfoweb/knockpy","cat":"web"},{"name":"komodo","repo":"https://github.com/jl777/komodo","cat":"other"},{"name":"kubik-bot","repo":"https://github.com/wakhidulkhoiri/kubik-bot","cat":"social"},{"name":"kwetza","repo":"https://github.com/sensepost/kwetza","cat":"other"},{"name":"lazada","repo":"https://github.com/yoolk/lazada","cat":"other"},{"name":"Lazy-RDP","repo":"https://github.com/getdrive/Lazy-RDP","cat":"other"},{"name":"lazybee","repo":"https://github.com/noob-hackers/lazybee","cat":"other"},{"name":"lazygit","repo":"https://github.com/jesseduffield/lazygit","cat":"other"},{"name":"Lazymux","repo":"https://github.com/Gameye98/Lazymux","cat":"other"},{"name":"learn-python","repo":"https://github.com/trekhleb/learn-python","cat":"other"},{"name":"leet1998","repo":"https://github.com/BlackHoleSecurity/leet1998","cat":"other"},{"name":"leviathan","repo":"https://github.com/utkusen/leviathan","cat":"other"},{"name":"LFISuite","repo":"https://github.com/D35m0nd142/LFISuite","cat":"web"},{"name":"libzc","repo":"https://github.com/mferland/libzc","cat":"other"},{"name":"linset","repo":"https://github.com/vk496/linset","cat":"other"},{"name":"linux","repo":"https://github.com/torvalds/linux","cat":"utility"},{"name":"lists","repo":"https://github.com/jnv/lists","cat":"other"},{"name":"LITEDDOS","repo":"https://github.com/4L13199/LITEDDOS","cat":"other"},{"name":"LITEFONT","repo":"https://github.com/4L13199/LITEFONT","cat":"utility"},{"name":"LiteOTP","repo":"https://github.com/Cvar1984/LiteOTP","cat":"other"},{"name":"LiteScript","repo":"https://github.com/luciotato/LiteScript","cat":"other"},{"name":"LITESPAM","repo":"https://github.com/4L13199/LITESPAM","cat":"social"},{"name":"LITETOOLS","repo":"https://github.com/4L13199/LITETOOLS","cat":"utility"},{"name":"lockphish","repo":"https://github.com/JasonJerry/lockphish","cat":"phishing"},{"name":"logger","repo":"https://github.com/dolab/logger","cat":"other"},{"name":"login-server","repo":"https://github.com/gbv/login-server","cat":"other"},{"name":"loveTools","repo":"https://github.com/ALX-04/loveTools","cat":"utility"},{"name":"lscript","repo":"https://github.com/arismelachroinos/lscript","cat":"other"},{"name":"lucky","repo":"https://github.com/luckyframework/lucky","cat":"other"},{"name":"lynis","repo":"https://github.com/CISOfy/lynis","cat":"other"},{"name":"m-wiz","repo":"https://github.com/noob-hackers/m-wiz","cat":"other"},{"name":"mac-lookup","repo":"https://github.com/ivan-loh/mac-lookup","cat":"other"},{"name":"macphish","repo":"https://github.com/cldrn/macphish","cat":"phishing"},{"name":"mailer-cli","repo":"https://github.com/pedro-stanaka/mailer-cli","cat":"other"},{"name":"Malicious","repo":"https://github.com/TheReaper167/Malicious","cat":"other"},{"name":"malware","repo":"https://github.com/RamadhanAmizudin/malware","cat":"other"},{"name":"Mamangkey","repo":"https://github.com/Amriez/Mamangkey","cat":"other"},{"name":"maskprocessor","repo":"https://github.com/hashcat/maskprocessor","cat":"other"},{"name":"masscan","repo":"https://github.com/robertdavidgraham/masscan","cat":"web"},{"name":"matahari","repo":"https://github.com/jhudsl/matahari","cat":"other"},{"name":"MaterialFBook","repo":"https://github.com/ZeeRooo/MaterialFBook","cat":"other"},{"name":"MaxSubdoFinder","repo":"https://github.com/exlinee/MaxSubdoFinder","cat":"other"},{"name":"MBF","repo":"https://github.com/MaulanaRyM/MBF","cat":"other"},{"name":"MBomb","repo":"https://github.com/palahsu/MBomb","cat":"other"},{"name":"MD5-Cracker","repo":"https://github.com/recepgunes1/MD5-Cracker","cat":"password"},{"name":"MediaInfo","repo":"https://github.com/MediaArea/MediaInfo","cat":"recon"},{"name":"Mega-Bot","repo":"https://github.com/aron-tn/Mega-Bot","cat":"social"},{"name":"meisha-ui","repo":"https://github.com/meishaFE/meisha-ui","cat":"other"},{"name":"mercury","repo":"https://github.com/cisco/mercury","cat":"other"},{"name":"Mesos-Bitcoin-Miner","repo":"https://github.com/derekchiang/Mesos-Bitcoin-Miner","cat":"other"},{"name":"meTAInstall","repo":"https://github.com/4L13199/meTAInstall","cat":"social"},{"name":"metasploit-framework","repo":"https://github.com/rapid7/metasploit-framework","cat":"exploit"},{"name":"Meterpreter_Paranoid_Mode-SSL","repo":"https://github.com/r00t-3xp10it/Meterpreter_Paranoid_Mode-SSL","cat":"other"},{"name":"mfcuk","repo":"https://github.com/nfc-tools/mfcuk","cat":"other"},{"name":"mfoc","repo":"https://github.com/nfc-tools/mfoc","cat":"other"},{"name":"mfterm","repo":"https://github.com/4ZM/mfterm","cat":"other"},{"name":"MHDDoS","repo":"https://github.com/MatrixTM/MHDDoS","cat":"other"},{"name":"MikrotikSploit","repo":"https://github.com/0x802/MikrotikSploit","cat":"exploit"},{"name":"Mirai-Source-Code","repo":"https://github.com/jgamblin/Mirai-Source-Code","cat":"other"},{"name":"mitmAP","repo":"https://github.com/xdavidhu/mitmAP","cat":"other"},{"name":"MITMf","repo":"https://github.com/byt3bl33d3r/MITMf","cat":"other"},{"name":"mitmproxy","repo":"https://github.com/mitmproxy/mitmproxy","cat":"anonymity"},{"name":"mongoaudit","repo":"https://github.com/stampery/mongoaudit","cat":"other"},{"name":"morpheus","repo":"https://github.com/r00t-3xp10it/morpheus","cat":"other"},{"name":"movies-for-hackers","repo":"https://github.com/k4m4/movies-for-hackers","cat":"other"},{"name":"Mr.Rv1.1","repo":"https://github.com/Mr-R225/Mr.Rv1.1","cat":"other"},{"name":"Mr.Rv2","repo":"https://github.com/Mr-R225/Mr.Rv2","cat":"other"},{"name":"Mr.SIP","repo":"https://github.com/meliht/Mr.SIP","cat":"other"},{"name":"mrphish","repo":"https://github.com/noob-hackers/mrphish","cat":"phishing"},{"name":"msfpc","repo":"https://github.com/g0tmi1k/msfpc","cat":"exploit"},{"name":"multi-SpaM","repo":"https://github.com/tdencker/multi-SpaM","cat":"social"},{"name":"Multilang-fork-bombs","repo":"https://github.com/sigmamale1980/Multilang-fork-bombs","cat":"other"},{"name":"multimon-ng","repo":"https://github.com/EliasOenal/multimon-ng","cat":"other"},{"name":"mx-tools","repo":"https://github.com/AdrianTM/mx-tools","cat":"utility"},{"name":"my-first-bitcoin-miner","repo":"https://github.com/philipperemy/my-first-bitcoin-miner","cat":"other"},{"name":"My-Tools","repo":"https://github.com/TheSploit/My-Tools","cat":"utility"},{"name":"myenc","repo":"https://github.com/Sofik6649/myenc","cat":"other"},{"name":"MyServer","repo":"https://github.com/rajkumardusad/MyServer","cat":"other"},{"name":"Namechk","repo":"https://github.com/GONZOsint/Namechk","cat":"other"},{"name":"nCovForecast","repo":"https://github.com/benflips/nCovForecast","cat":"other"},{"name":"netattack","repo":"https://github.com/chrizator/netattack","cat":"other"},{"name":"netattack2","repo":"https://github.com/chrizator/netattack2","cat":"other"},{"name":"netdiscover","repo":"https://github.com/netdiscover-scanner/netdiscover","cat":"other"},{"name":"Nethunter-In-Termux","repo":"https://github.com/Hax4us/Nethunter-In-Termux","cat":"utility"},{"name":"NETNOOB","repo":"https://github.com/NARCOTIC/NETNOOB","cat":"other"},{"name":"Nettacker","repo":"https://github.com/OWASP/Nettacker","cat":"other"},{"name":"nexphisher","repo":"https://github.com/htr-tech/nexphisher","cat":"phishing"},{"name":"nginx","repo":"https://github.com/nginx/nginx","cat":"other"},{"name":"nginxconfig.io","repo":"https://github.com/digitalocean/nginxconfig.io","cat":"other"},{"name":"nikto","repo":"https://github.com/sullo/nikto","cat":"web"},{"name":"nikto-sym-fix","repo":"https://github.com/b3nsh4/nikto-sym-fix","cat":"web"},{"name":"nishang","repo":"https://github.com/samratashok/nishang","cat":"other"},{"name":"nk26","repo":"https://github.com/milio48/nk26","cat":"other"},{"name":"nmap","repo":"https://github.com/nmap/nmap","cat":"recon"},{"name":"nodexp","repo":"https://github.com/esmog/nodexp","cat":"other"},{"name":"noisy","repo":"https://github.com/1tayH/noisy","cat":"other"},{"name":"NoSQLMap","repo":"https://github.com/codingo/NoSQLMap","cat":"web"},{"name":"notefast","repo":"https://github.com/cyweb/notefast","cat":"other"},{"name":"Nscan","repo":"https://github.com/OffensivePython/Nscan","cat":"web"},{"name":"nuclei","repo":"https://github.com/projectdiscovery/nuclei","cat":"other"},{"name":"nWatch","repo":"https://github.com/Cyber-Forensic/nWatch","cat":"other"},{"name":"ohmyqr","repo":"https://github.com/cryptedwolf/ohmyqr","cat":"utility"},{"name":"One-Lin3r","repo":"https://github.com/D4Vinci/One-Lin3r","cat":"other"},{"name":"onioff","repo":"https://github.com/k4m4/onioff","cat":"other"},{"name":"OpenDoor","repo":"https://github.com/stanislav-web/OpenDoor","cat":"other"},{"name":"osi.ig","repo":"https://github.com/th3unkn0n/osi.ig","cat":"other"},{"name":"OSIF","repo":"https://github.com/0xlousie/OSIF","cat":"other"},{"name":"otc","repo":"https://github.com/vetid/otc","cat":"other"},{"name":"Overload-DoS","repo":"https://github.com/codingplanets/Overload-DoS","cat":"other"},{"name":"OWASP-WebScarab","repo":"https://github.com/OWASP/OWASP-WebScarab","cat":"other"},{"name":"OWScan","repo":"https://github.com/Gameye98/OWScan","cat":"web"},{"name":"p0f","repo":"https://github.com/p0f/p0f","cat":"other"},{"name":"PadBuster","repo":"https://github.com/strozfriedberg/PadBuster","cat":"other"},{"name":"pakcrack","repo":"https://github.com/htr-tech/pakcrack","cat":"password"},{"name":"PANhunt","repo":"https://github.com/Dionach/PANhunt","cat":"other"},{"name":"Parat","repo":"https://github.com/fadinglr/Parat","cat":"exploit"},{"name":"parity-config-generator","repo":"https://github.com/paritytech/parity-config-generator","cat":"anonymity"},{"name":"paroleitaliane","repo":"https://github.com/napolux/paroleitaliane","cat":"other"},{"name":"parrot","repo":"https://github.com/parrot/parrot","cat":"other"},{"name":"Parsero","repo":"https://github.com/behindthefirewalls/Parsero","cat":"other"},{"name":"PassGen","repo":"https://github.com/Broham/PassGen","cat":"password"},{"name":"Password-Cracker","repo":"https://github.com/PhilipMur/Password-Cracker","cat":"password"},{"name":"patator","repo":"https://github.com/lanjelot/patator","cat":"anonymity"},{"name":"pdfinfo","repo":"https://github.com/jfuentestgn/pdfinfo","cat":"recon"},{"name":"pdfparser","repo":"https://github.com/smalot/pdfparser","cat":"other"},{"name":"peepdf","repo":"https://github.com/jesparza/peepdf","cat":"other"},{"name":"peframe","repo":"https://github.com/guelfoweb/peframe","cat":"other"},{"name":"pemulungBTC","repo":"https://github.com/Cvar1984/pemulungBTC","cat":"other"},{"name":"PenBox","repo":"https://github.com/x3omdax/PenBox","cat":"other"},{"name":"Pentest-Tools","repo":"https://github.com/S3cur3Th1sSh1t/Pentest-Tools","cat":"utility"},{"name":"pentest-wiki","repo":"https://github.com/nixawk/pentest-wiki","cat":"other"},{"name":"pentmenu","repo":"https://github.com/GinjaChris/pentmenu","cat":"other"},{"name":"perl5","repo":"https://github.com/Perl/perl5","cat":"other"},{"name":"phd","repo":"https://github.com/php/phd","cat":"other"},{"name":"PhEmail","repo":"https://github.com/Dionach/PhEmail","cat":"other"},{"name":"phishin","repo":"https://github.com/jcraigk/phishin","cat":"phishing"},{"name":"phishing_catcher","repo":"https://github.com/x0rz/phishing_catcher","cat":"phishing"},{"name":"PhishMailer","repo":"https://github.com/BiZken/PhishMailer","cat":"phishing"},{"name":"Phising-Game","repo":"https://github.com/CyberTCA/Phising-Game","cat":"other"},{"name":"Phoneinfoga","repo":"https://github.com/la-deep-web/Phoneinfoga","cat":"recon"},{"name":"Photon","repo":"https://github.com/s0md3v/Photon","cat":"other"},{"name":"PHP-Connector","repo":"https://github.com/LoopFiftyFour/PHP-Connector","cat":"anonymity"},{"name":"phpsploit","repo":"https://github.com/nil0x42/phpsploit","cat":"exploit"},{"name":"PiDense","repo":"https://github.com/WiPi-Hunter/PiDense","cat":"other"},{"name":"pig","repo":"https://github.com/apache/pig","cat":"other"},{"name":"pinky","repo":"https://github.com/lorenzo/pinky","cat":"other"},{"name":"pixiewps","repo":"https://github.com/wiire-a/pixiewps","cat":"wifi"},{"name":"plecost","repo":"https://github.com/Plecost/plecost","cat":"other"},{"name":"Plutus","repo":"https://github.com/Isaacdelly/Plutus","cat":"other"},{"name":"PoC-Exploits","repo":"https://github.com/CERTCC/PoC-Exploits","cat":"exploit"},{"name":"podcrush","repo":"https://github.com/jnystad/podcrush","cat":"other"},{"name":"poet","repo":"https://github.com/uber-research/poet","cat":"other"},{"name":"Pompem","repo":"https://github.com/rfunix/Pompem","cat":"other"},{"name":"PooleBotnet","repo":"https://github.com/codingplanets/PooleBotnet","cat":"social"},{"name":"port-lookup","repo":"https://github.com/the-c0d3r/port-lookup","cat":"other"},{"name":"PortWitness","repo":"https://github.com/viperbluff/PortWitness","cat":"other"},{"name":"Powershell-RAT","repo":"https://github.com/Viralmaniar/Powershell-RAT","cat":"exploit"},{"name":"PowerSploit","repo":"https://github.com/PowerShellMafia/PowerSploit","cat":"exploit"},{"name":"prank","repo":"https://github.com/siputra12/prank","cat":"other"},{"name":"prex","repo":"https://github.com/rbuckton/prex","cat":"other"},{"name":"PrivEsc","repo":"https://github.com/1N3/PrivEsc","cat":"other"},{"name":"probot","repo":"https://github.com/probot/probot","cat":"social"},{"name":"project-black","repo":"https://github.com/c0rv4x/project-black","cat":"other"},{"name":"proxystrike","repo":"https://github.com/bincker/proxystrike","cat":"anonymity"},{"name":"pupy","repo":"https://github.com/n1nj4sec/pupy","cat":"other"},{"name":"pwnat","repo":"https://github.com/samyk/pwnat","cat":"other"},{"name":"pwnedOrNot","repo":"https://github.com/thewhiteh4t/pwnedOrNot","cat":"other"},{"name":"PwnSTAR","repo":"https://github.com/SilverFoxx/PwnSTAR","cat":"other"},{"name":"Pybelt","repo":"https://github.com/Ekultek/Pybelt","cat":"other"},{"name":"pybluez","repo":"https://github.com/pybluez/pybluez","cat":"wifi"},{"name":"PyBozoCrack","repo":"https://github.com/ikkebr/PyBozoCrack","cat":"password"},{"name":"pyDeletePdfPages","repo":"https://github.com/Mebus/pyDeletePdfPages","cat":"other"},{"name":"pydictor","repo":"https://github.com/LandGrey/pydictor","cat":"anonymity"},{"name":"pynmap","repo":"https://github.com/emsellem/pynmap","cat":"recon"},{"name":"PyPhisher","repo":"https://github.com/sneakerhax/PyPhisher","cat":"phishing"},{"name":"Pyrit","repo":"https://github.com/JPaulMora/Pyrit","cat":"other"},{"name":"pythem","repo":"https://github.com/m4n3dw0lf/pythem","cat":"other"},{"name":"Python-Botnet","repo":"https://github.com/MayankFawkes/Python-Botnet","cat":"social"},{"name":"python-bruteForce","repo":"https://github.com/Antu7/python-bruteForce","cat":"password"},{"name":"Python-Twitter-Bot","repo":"https://github.com/gauravssnl/Python-Twitter-Bot","cat":"social"},{"name":"python-uncompyle6","repo":"https://github.com/rocky/python-uncompyle6","cat":"other"},{"name":"qark","repo":"https://github.com/linkedin/qark","cat":"other"},{"name":"QFloodSms","repo":"https://github.com/qpqg/QFloodSms","cat":"other"},{"name":"QJDID","repo":"https://github.com/qpqg/QJDID","cat":"other"},{"name":"QRLJacking","repo":"https://github.com/OWASP/QRLJacking","cat":"other"},{"name":"quark-engine","repo":"https://github.com/ev-flow/quark-engine","cat":"other"},{"name":"quark-rules","repo":"https://github.com/ev-flow/quark-rules","cat":"other"},{"name":"quasar","repo":"https://github.com/quasarframework/quasar","cat":"other"},{"name":"Raccoon","repo":"https://github.com/evyatarmeged/Raccoon","cat":"other"},{"name":"random-chucknorris-facts","repo":"https://github.com/nbluis/random-chucknorris-facts","cat":"other"},{"name":"rang3r","repo":"https://github.com/floriankunushevci/rang3r","cat":"other"},{"name":"RaspberryPi-Packet-Sniffer","repo":"https://github.com/adityashrm21/RaspberryPi-Packet-Sniffer","cat":"other"},{"name":"rdpy","repo":"https://github.com/citronneur/rdpy","cat":"other"},{"name":"reaver-wps-fork-t6x","repo":"https://github.com/t6x/reaver-wps-fork-t6x","cat":"wifi"},{"name":"Reborn","repo":"https://github.com/4nat/Reborn","cat":"other"},{"name":"recaptcha","repo":"https://github.com/google/recaptcha","cat":"other"},{"name":"recon-ng","repo":"https://github.com/lanmaster53/recon-ng","cat":"recon"},{"name":"recon-raven","repo":"https://github.com/hahwul/recon-raven","cat":"recon"},{"name":"ReconDog","repo":"https://github.com/s0md3v/ReconDog","cat":"recon"},{"name":"Reconnoitre","repo":"https://github.com/codingo/Reconnoitre","cat":"recon"},{"name":"Red-Teaming-Toolkit","repo":"https://github.com/infosecn1nja/Red-Teaming-Toolkit","cat":"other"},{"name":"RED_HAWK","repo":"https://github.com/Tuhinshubhra/RED_HAWK","cat":"other"},{"name":"RegRipper2.8","repo":"https://github.com/sbousseaden/RegRipper2.8","cat":"other"},{"name":"Remot3d","repo":"https://github.com/KeepWannabe/Remot3d","cat":"other"},{"name":"remote-shell","repo":"https://github.com/taylorflatt/remote-shell","cat":"exploit"},{"name":"RenBot","repo":"https://github.com/rorre/RenBot","cat":"social"},{"name":"Report","repo":"https://github.com/IlayTamvan/Report","cat":"other"},{"name":"Repot3","repo":"https://github.com/PangeranAlvins/Repot3","cat":"other"},{"name":"request-ip","repo":"https://github.com/pbojinov/request-ip","cat":"other"},{"name":"Responder","repo":"https://github.com/SpiderLabs/Responder","cat":"other"},{"name":"ReverseAPK","repo":"https://github.com/1N3/ReverseAPK","cat":"other"},{"name":"ridenum","repo":"https://github.com/trustedsec/ridenum","cat":"recon"},{"name":"rock3tman","repo":"https://github.com/binkybear/rock3tman","cat":"other"},{"name":"ROOT.NET","repo":"https://github.com/gordonwatts/ROOT.NET","cat":"exploit"},{"name":"routersploit","repo":"https://github.com/threat9/routersploit","cat":"exploit"},{"name":"RouteryPi","repo":"https://github.com/NuclearPhoenixx/RouteryPi","cat":"other"},{"name":"routing-controllers","repo":"https://github.com/typestack/routing-controllers","cat":"other"},{"name":"roxysploit","repo":"https://github.com/andyvaikunth/roxysploit","cat":"exploit"},{"name":"RsaCrypt","repo":"https://github.com/mussatto/RsaCrypt","cat":"other"},{"name":"rsfac","repo":"https://github.com/farinap5/rsfac","cat":"other"},{"name":"RTLSDR-Scanner","repo":"https://github.com/EarToEarOak/RTLSDR-Scanner","cat":"web"},{"name":"rxTools","repo":"https://github.com/roxas75/rxTools","cat":"utility"},{"name":"Saddam","repo":"https://github.com/OffensivePython/Saddam","cat":"other"},{"name":"sAINT","repo":"https://github.com/tiagorlampert/sAINT","cat":"other"},{"name":"santet-online","repo":"https://github.com/Gameye98/santet-online","cat":"other"},{"name":"saycheese","repo":"https://github.com/MrHacker-X/saycheese","cat":"phishing"},{"name":"sayhello","repo":"https://github.com/greyli/sayhello","cat":"other"},{"name":"SCANNER-INURLBR","repo":"https://github.com/googleinurl/SCANNER-INURLBR","cat":"web"},{"name":"scorpion","repo":"https://github.com/sirrice/scorpion","cat":"other"},{"name":"scrape","repo":"https://github.com/dmmcquay/scrape","cat":"other"},{"name":"script-deface-creator","repo":"https://github.com/ubaydev/script-deface-creator","cat":"anonymity"},{"name":"sechub","repo":"https://github.com/mercedes-benz/sechub","cat":"other"},{"name":"SecLists","repo":"https://github.com/danielmiessler/SecLists","cat":"other"},{"name":"security-cheat-sheet","repo":"https://github.com/GoSecure/security-cheat-sheet","cat":"other"},{"name":"seeker","repo":"https://github.com/thewhiteh4t/seeker","cat":"recon"},{"name":"server","repo":"https://github.com/localtunnel/server","cat":"other"},{"name":"SH33LL","repo":"https://github.com/LOoLzeC/SH33LL","cat":"other"},{"name":"shellnoob","repo":"https://github.com/reyammer/shellnoob","cat":"exploit"},{"name":"shellphish","repo":"https://github.com/suljot/shellphish","cat":"exploit"},{"name":"ShellPop","repo":"https://github.com/0x00-0x00/ShellPop","cat":"exploit"},{"name":"shellstack","repo":"https://github.com/Tuhinshubhra/shellstack","cat":"exploit"},{"name":"sherlock","repo":"https://github.com/sherlock-project/sherlock","cat":"recon"},{"name":"shhgit","repo":"https://github.com/eth0izzle/shhgit","cat":"other"},{"name":"shimit","repo":"https://github.com/cyberark/shimit","cat":"other"},{"name":"shodanwave","repo":"https://github.com/jimywork/shodanwave","cat":"other"},{"name":"shorturl","repo":"https://github.com/develer-staff/shorturl","cat":"other"},{"name":"SigPloit","repo":"https://github.com/SigPloiter/SigPloit","cat":"other"},{"name":"Simple-Fuzzer","repo":"https://github.com/apconole/Simple-Fuzzer","cat":"web"},{"name":"sipvicious","repo":"https://github.com/EnableSecurity/sipvicious","cat":"other"},{"name":"SiteBroker","repo":"https://github.com/Anon-Exploiter/SiteBroker","cat":"other"},{"name":"sitedorks","repo":"https://github.com/Zarcolio/sitedorks","cat":"recon"},{"name":"skipfish","repo":"https://github.com/spinkham/skipfish","cat":"other"},{"name":"sleuthkit","repo":"https://github.com/sleuthkit/sleuthkit","cat":"other"},{"name":"slowhttptest","repo":"https://github.com/shekyan/slowhttptest","cat":"web"},{"name":"slowloris","repo":"https://github.com/gkbrk/slowloris","cat":"other"},{"name":"SMAP","repo":"https://github.com/jries/SMAP","cat":"other"},{"name":"smbmap","repo":"https://github.com/ShawnDEvans/smbmap","cat":"other"},{"name":"smokescreen","repo":"https://github.com/keeganjk/smokescreen","cat":"other"},{"name":"smsid-go","repo":"https://github.com/amsitlab/smsid-go","cat":"other"},{"name":"Sn1per","repo":"https://github.com/1N3/Sn1per","cat":"other"},{"name":"sniffjoke","repo":"https://github.com/vecna/sniffjoke","cat":"other"},{"name":"snoop","repo":"https://github.com/snooppr/snoop","cat":"other"},{"name":"social-engineer-toolkit","repo":"https://github.com/trustedsec/social-engineer-toolkit","cat":"phishing"},{"name":"SocialBox","repo":"https://github.com/Cyb0r9/SocialBox","cat":"phishing"},{"name":"socialbrute","repo":"https://github.com/sh4d0wb0y/socialbrute","cat":"password"},{"name":"SocialFish","repo":"https://github.com/UndeadSec/SocialFish","cat":"web"},{"name":"socialify","repo":"https://github.com/wei/socialify","cat":"phishing"},{"name":"Sooty","repo":"https://github.com/TheresAFewConors/Sooty","cat":"other"},{"name":"Spade","repo":"https://github.com/Cesar-Hack-Gray/Spade","cat":"other"},{"name":"spaghetti","repo":"https://github.com/aljen/spaghetti","cat":"other"},{"name":"spam","repo":"https://github.com/jeremyevans/spam","cat":"social"},{"name":"spamchat","repo":"https://github.com/errorBrain/spamchat","cat":"social"},{"name":"Spammer-Email","repo":"https://github.com/avestra/Spammer-Email","cat":"social"},{"name":"spammer.sys","repo":"https://github.com/sysadminteam/spammer.sys","cat":"social"},{"name":"spamx","repo":"https://github.com/noob-hackers/spamx","cat":"social"},{"name":"spiderbot","repo":"https://github.com/mustafaneguib/spiderbot","cat":"web"},{"name":"SploitX","repo":"https://github.com/MrHacker-X/SploitX","cat":"exploit"},{"name":"SpyCam","repo":"https://github.com/darshanrn/SpyCam","cat":"other"},{"name":"spyder","repo":"https://github.com/spyder-ide/spyder","cat":"other"},{"name":"sqldump","repo":"https://github.com/matssigge/sqldump","cat":"web"},{"name":"sqlitebrowser","repo":"https://github.com/sqlitebrowser/sqlitebrowser","cat":"web"},{"name":"sqliv","repo":"https://github.com/the-robot/sqliv","cat":"web"},{"name":"sqlmap","repo":"https://github.com/sqlmapproject/sqlmap","cat":"web"},{"name":"sqlmate","repo":"https://github.com/s0md3v/sqlmate","cat":"web"},{"name":"sqlscan","repo":"https://github.com/Cvar1984/sqlscan","cat":"web"},{"name":"ss5","repo":"https://github.com/ananclub/ss5","cat":"other"},{"name":"ss7MAPer","repo":"https://github.com/ernw/ss7MAPer","cat":"other"},{"name":"ssb","repo":"https://github.com/pwnesia/ssb","cat":"other"},{"name":"ssh-honeypot","repo":"https://github.com/droberson/ssh-honeypot","cat":"other"},{"name":"ssh-mitm","repo":"https://github.com/ssh-mitm/ssh-mitm","cat":"other"},{"name":"sslcaudit","repo":"https://github.com/abbbe/sslcaudit","cat":"other"},{"name":"sslsplit","repo":"https://github.com/droe/sslsplit","cat":"other"},{"name":"sslstrip","repo":"https://github.com/moxie0/sslstrip","cat":"other"},{"name":"sslyze","repo":"https://github.com/nabla-c0d3/sslyze","cat":"other"},{"name":"stabilizerbot","repo":"https://github.com/4shadoww/stabilizerbot","cat":"social"},{"name":"stagefright","repo":"https://github.com/eudemonics/stagefright","cat":"other"},{"name":"Stark","repo":"https://github.com/ximsfei/Stark","cat":"other"},{"name":"steghide","repo":"https://github.com/StegHigh/steghide","cat":"forensics"},{"name":"stegosploit","repo":"https://github.com/csh/stegosploit","cat":"exploit"},{"name":"Stitch","repo":"https://github.com/nathanlopez/Stitch","cat":"other"},{"name":"stp","repo":"https://github.com/stp/stp","cat":"other"},{"name":"Striker","repo":"https://github.com/s0md3v/Striker","cat":"other"},{"name":"subbrute","repo":"https://github.com/TheRook/subbrute","cat":"password"},{"name":"subfinder","repo":"https://github.com/projectdiscovery/subfinder","cat":"other"},{"name":"Sublist3r","repo":"https://github.com/aboul3la/Sublist3r","cat":"web"},{"name":"subscraper","repo":"https://github.com/m8sec/subscraper","cat":"other"},{"name":"suratcinta","repo":"https://github.com/qmuaji/suratcinta","cat":"other"},{"name":"Swapcli","repo":"https://github.com/WahyuHidayattz/Swapcli","cat":"other"},{"name":"Swift-Keylogger","repo":"https://github.com/SkrewEverything/Swift-Keylogger","cat":"other"},{"name":"T-Header","repo":"https://github.com/remo7777/T-Header","cat":"other"},{"name":"T-LOAD","repo":"https://github.com/noob-hackers/T-LOAD","cat":"other"},{"name":"T.DYF","repo":"https://github.com/fahri-x-droid/T.DYF","cat":"other"},{"name":"TAPSELsec","repo":"https://github.com/B4TAK/TAPSELsec","cat":"other"},{"name":"Tbanner","repo":"https://github.com/tahmidrayat/Tbanner","cat":"utility"},{"name":"Tbomb","repo":"https://github.com/Hackertrackersj/Tbomb","cat":"other"},{"name":"tcpdump","repo":"https://github.com/the-tcpdump-group/tcpdump","cat":"forensics"},{"name":"TekDefense-Automater","repo":"https://github.com/1aN0rmus/TekDefense-Automater","cat":"other"},{"name":"TeleKiller","repo":"https://github.com/ultrasecurity/TeleKiller","cat":"other"},{"name":"telkomsel","repo":"https://github.com/faizzart/telkomsel","cat":"other"},{"name":"tembakxl","repo":"https://github.com/errorBrain/tembakxl","cat":"other"},{"name":"termineter","repo":"https://github.com/rsmusllp/termineter","cat":"other"},{"name":"termshark","repo":"https://github.com/gcla/termshark","cat":"other"},{"name":"Termux-Banner","repo":"https://github.com/Bhai4You/Termux-Banner","cat":"utility"},{"name":"termux-create-package","repo":"https://github.com/termux/termux-create-package","cat":"utility"},{"name":"termux-fedora","repo":"https://github.com/nmilosev/termux-fedora","cat":"utility"},{"name":"termux-go","repo":"https://github.com/rafalgolarz/termux-go","cat":"utility"},{"name":"Termux-Lazyscript","repo":"https://github.com/TechnicalMujeeb/Termux-Lazyscript","cat":"utility"},{"name":"termux-login","repo":"https://github.com/htr-tech/termux-login","cat":"utility"},{"name":"Termux-Login-v1.2","repo":"https://github.com/TechnicalMujeeb/Termux-Login-v1.2","cat":"utility"},{"name":"termux-loginv2fx","repo":"https://github.com/Harisgitama/termux-loginv2fx","cat":"utility"},{"name":"termux-ohmyzsh","repo":"https://github.com/Cabbagec/termux-ohmyzsh","cat":"utility"},{"name":"Termux-Os","repo":"https://github.com/Bhai4You/Termux-Os","cat":"utility"},{"name":"termux-shell","repo":"https://github.com/htr-tech/termux-shell","cat":"exploit"},{"name":"Termux-speak","repo":"https://github.com/TechnicalMujeeb/Termux-speak","cat":"utility"},{"name":"termux-styling","repo":"https://github.com/termux/termux-styling","cat":"utility"},{"name":"termux-ubuntu","repo":"https://github.com/Neo-Oli/termux-ubuntu","cat":"utility"},{"name":"TermuxAlpine","repo":"https://github.com/Hax4us/TermuxAlpine","cat":"utility"},{"name":"Th3inspector","repo":"https://github.com/Moham3dRiahi/Th3inspector","cat":"anonymity"},{"name":"thanatos-archer","repo":"https://github.com/4shadoww/thanatos-archer","cat":"utility"},{"name":"thc-hydra","repo":"https://github.com/vanhauser-thc/thc-hydra","cat":"password"},{"name":"thc-ipv6","repo":"https://github.com/vanhauser-thc/thc-ipv6","cat":"password"},{"name":"the-backdoor-factory","repo":"https://github.com/secretsquirrel/the-backdoor-factory","cat":"exploit"},{"name":"The-Egyptian-Tangram","repo":"https://github.com/CarlosLunaMota/The-Egyptian-Tangram","cat":"other"},{"name":"The-Eye","repo":"https://github.com/EgeBalci/The-Eye","cat":"other"},{"name":"TheFatRat","repo":"https://github.com/Screetsec/TheFatRat","cat":"exploit"},{"name":"thefuck","repo":"https://github.com/nvbn/thefuck","cat":"other"},{"name":"theHarvester","repo":"https://github.com/laramies/theHarvester","cat":"recon"},{"name":"thermo","repo":"https://github.com/CalebBell/thermo","cat":"other"},{"name":"TheSmartool","repo":"https://github.com/Coroxx/TheSmartool","cat":"other"},{"name":"tinper-mox","repo":"https://github.com/iuap-design/tinper-mox","cat":"other"},{"name":"Tishna","repo":"https://github.com/marciopocebon/Tishna","cat":"other"},{"name":"TM-scanner","repo":"https://github.com/TechnicalMujeeb/TM-scanner","cat":"web"},{"name":"tmanager","repo":"https://github.com/TerrariaManager/tmanager","cat":"other"},{"name":"tmvenom","repo":"https://github.com/TechnicalMujeeb/tmvenom","cat":"other"},{"name":"TokopediaAPI","repo":"https://github.com/kevinjon27/TokopediaAPI","cat":"other"},{"name":"toolkit","repo":"https://github.com/actions/toolkit","cat":"other"},{"name":"Toolss","repo":"https://github.com/AnonHackerr/Toolss","cat":"utility"},{"name":"ToRat","repo":"https://github.com/luantak/ToRat","cat":"exploit"},{"name":"torghost","repo":"https://github.com/SusmithKrishnan/torghost","cat":"anonymity"},{"name":"torshammer","repo":"https://github.com/Karlheinzniebuhr/torshammer","cat":"anonymity"},{"name":"torstats","repo":"https://github.com/mono-man/torstats","cat":"anonymity"},{"name":"TrackerDSST","repo":"https://github.com/honggui/TrackerDSST","cat":"other"},{"name":"trackerjacker","repo":"https://github.com/calebmadrigal/trackerjacker","cat":"other"},{"name":"TrackOut","repo":"https://github.com/abaykan/TrackOut","cat":"other"},{"name":"traitor","repo":"https://github.com/liamg/traitor","cat":"anonymity"},{"name":"trape","repo":"https://github.com/jofpin/trape","cat":"other"},{"name":"Traper-X","repo":"https://github.com/MrHacker-X/Traper-X","cat":"other"},{"name":"Trity-1","repo":"https://github.com/samyoyo/Trity-1","cat":"other"},{"name":"trojanizer","repo":"https://github.com/r00t-3xp10it/trojanizer","cat":"other"},{"name":"Truth","repo":"https://github.com/CybernetiX-S3C/Truth","cat":"other"},{"name":"tstyle","repo":"https://github.com/htr-tech/tstyle","cat":"other"},{"name":"TTR-Tools","repo":"https://github.com/AskAlice/TTR-Tools","cat":"utility"},{"name":"tweetbot-max","repo":"https://github.com/maxrooted/tweetbot-max","cat":"social"},{"name":"tweetentropy","repo":"https://github.com/x0rz/tweetentropy","cat":"other"},{"name":"Twitter-Sniper","repo":"https://github.com/MohammedSalama/Twitter-Sniper","cat":"social"},{"name":"twitterscraper","repo":"https://github.com/taspinar/twitterscraper","cat":"social"},{"name":"txtool","repo":"https://github.com/kuburan/txtool","cat":"other"},{"name":"udfhack","repo":"https://github.com/sqlmapproject/udfhack","cat":"other"},{"name":"ufonet","repo":"https://github.com/epsylon/ufonet","cat":"other"},{"name":"Ultimate-Bomber-Spammer","repo":"https://github.com/Nocturnal-Compiler/Ultimate-Bomber-Spammer","cat":"social"},{"name":"Umbrella","repo":"https://github.com/4w4k3/Umbrella","cat":"other"},{"name":"unfollow-plus","repo":"https://github.com/htr-tech/unfollow-plus","cat":"other"},{"name":"unifi-voucher-generator","repo":"https://github.com/DJM0/unifi-voucher-generator","cat":"anonymity"},{"name":"unlimited-tethering","repo":"https://github.com/RiFi2k/unlimited-tethering","cat":"other"},{"name":"urh","repo":"https://github.com/jopohl/urh","cat":"other"},{"name":"usql","repo":"https://github.com/xo/usql","cat":"web"},{"name":"V3n0M-Scanner","repo":"https://github.com/v3n0m-Scanner/V3n0M-Scanner","cat":"web"},{"name":"vbscan","repo":"https://github.com/OWASP/vbscan","cat":"web"},{"name":"Vegile","repo":"https://github.com/Screetsec/Vegile","cat":"other"},{"name":"VHostScan","repo":"https://github.com/codingo/VHostScan","cat":"web"},{"name":"vinfo","repo":"https://github.com/alx741/vinfo","cat":"recon"},{"name":"VirusX","repo":"https://github.com/TSMaitry/VirusX","cat":"other"},{"name":"viSQL","repo":"https://github.com/ethicalhackeragnidhra/viSQL","cat":"web"},{"name":"volatility","repo":"https://github.com/volatilityfoundation/volatility","cat":"forensics"},{"name":"vtools","repo":"https://github.com/LUMC/vtools","cat":"utility"},{"name":"Vulmap","repo":"https://github.com/vulmon/Vulmap","cat":"other"},{"name":"w3af","repo":"https://github.com/andresriancho/w3af","cat":"other"},{"name":"wafw00f","repo":"https://github.com/EnableSecurity/wafw00f","cat":"other"},{"name":"watweb","repo":"https://github.com/siddharthpandey22/watweb","cat":"other"},{"name":"web-terminal","repo":"https://github.com/rabchev/web-terminal","cat":"other"},{"name":"webdav","repo":"https://github.com/hacdias/webdav","cat":"other"},{"name":"WebHackersWeapons","repo":"https://github.com/hahwul/WebHackersWeapons","cat":"other"},{"name":"webkiller","repo":"https://github.com/ultrasecurity/webkiller","cat":"other"},{"name":"WebKit","repo":"https://github.com/WebKit/WebKit","cat":"other"},{"name":"webpwn3r","repo":"https://github.com/zigoo0/webpwn3r","cat":"other"},{"name":"websploit","repo":"https://github.com/websploit/websploit","cat":"exploit"},{"name":"WebXploiter","repo":"https://github.com/a0xnirudh/WebXploiter","cat":"other"},{"name":"weeman","repo":"https://github.com/evait-security/weeman","cat":"other"},{"name":"weevely3","repo":"https://github.com/epinna/weevely3","cat":"other"},{"name":"wesng","repo":"https://github.com/bitsadmin/wesng","cat":"other"},{"name":"wfdroid-termux","repo":"https://github.com/bytezcrew/wfdroid-termux","cat":"utility"},{"name":"wfuzz","repo":"https://github.com/xmendez/wfuzz","cat":"web"},{"name":"WhatsappHack","repo":"https://github.com/ZheHacK/WhatsappHack","cat":"social"},{"name":"whatshack","repo":"https://github.com/sabriallani/whatshack","cat":"social"},{"name":"WhatWeb","repo":"https://github.com/urbanadventurer/WhatWeb","cat":"other"},{"name":"whonow","repo":"https://github.com/brannondorsey/whonow","cat":"other"},{"name":"wifi-hacker","repo":"https://github.com/esc0rtd3w/wifi-hacker","cat":"wifi"},{"name":"wifi-password","repo":"https://github.com/sdushantha/wifi-password","cat":"wifi"},{"name":"WiFi-Pumpkin","repo":"https://github.com/zackhaikal/WiFi-Pumpkin","cat":"wifi"},{"name":"WiFiBroot","repo":"https://github.com/hash3liZer/WiFiBroot","cat":"wifi"},{"name":"WifiBruteCrack","repo":"https://github.com/cinquemb/WifiBruteCrack","cat":"wifi"},{"name":"wifiphisher","repo":"https://github.com/wifiphisher/wifiphisher","cat":"wifi"},{"name":"wifitap","repo":"https://github.com/GDSSecurity/wifitap","cat":"wifi"},{"name":"wifite","repo":"https://github.com/derv82/wifite","cat":"wifi"},{"name":"wifite2","repo":"https://github.com/derv82/wifite2","cat":"wifi"},{"name":"wifresti","repo":"https://github.com/LionSec/wifresti","cat":"other"},{"name":"win-toolkit","repo":"https://github.com/giovadifiore/win-toolkit","cat":"other"},{"name":"Windows-Hacks","repo":"https://github.com/LazoVelko/Windows-Hacks","cat":"other"},{"name":"Winpayloads","repo":"https://github.com/nccgroup/Winpayloads","cat":"exploit"},{"name":"wirespy","repo":"https://github.com/aress31/wirespy","cat":"other"},{"name":"wordpress","repo":"https://github.com/docker-library/wordpress","cat":"other"},{"name":"Wordpresscan","repo":"https://github.com/swisskyrepo/Wordpresscan","cat":"web"},{"name":"world_mortality","repo":"https://github.com/akarlinsky/world_mortality","cat":"other"},{"name":"wp-plugin-scanner","repo":"https://github.com/pywget/wp-plugin-scanner","cat":"web"},{"name":"wpbf","repo":"https://github.com/atarantini/wpbf","cat":"other"},{"name":"wpscan","repo":"https://github.com/wpscanteam/wpscan","cat":"wifi"},{"name":"WPSeku","repo":"https://github.com/Redshoee/WPSeku","cat":"wifi"},{"name":"wreckuests","repo":"https://github.com/abriginets/wreckuests","cat":"other"},{"name":"WSLTools","repo":"https://github.com/AnonHackerr/WSLTools","cat":"utility"},{"name":"XAttackProV30","repo":"https://github.com/Moham3dRiahi/XAttackProV30","cat":"other"},{"name":"XCTR-Hacking-Tools","repo":"https://github.com/capture0x/XCTR-Hacking-Tools","cat":"utility"},{"name":"xerces-c","repo":"https://github.com/apache/xerces-c","cat":"other"},{"name":"xerosploit","repo":"https://github.com/LionSec/xerosploit","cat":"exploit"},{"name":"XERXES","repo":"https://github.com/XCHADXFAQ77X/XERXES","cat":"other"},{"name":"xl-py","repo":"https://github.com/anggialberto/xl-py","cat":"other"},{"name":"XPL-SEARCH","repo":"https://github.com/CoderPirata/XPL-SEARCH","cat":"utility"},{"name":"xplico","repo":"https://github.com/xplico/xplico","cat":"other"},{"name":"Xshell","repo":"https://github.com/Manisso/Xshell","cat":"exploit"},{"name":"xspy","repo":"https://github.com/mnp/xspy","cat":"other"},{"name":"xsser","repo":"https://github.com/epsylon/xsser","cat":"web"},{"name":"XSStrike","repo":"https://github.com/s0md3v/XSStrike","cat":"web"},{"name":"yahoo-cracker-","repo":"https://github.com/afeck21/yahoo-cracker-","cat":"password"},{"name":"yersinia","repo":"https://github.com/tomac/yersinia","cat":"other"},{"name":"youtube-comment-suite","repo":"https://github.com/mattwright324/youtube-comment-suite","cat":"other"},{"name":"YouTubeShop","repo":"https://github.com/BitTheByte/YouTubeShop","cat":"other"},{"name":"ysoserial","repo":"https://github.com/frohoff/ysoserial","cat":"other"},{"name":"Z3sec","repo":"https://github.com/IoTsec/Z3sec","cat":"other"},{"name":"zambie","repo":"https://github.com/iTzPrime/zambie","cat":"other"},{"name":"zaproxy","repo":"https://github.com/zaproxy/zaproxy","cat":"web"},{"name":"zarp","repo":"https://github.com/hatRiot/zarp","cat":"other"},{"name":"ZBOT-Botnet","repo":"https://github.com/codingplanets/ZBOT-Botnet","cat":"social"},{"name":"Zerodoor","repo":"https://github.com/Souhardya/Zerodoor","cat":"other"},{"name":"Zeus","repo":"https://github.com/zeustrojancode/Zeus","cat":"other"},{"name":"zirikatu","repo":"https://github.com/pasahitz/zirikatu","cat":"other"},{"name":"zones","repo":"https://github.com/jgrss/zones","cat":"other"},{"name":"zphisher","repo":"https://github.com/htr-tech/zphisher","cat":"phishing"},{"name":"Zydra","repo":"https://github.com/hamedA2/Zydra","cat":"other"}]""")

CATEGORIES = [
    ("wifi", "Wi-Fi & wireless"),
    ("web", "Web exploitation"),
    ("recon", "Recon & OSINT"),
    ("password", "Password & hash"),
    ("exploit", "Exploitation"),
    ("phishing", "Phishing (authorized testing)"),
    ("anonymity", "Anonymity & tunneling"),
    ("forensics", "Forensics"),
    ("social", "Social & bots"),
    ("utility", "Utility & environment"),
    ("other", "General / uncategorized"),
]

INSTALL_ROOT = os.path.join(os.path.expanduser("~"), "Hacked-tools")


def _find_tool(pred):
    return [t for t in TOOLS if pred(t)]


def tools_by_letter(letter: str):
    return _find_tool(lambda t: t["name"].upper().startswith(letter.upper()))


def tools_by_category(cat: str):
    return _find_tool(lambda t: t["cat"] == cat)


def search_tools(query: str):
    q = query.lower()
    return [t for t in TOOLS if q in t["name"].lower()]


# ============================================================
#  Install engine - one generic path for all 920 tools
# ============================================================


def _pkg_cmd() -> str:
    if shutil.which("apt") or shutil.which("apt-get"):
        return "apt" if shutil.which("apt") else "apt-get"
    for pm in ("dnf", "yum", "pacman", "zypper", "apk"):
        if shutil.which(pm):
            return pm
    return ""


def _ensure_git() -> bool:
    if shutil.which("git"):
        return True
    pm = _pkg_cmd()
    if not pm:
        err("git is not installed and no package manager was found")
        return False
    warn("git missing - installing it first")
    subprocess.call([pm, "install", "-y", "git"])
    return bool(shutil.which("git"))


def install_tool(entry: dict) -> bool:
    name, repo = entry["name"], entry["repo"]
    dest = os.path.join(INSTALL_ROOT, re.sub(r"[^\w.-]", "_", name))
    print()
    if os.path.exists(dest):
        if confirm(f"{name} already installed at {dest} - update it?"):
            say("git -C " + dest + " pull")
            subprocess.call(["git", "-C", dest, "pull"])
            ok(f"{name} updated")
        else:
            note(f"keeping existing {name}")
        return True
    if not _ensure_git():
        pause()
        return False
    os.makedirs(INSTALL_ROOT, exist_ok=True)
    say(f"cloning {name}")
    note(repo)
    code = subprocess.call(["git", "clone", "--depth", "1", repo, dest])
    if code != 0:
        err(f"clone failed for {name}")
        return False
    ok(f"{name} installed at {dest}")
    for marker in ("install.sh", "setup.sh"):
        marker_path = os.path.join(dest, marker)
        if os.path.isfile(marker_path):
            if confirm(f"run {marker} for {name}?"):
                subprocess.call(["bash", marker_path], cwd=dest)
            break
    return True


def install_all_matching(tools: list, *, batch: bool = False):
    if not tools:
        err("nothing matched")
        pause()
        return
    if not batch:
        say(f"{len(tools)} tool(s) selected")
        if not confirm(f"install all {len(tools)} now?"):
            note("cancelled")
            return
    good = bad = skip = 0
    for i, t in enumerate(tools, 1):
        dest = os.path.join(INSTALL_ROOT, re.sub(r"[^\w.-]", "_", t["name"]))
        if os.path.exists(dest):
            skip += 1
            continue
        say(f"[{i}/{len(tools)}] {t['name']}")
        if _clone_quiet(t):
            good += 1
        else:
            bad += 1
    print()
    kv("installed", good)
    kv("skipped (existing)", skip)
    kv("failed", bad)
    pause()


def _clone_quiet(t: dict) -> bool:
    dest = os.path.join(INSTALL_ROOT, re.sub(r"[^\w.-]", "_", t["name"]))
    os.makedirs(INSTALL_ROOT, exist_ok=True)
    code = subprocess.call(["git", "clone", "--depth", "1", "-q", t["repo"], dest])
    return code == 0


# ============================================================
#  Browsers - letter, category, search
# ============================================================

PAGE = 30


def _print_tool_rows(tools: list, start: int = 0):
    for i, t in enumerate(tools[start:start + PAGE], start + 1):
        print(f"  {_c(DM, str(i).rjust(4))}  {_c(WH, t['name'])}")


def _pick_and_install(tools: list, label: str):
    """Paginated picker over a tool list. Returns when user goes back."""
    start = 0
    while True:
        _clear()
        banner()
        header(f"{label} - {len(tools)} tool(s)")
        _print_tool_rows(tools, start)
        shown_end = min(start + PAGE, len(tools))
        more = shown_end < len(tools)
        print()
        hint = f"showing {start + 1}-{shown_end} of {len(tools)}"
        if more:
            hint += "  ·  'n' next page"
        if start > 0:
            hint += "  ·  'p' previous page"
        hint += "  ·  'all' install everything listed"
        note(hint)
        try:
            pick = input(f"\n  {_c(YL, 'hacked')}{_c(DM, ' ❯ ')}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise SafeExit
        if pick in EXIT_WORDS:
            return
        if pick == "n" and more:
            start = shown_end
            continue
        if pick == "p" and start > 0:
            start = max(0, start - PAGE)
            continue
        if pick == "all":
            if confirm(f"install all {len(tools)} listed tool(s)?"):
                install_all_matching(tools, batch=True)
            continue
        if pick.isdigit():
            idx = int(pick) - 1
            if 0 <= idx < len(tools):
                install_tool(tools[idx])
                pause()
                continue
        err("invalid choice")


def letters_menu():
    while True:
        _clear()
        banner()
        header("BROWSE BY LETTER")
        row_a = "  ".join(f"{_c(WH, ch)}" for ch in "ABCDEFGHI")
        row_b = "  ".join(f"{_c(WH, ch)}" for ch in "JKLMNOPQR")
        row_c = "  ".join(f"{_c(WH, ch)}" for ch in "STUVWXYZ")
        print()
        print(f"  {row_a}")
        print(f"  {row_b}")
        print(f"  {row_c}")
        print()
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if not tools_by_letter(ch):
                warn(f"letter {ch} has no tools")
        note("type a letter to browse  ·  q to go back")
        try:
            pick = input(f"\n  {_c(YL, 'letter')}{_c(DM, ' ❯ ')}").strip().upper()
        except (EOFError, KeyboardInterrupt):
            raise SafeExit
        if pick.lower() in EXIT_WORDS:
            return
        if len(pick) == 1 and pick.isalpha():
            sel = tools_by_letter(pick)
            if not sel:
                err(f"no tools starting with {pick}")
                pause()
                continue
            _pick_and_install(sel, f"Letter {pick}")
        else:
            err("enter a single letter")


def categories_menu():
    while True:
        _clear()
        banner()
        header("BROWSE BY CATEGORY")
        print()
        for i, (cat, label) in enumerate(CATEGORIES, 1):
            item(str(i), f"{label}", numw=2)
        try:
            pick = input(f"\n  {_c(YL, 'hacked')}{_c(DM, ' ❯ ')}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise SafeExit
        if pick in EXIT_WORDS:
            return
        if pick.isdigit() and 1 <= int(pick) <= len(CATEGORIES):
            cat, label = CATEGORIES[int(pick) - 1]
            sel = tools_by_category(cat)
            if not sel:
                err("no tools in this category")
                pause()
                continue
            _pick_and_install(sel, label)
        else:
            err("invalid choice")


def search_menu():
    while True:
        _clear()
        banner()
        header("SEARCH TOOLS")
        try:
            q = input(f"\n  {_c(YL, 'search')}{_c(DM, ' ❯ ')}").strip()
        except (EOFError, KeyboardInterrupt):
            raise SafeExit
        if q.lower() in EXIT_WORDS:
            return
        if not q:
            continue
        sel = search_tools(q)
        if not sel:
            err(f"nothing matches '{q}'")
            pause()
            continue
        _pick_and_install(sel, f"Search: {q}")


def show_all_menu():
    sel = list(TOOLS)
    _pick_and_install(sel, "All tools")


# ============================================================
#  Update / about / doctor
# ============================================================


def update_all():
    header("UPDATE INSTALLED TOOLS")
    if not os.path.isdir(INSTALL_ROOT):
        note("nothing installed yet - " + INSTALL_ROOT)
        pause()
        return
    entries = sorted(os.listdir(INSTALL_ROOT))
    if not entries:
        note("nothing installed yet")
        pause()
        return
    good = bad = 0
    for d in entries:
        path = os.path.join(INSTALL_ROOT, d)
        if not os.path.isdir(os.path.join(path, ".git")):
            continue
        say(f"pulling {d}")
        code = subprocess.call(["git", "-C", path, "pull", "--ff-only"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if code == 0:
            good += 1
        else:
            bad += 1
    print()
    kv("updated", good)
    kv("failed", bad)
    pause()


def about():
    header("ABOUT HACKED")
    kv("version", __version__)
    kv("author", "MrHacker-X")
    kv("website", "https://vritrasec.com")
    kv("network", "https://link.vritrasec.com")
    kv("license", "Boost Software License 1.0")
    kv("catalog", f"{len(TOOLS)} verified tools")
    print()
    say("Hacked installs third-party security tools from GitHub with one")
    say("generic engine - no more copy-pasted installers, no dead links.")
    print()
    warn("every tool has its own license and purpose - review before use.")


def run_doctor():
    header("DOCTOR - ENVIRONMENT CHECK")

    def chk(label, good, detail=""):
        if good:
            ok(f"{label} - {detail}" if detail else label)
        else:
            err(f"{label} - {detail}" if detail else label)

    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    chk("python 3.8+", sys.version_info >= (3, 8), ver)
    chk("colorama", HAVE_COLORAMA, "installed" if HAVE_COLORAMA else "pip install colorama")
    chk("git", shutil.which("git") is not None, shutil.which("git") or "required for installs")
    pm = _pkg_cmd()
    chk("package manager", bool(pm), pm or "none detected")
    net = _probe_net()
    chk("network (github.com)", net, "reachable" if net else "unreachable")
    print()
    print()


def _probe_net() -> bool:
    try:
        req = urllib.request.Request("https://github.com", headers={"User-Agent": "Hacked/2.0"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.status < 500
    except Exception:
        return False


# ============================================================
#  Main menu + CLI
# ============================================================


def main_menu_screen():
    print()
    header("MAIN MENU")
    item("1", "Browse by letter", numw=2)
    item("2", "Browse by category", numw=2)
    item("3", "Search tools", numw=2)
    item("4", "Show all tools", numw=2)
    item("5", "Update installed tools", numw=2)
    item("6", "About")
    item("7", "Doctor", numw=2)
    item("0", "Exit")


def category_screen(ch: str):
    if ch == "01":
        letters_menu()
    elif ch == "02":
        categories_menu()
    elif ch == "03":
        search_menu()
    elif ch == "04":
        show_all_menu()
    elif ch == "05":
        update_all()
    elif ch == "06":
        about()
        pause()
    elif ch == "07":
        run_doctor()
        pause()


def parse_args():
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Hacked v2.0 - The Massive Tools Installer for Termux & Linux",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--doctor", action="store_true", help="run environment checks and exit")
    parser.add_argument("-s", "--search", metavar="QUERY", help="search the catalog and exit to picker")
    parser.add_argument("-i", "--install", metavar="NAME", help="install a tool by exact name and exit")
    return parser


def main():
    args = parse_args().parse_args()
    try:
        if args.doctor:
            run_doctor()
            pause()
            return
        if args.search:
            sel = search_tools(args.search)
            if not sel:
                err(f"nothing matches '{args.search}'")
                sys.exit(1)
            _pick_and_install(sel, f"Search: {args.search}")
            return
        if args.install:
            sel = [t for t in TOOLS if t["name"].lower() == args.install.lower()]
            if not sel:
                err(f"no tool named '{args.install}' - try: {PROG} -s {args.install}")
                sys.exit(1)
            install_tool(sel[0])
            return
        while True:
            _clear()
            banner()
            main_menu_screen()
            try:
                ch = input(f"\n  {_c(YL, 'hacked')}{_c(DM, ' ❯ ')}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                raise SafeExit
            if ch == "0":
                raise SafeExit
            if ch.isdigit() and ch != "0":
                ch = ch.zfill(2)
            elif not ch:
                continue
            try:
                category_screen(ch)
            except SafeExit:
                raise
            except Exception as exc:  # a broken screen must never kill the session
                err(f"error: {exc.__class__.__name__}: {exc}")
                note("returned to the main menu - nothing lost")
                pause()
    except SafeExit:
        print()
        ok("safe exit - stay ethical")
        sys.exit(130)
    except KeyboardInterrupt:
        print()
        ok("safe exit - stay ethical")
        sys.exit(130)


if __name__ == "__main__":
    main()
