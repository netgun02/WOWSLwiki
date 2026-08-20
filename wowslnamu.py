import json
import os
import re
import sys
import traceback
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
try:
    import ctypes
except Exception:
    ctypes = None

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = APP_DIR

DATA_DIR = os.path.join(APP_DIR, "data")
BUNDLE_DATA_DIR = os.path.join(BUNDLE_DIR, "data")
UI_STATE_PATH = os.path.join(DATA_DIR, "ui_state.json")
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "wowsl_terms.json")
DEFAULT_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_header_template.txt")
DEFAULT_TRAITS_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_traits_template.txt")
DEFAULT_MAIN_BATTERY_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_main_battery_template.txt")
DEFAULT_MAIN_BATTERY_READY_RACK_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_main_battery_ready_rack_template.txt")
DEFAULT_SECONDARY_BATTERY_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_secondary_battery_template.txt")
DEFAULT_TORPEDO_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_torpedo_template.txt")
DEFAULT_INCENDIARY_TORPEDO_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_incendiary_torpedo_template.txt")
DEFAULT_TORPEDO_BOMBER_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_torpedo_bomber_template.txt")
DEFAULT_DIVE_SKIP_BOMBER_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_dive_skip_bomber_template.txt")
DEFAULT_LOW_ALT_BOMBER_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_low_alt_bomber_template.txt")
DEFAULT_CARPET_BOMBER_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_carpet_bomber_template.txt")
DEFAULT_AIRSTRIKE_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_airstrike_template.txt")
DEFAULT_SURV_MANEUVER_CONCEAL_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_surv_maneuver_conceal_template.txt")
DEFAULT_AA_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_aa_template.txt")
DEFAULT_MODS_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_mods_template.txt")
DEFAULT_CONSUMABLES_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_consumables_template.txt")
DEFAULT_CV_CONSUMABLES_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_cv_consumables_template.txt")
DEFAULT_CONSUMABLES_LIST_TEMPLATE_PATH = os.path.join(DATA_DIR, "wiki_consumables_list_template.txt")
DEFAULT_CONSUMABLES_RULES_DIR = os.path.join(DATA_DIR, "consumables_parser_rules")
TEMPLATE_DIR_OVERRIDE = ""
DEFAULT_NATION_COLOR_MAP = {
    "american": "002664",
    "japanese": "df4d4d",
    "british": "00247D",
    "german": "353535",
    "french": "1E90FF",
    "soviet": "87CEEB",
    "italian": "009246",
    "pan-asian": "DE2910",
    "pan-european": "006AA7",
    "netherlands": "FF7F00",
    "pan-american": "448bff",
    "commonwealth": "000080",
    "spanish": "DAA520",
}

NATION_BUTTON_PALETTES = {
    "002664": ("001E4E", "FFE900", "FFFFFF", "0 0 2px #000"),
    "DF4D4D": ("AE3C3C", "FFE900", "FFFFFF", "0 0 2px #000"),
    "00247D": ("001C62", "FFE900", "FFFFFF", "0 0 2px #000"),
    "353535": ("292929", "FFE900", "FFFFFF", "0 0 2px #000"),
    "1E90FF": ("1770C7", "FFE900", "FFFFFF", "0 0 2px #000"),
    "87CEEB": ("69A1B7", "FFE900", "1F2E36", "none"),
    "009246": ("007237", "FFE900", "FFFFFF", "0 0 2px #000"),
    "DE2910": ("AD200C", "FFE900", "FFFFFF", "0 0 2px #000"),
    "006AA7": ("005282", "FFE900", "FFFFFF", "0 0 2px #000"),
    "FF7F00": ("C66300", "74C365", "FFFFFF", "0 0 2px #000"),
    "448BFF": ("356CC7", "FFE900", "FFFFFF", "0 0 2px #000"),
    "000080": ("000064", "FFE900", "FFFFFF", "0 0 2px #000"),
    "DAA520": ("AA8119", "AA151B", "FFFFFF", "0 0 2px #000"),
}


def get_nation_button_palette(border_color):
    selected = (border_color or "").strip().lstrip("#").upper() or "353535"
    palette = NATION_BUTTON_PALETTES.get(selected)
    if palette:
        wrap, accent, text_color, text_shadow = palette
    else:
        try:
            rgb = [int(selected[i:i + 2], 16) for i in (0, 2, 4)]
            wrap = "".join(f"{max(0, min(255, round(channel * 0.78))):02X}" for channel in rgb)
        except Exception:
            wrap = "292929"
        accent, text_color, text_shadow = "FFE900", "FFFFFF", "0 0 2px #000"
    return {
        "wrap": wrap,
        "selected": selected,
        "accent": accent,
        "text": text_color,
        "shadow": text_shadow,
    }

IS_WINDOWS = sys.platform.startswith("win")


def resolve_runtime_data_path(path):
    if path and os.path.exists(path):
        return path
    try:
        rel = os.path.relpath(path, DATA_DIR)
        if not rel.startswith(".."):
            alt = os.path.normpath(os.path.join(BUNDLE_DATA_DIR, rel))
            if os.path.exists(alt):
                return alt
    except Exception:
        pass
    try:
        alt = os.path.join(BUNDLE_DATA_DIR, os.path.basename(path))
        if os.path.exists(alt):
            return alt
    except Exception:
        pass
    return path


def set_template_dir_override(path):
    global TEMPLATE_DIR_OVERRIDE
    TEMPLATE_DIR_OVERRIDE = (path or "").strip()


def resolve_runtime_text_path(path):
    if path and os.path.exists(path):
        return path
    if TEMPLATE_DIR_OVERRIDE:
        alt = os.path.join(TEMPLATE_DIR_OVERRIDE, os.path.basename(path or ""))
        if os.path.exists(alt):
            return alt
    return resolve_runtime_data_path(path)


def load_json(path):
    p = resolve_runtime_data_path(path)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class DuplicateJsonKeyError(ValueError):
    pass


def strict_json_loads(raw_text):
    def _hook(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise DuplicateJsonKeyError(f"중복 키 발견: {k}")
            out[k] = v
        return out

    return json.loads(raw_text, object_pairs_hook=_hook)


def safe_save_json(path, data):
    # Prevent data loss: backup current file then atomically replace.
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    backup_path = path + ".bak"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as src, open(backup_path, "w", encoding="utf-8") as dst:
                dst.write(src.read())
        except Exception:
            pass

    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


def dedupe_json_data(value):
    # Recursively remove duplicate list items while preserving order.
    if isinstance(value, dict):
        return {k: dedupe_json_data(v) for k, v in value.items()}
    if isinstance(value, list):
        out = []
        seen = set()
        for item in value:
            norm = dedupe_json_data(item)
            try:
                key = json.dumps(norm, ensure_ascii=False, sort_keys=True)
            except Exception:
                key = str(norm)
            if key in seen:
                continue
            seen.add(key)
            out.append(norm)
        return out
    return value


def load_text(path):
    p = resolve_runtime_text_path(path)
    with open(p, "r", encoding="utf-8") as f:
        return f.read().lstrip("\ufeff")


def render_template(template_text, context):
    text = template_text or ""
    for key, value in context.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    # Remove template comment lines (namuwiki comments).
    text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("##"))
    return text


def wrap_folding_block(block_text):
    body = (block_text or "").strip()
    if not body:
        return ""
    lines = body.splitlines()
    if len(lines) <= 1:
        return "|| {{{#!folding [ 보기 · 닫기 ]\n" + body + "\n}}} ||"
    head = lines[0].rstrip()
    tail = "\n".join(lines[1:]).strip()
    if not tail:
        return head
    return head + "\n|| {{{#!folding [ 보기 · 닫기 ]\n" + tail + "\n}}} ||"


def normalize_token(v):
    return (v or "").strip().lower()


def dedupe_preserve_order(items, key_fn=None):
    seen = set()
    out = []
    for item in (items or []):
        key = key_fn(item) if key_fn else item
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def get_db_rules(db):
    if not isinstance(db, dict):
        db = {}
    rules = db.get("rules", {})
    if not isinstance(rules, dict):
        rules = {}
    bomber = rules.get("bomber", {})
    if not isinstance(bomber, dict):
        bomber = {}
    return {
        "ap_trait_keys": [normalize_token(x) for x in bomber.get("ap_trait_keys", ["ap bomb", "ap bombs", "armor piercing bomb", "armor-piercing bomb"])],
        "carpet_trait_keys": [normalize_token(x) for x in bomber.get("carpet_trait_keys", ["carpet bombing"])],
        "low_alt_trait_keys": [normalize_token(x) for x in bomber.get("low_alt_trait_keys", ["skip bombers", "skip bomber"])],
        "bomb_type_default_ko": bomber.get("bomb_type_default_ko", "고폭탄"),
        "bomb_type_ap_ko": bomber.get("bomb_type_ap_ko", "철갑탄"),
        "mode_carpet_ko": bomber.get("mode_carpet_ko", "융단"),
        "mode_low_alt_ko": bomber.get("mode_low_alt_ko", "저공"),
    }


def pick_preferred_stat(parts):
    # Expected format: [label, stock, upgraded]
    if len(parts) >= 3:
        upgraded = (parts[2] or "").strip()
        if upgraded and upgraded != "-":
            return upgraded
    return parts[1] if len(parts) >= 2 else ""


def parse_trait_names(raw_text):
    text = raw_text or ""
    lines = text.splitlines()
    names = []
    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        ll = line.lower()
        if "trait" not in ll or ".png" not in ll:
            continue
        # Find the next non-empty description line, e.g. "Pyromania: ..."
        for j in range(i + 1, min(i + 5, len(lines))):
            next_line = lines[j].strip()
            if not next_line:
                continue
            if ":" not in next_line:
                break
            name = next_line.split(":", 1)[0].strip()
            if not name:
                break
            low = name.lower()
            if low not in ("money maker", "moneymaker"):
                names.append(name)
            break
    return dedupe_preserve_order(names, key_fn=lambda x: normalize_token(x))


def translate_trait_name(name, db, lang="ko"):
    if not isinstance(db, dict):
        db = {}
    traits = db.get("traits", {})
    if not isinstance(traits, dict):
        traits = {}
    found = traits.get(name)
    if isinstance(found, dict):
        if lang == "ko":
            return found.get("ko") or found.get("en") or name
        return found.get("en") or found.get("ko") or name
    if isinstance(found, str):
        return found
    return name


def translate_trait_include(name, db, lang="ko"):
    token = normalize_token(name)
    # Blue/precision family override.
    if token in ("precise bombs", "precise bomb"):
        return "정밀 타격 포탄"

    traits = (db or {}).get("traits", {})
    if not isinstance(traits, dict):
        traits = {}

    found = traits.get(name)
    if found is None:
        for k, v in traits.items():
            if normalize_token(k) == token:
                found = v
                break

    if isinstance(found, dict):
        inc = (found.get("include") or "").strip()
        if inc:
            return inc
        if lang == "ko":
            return found.get("ko") or found.get("en") or name
        return found.get("en") or found.get("ko") or name
    if isinstance(found, str):
        return found
    return translate_trait_name(name, db, lang=lang)


def build_traits_block(trait_names_local, border_color):
    names = [t.strip() for t in (trait_names_local or []) if (t or "").strip()]
    if not names:
        return ""

    n = len(names)
    width = 100.0 / n

    def _fmt_width(v):
        s = f"{v:.3f}".rstrip("0").rstrip(".")
        return s if s else "0"

    header = (
        "||<-"
        + str(n)
        + "><tablewidth=100%><width=25%><table bordercolor=#"
        + border_color
        + "><#"
        + border_color
        + "> {{{#FFFFFF 특성}}} ||"
    )
    row = "||" + "".join(
        f"<width={_fmt_width(width)}%> [include(월드 오브 워쉽 레전드/특성/{nm})] ||"
        for nm in names
    )
    return header + "\n" + row


def parse_main_battery(raw_text):
    text = raw_text or ""
    start = text.find("MAIN BATTERY")
    if start < 0:
        return {}
    tail = text[start:]

    stop_tokens = [
        "Secondary Artillery",
        "SECONDARY ARMAMENT",
        "SECONDARY ARTILLERY",
        "Torpedoes",
        "TORPEDOES",
        "Bomb Airstrike",
        "BOMB AIRSTRIKE",
        "Anti-Aircraft Artillery",
        "AA ARMAMENT",
        "WoWsLIconBlack.pngModules",
        "Modules",
    ]
    stop_at = len(tail)
    for token in stop_tokens:
        p = tail.find(token)
        if p >= 0:
            stop_at = min(stop_at, p)
    section = tail[:stop_at]

    data = {}
    for raw_line in section.splitlines():
        line = raw_line.strip()
        # Example: "• Main artillery name\t152mm/53 Bofors M42\t-"
        line = re.sub(r"^[^\w]+", "", line).strip()
        if not line:
            continue
        parts = [p.strip() for p in re.split(r"\t+", line) if p.strip()]
        if len(parts) < 2:
            parts = [p.strip() for p in re.split(r"\s{2,}", line) if p.strip()]
        if len(parts) < 2:
            continue
        key = parts[0].lower()
        val = pick_preferred_stat(parts)
        if key in ("main battery",):
            continue
        data[key] = val
        if len(parts) >= 3:
            data[f"{key}__stock"] = (parts[1] or "").strip()
            data[f"{key}__upgraded"] = (parts[2] or "").strip()
    return data


def fmt_num_with_comma(v):
    s = (v or "").strip()
    if not s:
        return ""
    s = s.replace(" ", "")
    if re.fullmatch(r"\d+", s):
        try:
            return f"{int(s):,}"
        except Exception:
            return s
    return s


def fmt_unit_or_x(v, unit):
    s = (v or "").strip()
    if not s:
        return unit
    if s.lower() == "x":
        return "x"
    return f"{s}{unit}"


def parse_number(v):
    s = (v or "").strip().replace(",", "").replace(" ", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def build_main_battery_block(main_bat, border_color, ship_name_en=""):
    def _has_value(v):
        s = (v or "").strip()
        return bool(s and s not in ("-", "~", "x", "X"))

    has_ready_rack = bool(
        (main_bat.get("ready rack reload time (sec)", "") or "").strip()
        or (main_bat.get("shells in ready rack", "") or "").strip()
    )
    try:
        template_path = DEFAULT_MAIN_BATTERY_READY_RACK_TEMPLATE_PATH if has_ready_rack else DEFAULT_MAIN_BATTERY_TEMPLATE_PATH
        template = load_text(template_path)
    except Exception:
        template = ""

    names = []
    arrs = []
    i = 1
    while True:
        suffix = "" if i == 1 else f" {i}"
        n = main_bat.get(f"main artillery name{suffix}", "")
        a = main_bat.get(f"main artillery arrangement{suffix}", "")
        if not n and not a:
            break
        if n:
            names.append(n)
        if a:
            arrs.append(a.replace("x", "×").replace("X", "×"))
        i += 1

    name = " [br] ".join(names) if names else main_bat.get("main artillery name", "")
    arrangement = " [br] ".join(arrs) if arrs else (
        main_bat.get("main artillery arrangement", "")
        .replace("x", "×")
        .replace("X", "×")
    )
    reload_t = main_bat.get("reload time (sec)", "")
    turn180 = (
        main_bat.get("180° turn time (sec)", "")
        or main_bat.get("180? turn time (sec)", "")
        or main_bat.get("180 turn time (sec)", "")
    )
    firing_range = main_bat.get("firing range (km)", "")
    sigma = main_bat.get("sigma", "")
    he_dmg = fmt_num_with_comma(main_bat.get("he maximum damage", ""))
    he_fire = (main_bat.get("he fire chance (%)", "") or "").strip()
    he_pen = (main_bat.get("he penetration (mm)", "") or "").strip()
    sap_dmg = fmt_num_with_comma(main_bat.get("sap maximum damage", ""))
    sap_pen = (main_bat.get("sap penetration (mm)", "") or "").strip()
    ap_dmg = fmt_num_with_comma(main_bat.get("ap maximum damage", ""))
    ready_rack_reload = (main_bat.get("ready rack reload time (sec)", "") or "").strip()
    ready_rack_shells = (main_bat.get("shells in ready rack", "") or "").strip()

    # SAP split mode: when HE exists only in stock and SAP exists only in upgraded,
    # render two sequential gun blocks (normal + SAP) as requested.
    def _norm_stat(v):
        s = (v or "").strip()
        return "" if s == "-" else s

    he_dmg_stock = _norm_stat(main_bat.get("he maximum damage__stock", ""))
    he_dmg_up = _norm_stat(main_bat.get("he maximum damage__upgraded", ""))
    he_fire_stock = _norm_stat(main_bat.get("he fire chance (%)__stock", ""))
    he_fire_up = _norm_stat(main_bat.get("he fire chance (%)__upgraded", ""))
    he_pen_stock = _norm_stat(main_bat.get("he penetration (mm)__stock", ""))
    he_pen_up = _norm_stat(main_bat.get("he penetration (mm)__upgraded", ""))
    ap_dmg_stock = _norm_stat(main_bat.get("ap maximum damage__stock", ""))
    ap_dmg_up = _norm_stat(main_bat.get("ap maximum damage__upgraded", ""))
    sap_dmg_stock = _norm_stat(main_bat.get("sap maximum damage__stock", ""))
    sap_dmg_up = _norm_stat(main_bat.get("sap maximum damage__upgraded", ""))
    sap_pen_stock = _norm_stat(main_bat.get("sap penetration (mm)__stock", ""))
    sap_pen_up = _norm_stat(main_bat.get("sap penetration (mm)__upgraded", ""))
    reload_stock = _norm_stat(main_bat.get("reload time (sec)__stock", ""))
    reload_up = _norm_stat(main_bat.get("reload time (sec)__upgraded", ""))
    # Render dual main-battery blocks only for module-switch pattern:
    # stock has HE, upgraded has SAP, and AP exists.
    split_sap_mode = bool(
        not has_ready_rack
        and (he_dmg_stock or he_fire_stock or he_pen_stock)
        and (not (he_dmg_up or he_fire_up or he_pen_up))
        and (sap_dmg_up or sap_pen_up)
        and (not (sap_dmg_stock or sap_pen_stock))
        and (ap_dmg_stock or ap_dmg_up or ap_dmg)
        and (reload_stock or reload_t)
        and (reload_up or reload_t)
    )
    if split_sap_mode:
        class_ship_name = re.sub(r"[^A-Za-z0-9]+", "", ship_name_en or "") or "Ship"
        class_prefix = f"main{class_ship_name}"
        button_palette = get_nation_button_palette(border_color)
        name2 = f"{name} (SAP)" if name else "주함포 (SAP)"
        ap_damage_cell = fmt_num_with_comma(ap_dmg_up or ap_dmg_stock or ap_dmg) or "-"
        he_damage_cell = fmt_num_with_comma(he_dmg_stock or he_dmg) or "-"
        sap_damage_cell = fmt_num_with_comma(sap_dmg_up or sap_dmg) or "-"
        he_fire_cell = f"{he_fire_stock}%" if he_fire_stock else "-"
        he_pen_cell = f"{he_pen_stock}mm" if he_pen_stock else "-"
        sap_pen_cell = f"{sap_pen_up}mm" if sap_pen_up else "-"
        range_cell = firing_range or ""
        sigma_cell = sigma or ""
        turn_cell = turn180 or ""
        reload1_cell = reload_stock or reload_t or ""
        reload2_cell = reload_up or reload_t or ""
        block = (
            "{{{#!style\n"
            ".__CLASS__BtnWrap {background-color: #__WRAP_COLOR__; display: flex; flex-wrap: nowrap; width: 320px; width: min(100%, calc(460px - 10vw)); min-width: 280px; max-width: 100%; margin: 0 0 -10px; justify-content: start; border-radius: 6px 6px 0 0; box-sizing: border-box;}\n"
            ".__CLASS__Btn {display: flex; flex: 1 1 50%; width: 50%; color: #fff; border-bottom: 6px solid transparent; text-align: center; padding: 4px 8px; border-radius: 0; box-sizing: border-box; cursor: pointer;}\n"
            ".__CLASS__BtnHE {border-radius: 6px 0 0 0;}\n"
            ".__CLASS__BtnSAP {border-radius: 0 6px 0 0;}\n"
            ".__CLASS__BtnSelected {background-color: #__SELECTED_COLOR__; border-bottom: 6px solid #__ACCENT_COLOR__; color: #__SELECTED_TEXT_COLOR__; font-weight: bold; text-shadow: __SELECTED_TEXT_SHADOW__;}\n"
            ".__CLASS__Hide {display: none;}\n"
            "}}}\n"
            "{{{#!wiki class=\"__CLASS__BtnWrap\"\n"
            "{{{#!wiki class=\"__CLASS__Btn __CLASS__BtnHE __CLASS__BtnSelected\" onclick=\"remove-class,__CLASS__Btn,__CLASS__BtnSelected;add-class,__CLASS__BtnHE,__CLASS__BtnSelected;add-class,__CLASS__Content,__CLASS__Hide;remove-class,__CLASS__HE,__CLASS__Hide\"\n"
            "{{{#!wiki style=\"margin: auto;\"\n"
            "HE}}}}}}{{{#!wiki class=\"__CLASS__Btn __CLASS__BtnSAP\" onclick=\"remove-class,__CLASS__Btn,__CLASS__BtnSelected;add-class,__CLASS__BtnSAP,__CLASS__BtnSelected;add-class,__CLASS__Content,__CLASS__Hide;remove-class,__CLASS__SAP,__CLASS__Hide\"\n"
            "{{{#!wiki style=\"margin: auto;\"\n"
            "SAP}}}}}}}}}{{{#!wiki class=\"__CLASS__Content __CLASS__HE\"\n"
            "||<tablewidth=100%><table bordercolor=#__BC__><#__BC__><-4> {{{#FFFFFF 주함포}}} ||\n"
            "||<#__BC__><width=10%> {{{#FFFFFF 명칭}}} ||<width=90%><-3> __NAME1__ ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 포대}}} ||<#__BC__><width=30%> {{{#FFFFFF 탑재 수}}} ||<#__BC__><width=30%> {{{#FFFFFF 장전 시간}}} ||<#__BC__><width=30%> {{{#FFFFFF 180도 회전 시간}}} ||\n"
            "|| __ARR__ || __RELOAD1__초 || __TURN__초 ||\n"
            "||<-3> {{{#!wiki style=\"margin: -16px -11px;\" \n"
            "||<-2><#__BC__><tablewidth=100%><width=50%> {{{#FFFFFF 사거리}}} ||<-2><#__BC__><width=50%> {{{#FFFFFF 시그마}}} ||\n"
            "||<-2> __RANGE__km ||<-2> __SIGMA__ ||}}} ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 포탄}}} ||<-3> {{{#!wiki style=\"margin: -16px -11px;\" \n"
            "||<#__BC__><tablewidth=100%><width=25%> {{{#FFFFFF 탄종}}} ||<#__BC__><width=25%> {{{#FFFFFF 최대 공격력}}} ||<#__BC__><width=25%> {{{#FFFFFF 화재 확률}}} ||<#__BC__><width=25%> {{{#FFFFFF 관통력}}} ||\n"
            "|| 고폭탄 || __HE_DMG__ || __HE_FIRE__ || __HE_PEN__ ||\n"
            "|| 철갑탄 || __AP_DMG__ || || ~ ||}}} ||\n"
            "}}}{{{#!wiki class=\"__CLASS__Content __CLASS__SAP __CLASS__Hide\"\n"
            "||<tablewidth=100%><table bordercolor=#__BC__><#__BC__><-4> {{{#FFFFFF 주함포}}} ||\n"
            "||<#__BC__><width=10%> {{{#FFFFFF 명칭}}} ||<width=90%><-3> __NAME2__ ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 포대}}} ||<#__BC__><width=30%> {{{#FFFFFF 탑재 수}}} ||<#__BC__><width=30%> {{{#FFFFFF 장전 시간}}} ||<#__BC__><width=30%> {{{#FFFFFF 180도 회전 시간}}} ||\n"
            "|| __ARR__ || __RELOAD2__초 || __TURN__초 ||\n"
            "||<-3> {{{#!wiki style=\"margin: -16px -11px;\" \n"
            "||<-2><#__BC__><tablewidth=100%><width=50%> {{{#FFFFFF 사거리}}} ||<-2><#__BC__><width=50%> {{{#FFFFFF 시그마}}} ||\n"
            "||<-2> __RANGE__km ||<-2> __SIGMA__ ||}}} ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 포탄}}} ||<-3> {{{#!wiki style=\"margin: -16px -11px;\" \n"
            "||<#__BC__><tablewidth=100%><width=25%> {{{#FFFFFF 탄종}}} ||<#__BC__><width=25%> {{{#FFFFFF 최대 공격력}}} ||<#__BC__><width=25%> {{{#FFFFFF 화재 확률}}} ||<#__BC__><width=25%> {{{#FFFFFF 관통력}}} ||\n"
            "|| 반철갑탄 || __SAP_DMG__ || - || __SAP_PEN__ ||\n"
            "|| 철갑탄 || __AP_DMG__ || || ~ ||}}} ||\n"
            "}}}"
        )
        return (
            block.replace("__CLASS__", class_prefix)
            .replace("__WRAP_COLOR__", button_palette["wrap"])
            .replace("__SELECTED_COLOR__", button_palette["selected"])
            .replace("__ACCENT_COLOR__", button_palette["accent"])
            .replace("__SELECTED_TEXT_COLOR__", button_palette["text"])
            .replace("__SELECTED_TEXT_SHADOW__", button_palette["shadow"])
            .replace("__BC__", border_color)
            .replace("__NAME1__", name)
            .replace("__NAME2__", name2)
            .replace("__ARR__", arrangement)
            .replace("__RELOAD1__", reload1_cell)
            .replace("__RELOAD2__", reload2_cell)
            .replace("__TURN__", turn_cell)
            .replace("__SIGMA__", sigma_cell)
            .replace("__RANGE__", range_cell)
            .replace("__HE_DMG__", he_damage_cell)
            .replace("__HE_FIRE__", he_fire_cell)
            .replace("__HE_PEN__", he_pen_cell)
            .replace("__SAP_DMG__", sap_damage_cell)
            .replace("__SAP_PEN__", sap_pen_cell)
            .replace("__AP_DMG__", ap_damage_cell)
        )

    has_sap = _has_value(sap_dmg) or _has_value(sap_pen)
    has_he = _has_value(he_dmg) or _has_value(he_pen) or _has_value(he_fire)
    has_ap = _has_value(ap_dmg)
    he_sap_no_ap_mode = has_he and has_sap and (not has_ap) and (not has_ready_rack)
    ap_only_mode = has_ap and (not has_he) and (not has_sap)
    if he_sap_no_ap_mode:
        he_damage_cell = he_dmg or "x"
        he_fire_cell = (he_fire + "%") if he_fire else "x"
        he_pen_cell = (he_pen + "mm") if he_pen else "x"
        sap_damage_cell = sap_dmg or "x"
        sap_pen_cell = (sap_pen + "mm") if sap_pen else "x"
        block = (
            "||<tablewidth=100%><table bordercolor=#__BC__><#__BC__><-4> {{{#FFFFFF 주함포}}} ||\n"
            "||<#__BC__><width=10%> {{{#FFFFFF 명칭}}} ||<width=90%><-3> __NAME__ ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 포대}}} ||<#__BC__><width=30%> {{{#FFFFFF 탑재 수}}} ||<#__BC__><width=30%> {{{#FFFFFF 장전 시간}}} ||<#__BC__><width=30%> {{{#FFFFFF 180도 회전 시간}}} ||\n"
            "|| __ARR__ || __RELOAD__초 || __TURN__초 ||\n"
            "||<-3> {{{#!wiki style=\"margin: -16px -11px;\" \n"
            "||<-2><#__BC__><tablewidth=100%><width=50%> {{{#FFFFFF 사거리}}} ||<-2><#__BC__><width=50%> {{{#FFFFFF 시그마}}} ||\n"
            "||<-2> __RANGE__km ||<-2> __SIGMA__ ||}}} ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 포탄}}} ||<-3> {{{#!wiki style=\"margin: -16px -11px;\" \n"
            "||<#__BC__><tablewidth=100%><width=25%> {{{#FFFFFF 탄종}}} ||<#__BC__><width=25%> {{{#FFFFFF 최대 공격력}}} ||<#__BC__><width=25%> {{{#FFFFFF 화재 확률}}} ||<#__BC__><width=25%> {{{#FFFFFF 관통력}}} ||\n"
            "|| 고폭탄 || __HE_DMG__ || __HE_FIRE__ || __HE_PEN__ ||\n"
            "|| 반철갑탄 || __SAP_DMG__ || - || __SAP_PEN__ ||}}} ||"
        )
        return (
            block.replace("__BC__", border_color)
            .replace("__NAME__", name)
            .replace("__ARR__", arrangement)
            .replace("__RELOAD__", reload_t)
            .replace("__TURN__", turn180)
            .replace("__RANGE__", firing_range)
            .replace("__SIGMA__", sigma)
            .replace("__HE_DMG__", he_damage_cell)
            .replace("__HE_FIRE__", he_fire_cell)
            .replace("__HE_PEN__", he_pen_cell)
            .replace("__SAP_DMG__", sap_damage_cell)
            .replace("__SAP_PEN__", sap_pen_cell)
        )
    if has_sap and not has_he:
        primary_shell = "반철갑탄"
        primary_damage = sap_dmg or "x"
        primary_fire = "x"
        primary_pen = (sap_pen + "mm") if sap_pen else "x"
    elif has_ap and not has_he and not has_sap:
        primary_shell = "철갑탄"
        primary_damage = ap_dmg
        primary_fire = "-"
        primary_pen = "-"
    else:
        primary_shell = "고폭탄"
        primary_damage = he_dmg or "x"
        primary_fire = (he_fire + "%") if he_fire else "x"
        primary_pen = (he_pen + "mm") if he_pen else "x"
    out = render_template(
        template,
        {
            "border_color": border_color,
            "main_name": name,
            "main_arrangement": arrangement,
            "main_reload_sec": reload_t,
            "main_turn180_sec": turn180,
            "main_range_km": firing_range,
            "main_sigma": sigma,
            "main_primary_shell": primary_shell,
            "main_primary_damage": primary_damage,
            "main_primary_fire": primary_fire,
            "main_primary_pen": primary_pen,
            "main_ap_damage": ap_dmg,
            "main_ready_rack_reload_sec": f"{ready_rack_reload}초" if ready_rack_reload else "초",
            "main_ready_rack_shells": f"{ready_rack_shells}발" if ready_rack_shells else "발",
        },
    )
    # If AP shell data doesn't exist, hide the template's fixed AP row.
    if not has_ap:
        out = re.sub(r"\n\|\|\s*철갑탄\s*\|\|.*?\|\|\s*\|\|\s*[~\-xX]*\s*\|\|", "", out, count=1)
    # AP-only case: remove the primary row and keep the fixed AP row only once.
    if ap_only_mode:
        out = re.sub(r"\n\|\|\s*철갑탄\s*\|\|.*?\|\|.*?\|\|.*?\|\|", "", out, count=1)
    return out


def build_simple_block(template_path, border_color):
    try:
        template = load_text(template_path)
    except Exception:
        return ""
    return render_template(template, {"border_color": border_color})


def has_section(raw_text, patterns):
    text = raw_text or ""
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
            return True
    return False


def parse_key_values_between(raw_text, start_patterns, stop_patterns):
    text = raw_text or ""
    lines = text.splitlines()
    start_idx = -1
    for i, line in enumerate(lines):
        line_s = line.strip()
        for pat in start_patterns:
            if re.search(pat, line_s, re.IGNORECASE):
                start_idx = i
                break
        if start_idx >= 0:
            break
    if start_idx < 0:
        return {}

    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        line_s = lines[j].strip()
        for pat in stop_patterns:
            if re.search(pat, line_s, re.IGNORECASE):
                end_idx = j
                break
        if end_idx != len(lines):
            break

    data = {}
    for line in lines[start_idx:end_idx]:
        s = re.sub(r"^[^\w]+", "", line).strip()
        if not s:
            continue
        parts = [p.strip() for p in re.split(r"\t+", s) if p.strip()]
        if len(parts) < 2:
            parts = [p.strip() for p in re.split(r"\s{2,}", s) if p.strip()]
        if len(parts) < 2:
            continue
        key = parts[0].lower()
        val = pick_preferred_stat(parts)
        if key in ("stock", "upgraded"):
            continue
        data[key] = val
    return data


def parse_surv_maneuver_conceal(raw_text):
    surv = parse_key_values_between(
        raw_text,
        [r"^Survivability\b", r"^SURVIVBILITY\b", r"^SURVIVABILITY\b"],
        [r"^Maneuverability\b", r"^MANEUVERABILITY\b"],
    )
    man = parse_key_values_between(
        raw_text,
        [r"^Maneuverability\b", r"^MANEUVERABILITY\b"],
        [r"^Concealment\b", r"^CONCEALMENT\b"],
    )
    con = parse_key_values_between(
        raw_text,
        [r"^Concealment\b", r"^CONCEALMENT\b"],
        [r"^Bomb Airstrike\b", r"^BOMB AIRSTRIKE\b", r"^Main Artillery\b", r"^MAIN BATTERY\b"],
    )
    def _extract_preferred_stat(label):
        text = raw_text or ""
        # Prefer explicit tab columns: LABEL<TAB>STOCK<TAB>UPGRADED
        pat_tab = rf"^\s*(?:[^\w\r\n]+)?{re.escape(label)}\s*\t([^\t\r\n]*)\t([^\t\r\n]*)"
        m = re.search(pat_tab, text, re.IGNORECASE | re.MULTILINE)
        if m:
            stock = (m.group(1) or "").strip()
            upgraded = (m.group(2) or "").strip()
            return upgraded if upgraded and upgraded not in ("-", "–", "—") else stock

        # Fallback: split by 2+ spaces.
        pat_sp = rf"^\s*(?:[^\w\r\n]+)?{re.escape(label)}\s+([^\r\n]*?)\s{{2,}}([^\r\n]*)$"
        m = re.search(pat_sp, text, re.IGNORECASE | re.MULTILINE)
        if m:
            stock = (m.group(1) or "").strip()
            upgraded = (m.group(2) or "").strip()
            return upgraded if upgraded and upgraded not in ("-", "–", "—") else stock
        return ""

    def _clean_km_value(v):
        s = (v or "").strip()
        if not s:
            return ""
        nums = re.findall(r"\d+(?:\.\d+)?", s)
        if not nums:
            return s
        # Keep the most plausible stat token when source text is malformed/merged.
        return max(nums, key=lambda x: (len(x), float(x)))

    for label, key in (
        ("Detectability by sea (km)", "detectability by sea (km)"),
        ("Detectability by air (km)", "detectability by air (km)"),
        ("Detectability while firing in smoke (km)", "detectability while firing in smoke (km)"),
    ):
        v = _extract_preferred_stat(label)
        if v:
            con[key] = _clean_km_value(v)
    return {"surv": surv, "man": man, "con": con}


def parse_bomb_airstrike(raw_text):
    return parse_key_values_between(
        raw_text,
        [r"^Bomb Airstrike\b", r"^BOMB AIRSTRIKE\b"],
        [r"^Main Artillery\b", r"^MAIN BATTERY\b", r"^Anti-Aircraft Artillery\b", r"^AA ARMAMENT\b"],
    )


def parse_torpedo_airstrike(raw_text):
    return parse_key_values_between(
        raw_text,
        [r"^Torpedo Airstrike\b", r"^TORPEDO AIRSTRIKE\b"],
        [r"^Main Artillery\b", r"^MAIN BATTERY\b", r"^Anti-Aircraft Artillery\b", r"^AA ARMAMENT\b"],
    )


def parse_aa_armaments(raw_text):
    text = raw_text or ""
    lines = text.splitlines()
    rows = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.search(r"^AA ARMAMENT\s+\d+", line, re.IGNORECASE):
            row = {}
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if re.search(r"^AA ARMAMENT\s+\d+", s, re.IGNORECASE):
                    break
                if re.search(r"^WoWsLIconBlack\.pngModules|^Modules\b", s, re.IGNORECASE):
                    break
                s2 = re.sub(r"^[^\w]+", "", s).strip()
                parts = [p.strip() for p in re.split(r"\t+", s2) if p.strip()]
                if len(parts) < 2:
                    parts = [p.strip() for p in re.split(r"\s{2,}", s2) if p.strip()]
                if len(parts) >= 2:
                    key = parts[0].lower()
                    # AA values must be a single chosen stat (upgraded preferred, else stock).
                    val = pick_preferred_stat(parts)
                    # Guard against malformed merged values like "218 315" -> pick upgraded-side token.
                    if key in ("dps", "range (km)") and re.search(r"\d+\s+\d+", val):
                        nums = re.findall(r"\d+(?:\.\d+)?", val)
                        if nums:
                            val = nums[-1]
                    row[key] = val
                j += 1
            rows.append(row)
            i = j
            continue
        i += 1
    return rows


def build_surv_maneuver_conceal_block(stats, border_color, ship_class=""):
    try:
        template = load_text(DEFAULT_SURV_MANEUVER_CONCEAL_TEMPLATE_PATH)
    except Exception:
        return ""
    surv = stats.get("surv", {})
    man = stats.get("man", {})
    con = stats.get("con", {})
    armor = (surv.get("armor (mm)", "") or "").replace(" - ", "~")
    smoke_raw = con.get("detectability while firing in smoke (km)", "")
    is_carrier = normalize_token(ship_class) == "aircraft carrier"
    detect_smoke_cell = "x" if is_carrier else (f"{smoke_raw}km" if smoke_raw else "km")
    return render_template(
        template,
        {
            "border_color": border_color,
            "hitpoints": fmt_num_with_comma(surv.get("hitpoints", "")),
            "torpedo_reduction": surv.get("torpedo damage reduction (%)", ""),
            "armor_range": armor,
            "turning_radius_m": man.get("turning circle radius (m)", ""),
            "rudder_shift_sec": man.get("rudder-shift time (sec)", ""),
            "max_speed_kt": man.get("maximum speed (kt)", ""),
            "detect_sea_km": con.get("detectability by sea (km)", ""),
            "detect_air_km": con.get("detectability by air (km)", ""),
            "detect_smoke_cell": detect_smoke_cell,
        },
    )


def build_airstrike_block(air, border_color, mode="bomb"):
    try:
        template = load_text(DEFAULT_AIRSTRIKE_TEMPLATE_PATH)
    except Exception:
        return ""
    is_torpedo = normalize_token(mode) == "torpedo"
    if is_torpedo:
        payload_total_raw = air.get("torpedoes in payload", "")
    else:
        payload_total_raw = air.get("bombs in payload", "")

    payload_per_plane = (payload_total_raw or "").strip()
    if not payload_per_plane:
        payload_total = parse_number(payload_total_raw)
        aircraft_per_sq_raw = air.get("aircraft per squadron", "")
        aircraft_per_sq = parse_number(aircraft_per_sq_raw)
        if payload_total is not None and aircraft_per_sq not in (None, 0):
            v = payload_total / aircraft_per_sq
            if abs(v - round(v)) < 1e-9:
                payload_per_plane = str(int(round(v)))
            else:
                payload_per_plane = f"{v:.2f}".rstrip("0").rstrip(".")

    total_squadrons = (air.get("total squadrons", "") or "").strip()
    if not total_squadrons:
        total_squadrons = "1"

    if is_torpedo:
        weapon_header = (
            "<#__BC__><width=17.5%> {{{#FFFFFF 어뢰 최대 공격력}}} ||"
            "<#__BC__><width=18.75%> {{{#FFFFFF 어뢰 사거리}}} ||"
            "<#__BC__><width=17.5%> {{{#FFFFFF 어뢰 속력}}} ||"
            "<#__BC__><width=17.5%> {{{#FFFFFF 적재량}}}"
        ).replace("__BC__", border_color)
        torp_damage = fmt_num_with_comma(air.get("maximum torpedo damage", ""))
        torp_range = (air.get("torpedo range (km)", "") or "").strip()
        torp_speed = (air.get("torpedo speed (kt)", "") or "").strip()
        weapon_row = f" {torp_damage} || {torp_range}km || {torp_speed}knots || {payload_per_plane}발"
    else:
        weapon_header = (
            "<#__BC__><width=17.5%> {{{#FFFFFF 폭탄 최대 공격력}}} ||"
            "<#__BC__><width=17.5%> {{{#FFFFFF 폭탄 관통력 }}} ||"
            "<#__BC__><width=17.5%> {{{#FFFFFF 화재 확률}}} ||"
            "<#__BC__><width=17.5%> {{{#FFFFFF 적재량}}}"
        ).replace("__BC__", border_color)
        bomb_damage = fmt_num_with_comma(air.get("maximum bomb damage", ""))
        bomb_pen = (air.get("armor piercing (mm)", "") or "").strip()
        fire = (air.get("fire-setting chances (%)", "") or "").strip()
        weapon_row = f" {bomb_damage} || {bomb_pen}mm || {fire}% || {payload_per_plane}발"

    return render_template(
        template,
        {
            "border_color": border_color,
            "air_name": air.get("plane name", ""),
            "air_mode": "뇌격" if is_torpedo else "폭격",
            "air_hp": fmt_num_with_comma(air.get("hit points", "")),
            "air_speed": air.get("maximum speed (kt)", ""),
            "air_range": air.get("maximum attack range (km)", ""),
            "air_attack_units": air.get("attack unit size", ""),
            "air_total_squadrons": total_squadrons,
            "air_reload_sec": air.get("aircraft restoration time (sec)", "") or air.get("squadron restoration time (sec)", ""),
            "air_arrival_sec": air.get("payload delivery time (sec)", ""),
            "air_weapon_header": weapon_header,
            "air_weapon_row": weapon_row,
        },
    )


def translate_mod_name(name, db, lang="ko"):
    if not isinstance(db, dict):
        db = {}
    mods = db.get("mods", {})
    if not isinstance(mods, dict):
        mods = {}
    found = mods.get(name)
    if found is None:
        # Case-insensitive exact-key fallback.
        needle = (name or "").strip().lower()
        for k, v in mods.items():
            if (k or "").strip().lower() == needle:
                found = v
                break
    if isinstance(found, dict):
        if lang == "ko":
            return found.get("ko") or found.get("en") or name
        return found.get("en") or found.get("ko") or name
    if isinstance(found, str):
        return found
    return name


def translate_consumable_name(name, db, lang="ko"):
    def _norm(s):
        s = (s or "").strip().lower()
        s = s.replace("‑", "-").replace("–", "-").replace("—", "-")
        s = re.sub(r"\s+", " ", s)
        return s

    # Built-in aliases for newly added consumables that may be missing in DB.
    nn = _norm(name)
    try:
        rules = load_consumable_rules()
        _, rule = find_consumable_rule(name, rules)
        if rule:
            if lang == "ko":
                return rule.get("ko") or name
            return rule.get("en") or name
    except Exception:
        pass

    if not isinstance(db, dict):
        db = {}
    items = db.get("consumables", {})
    if not isinstance(items, dict):
        items = {}
    found = items.get(name)
    if found is None:
        needle = _norm(name)
        for k, v in items.items():
            if _norm(k) == needle:
                found = v
                break
    if isinstance(found, dict):
        if lang == "ko":
            return found.get("ko") or found.get("en") or name
        return found.get("en") or found.get("ko") or name
    if isinstance(found, str):
        return found
    return name


def _extract_first_number(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return m.group(0) if m else ""


def _norm_rule_key(value):
    s = (value or "").strip().lower()
    s = s.replace("‑", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s)


def load_consumable_rules():
    rules = {"targets": {}, "output": {}}
    target_files = {
        "normal": "normal.json",
        "cv_mothership": "cv_mothership.json",
        "cv_aircraft": "cv_aircraft.json",
    }
    for target_name, filename in target_files.items():
        path = os.path.join(DEFAULT_CONSUMABLES_RULES_DIR, filename)
        try:
            data = load_json(path)
        except Exception:
            data = {}
        if isinstance(data, dict):
            rules["targets"][target_name] = data

    output_path = os.path.join(DEFAULT_CONSUMABLES_RULES_DIR, "output.json")
    try:
        output = load_json(output_path)
    except Exception:
        output = {}
    if isinstance(output, dict):
        rules["output"] = output
    return rules


def validate_consumable_rule_files():
    paths = [
        os.path.join(DEFAULT_CONSUMABLES_RULES_DIR, "normal.json"),
        os.path.join(DEFAULT_CONSUMABLES_RULES_DIR, "cv_mothership.json"),
        os.path.join(DEFAULT_CONSUMABLES_RULES_DIR, "cv_aircraft.json"),
        os.path.join(DEFAULT_CONSUMABLES_RULES_DIR, "output.json"),
    ]
    for path in paths:
        load_json(path)


def _all_consumable_target_rules(rules, target_names=None):
    targets = rules.get("targets", {}) if isinstance(rules, dict) else {}
    if not isinstance(targets, dict):
        return []
    names = list(target_names or targets.keys())
    out = []
    for target_name in names:
        target = targets.get(target_name, {})
        consumables = target.get("consumables", {}) if isinstance(target, dict) else {}
        if not isinstance(consumables, dict):
            continue
        for source_name, rule in consumables.items():
            if isinstance(rule, dict):
                out.append((target_name, source_name, rule))
    return out


def find_consumable_rule(name, rules, target_names=None, ko_name=""):
    candidates = {_norm_rule_key(name), _norm_rule_key(ko_name)}
    candidates.discard("")
    for target_name, source_name, rule in _all_consumable_target_rules(rules, target_names=target_names):
        names = [source_name, rule.get("ko", "")]
        aliases = rule.get("aliases", [])
        if isinstance(aliases, list):
            names.extend(str(x) for x in aliases)
        if any(_norm_rule_key(x) in candidates for x in names):
            return target_name, rule
    return "", {}


def _compile_consumable_pattern(pattern):
    text = str(pattern or "")
    marker = "\u0000NUM\u0000"
    text = text.replace("{n}", marker)
    text = re.escape(text)
    text = text.replace(re.escape(marker), r"([+\-]?\d+(?:\.\d+)?)")
    text = re.sub(r"\\\s+", r"\\s*", text)
    return text


def _read_rule_value(match, rule):
    value = str(rule.get("value", "group:1") or "group:1")
    if value.startswith("literal:"):
        return value.split(":", 1)[1]
    if value.startswith("group:"):
        try:
            return match.group(int(value.split(":", 1)[1]))
        except Exception:
            return ""
    return value


def apply_external_consumable_parsers(name, detail_lines, rules):
    _, rule = find_consumable_rule(name, rules)
    if not rule:
        return {}
    blob = "\n".join(detail_lines or [])
    out = {}
    parsers = rule.get("parsers", [])
    if not isinstance(parsers, list):
        return out
    for parser_rule in parsers:
        if not isinstance(parser_rule, dict):
            continue
        field = (parser_rule.get("field", "") or "").strip()
        patterns = parser_rule.get("patterns", [])
        if not field or not isinstance(patterns, list):
            continue
        for pat in patterns:
            try:
                m = re.search(_compile_consumable_pattern(pat), blob, re.IGNORECASE)
            except Exception:
                m = None
            if m:
                out[field] = _read_rule_value(m, parser_rule)
                break
    return out


def render_consumable_rule_text(template, values):
    def repl(match):
        key = match.group(1)
        return str((values or {}).get(key, "") or "")

    return re.sub(r"\{([A-Za-z0-9_]+)\}", repl, template or "")


def consumable_count_text(count, output_rules=None, cv=False):
    output = output_rules or {}
    count = (count or "").strip()
    if count:
        if "무제한" in count or count.lower() == "unlimited":
            return output.get("unlimited", "무제한 소모품")
        m = re.search(r"\d+", count)
        if m:
            fmt = output.get("cv_count" if cv else "count", "사용횟수 {count}회")
            return render_consumable_rule_text(fmt, {"count": m.group(0)})
    return output.get("cv_missing_count" if cv else "missing_count", "사용횟수 회")


def consumable_timing_text(item, rules, cv=False):
    output = (rules or {}).get("output", {}) if isinstance(rules, dict) else {}
    values = dict(item or {})
    values["count_text"] = consumable_count_text(values.get("count", ""), output_rules=output, cv=cv)
    if values.get("dispersion_sec"):
        fmt = output.get("timing_with_dispersion", "지속 {duration}초 / 분산 {dispersion_sec}초 / 쿨타임 {reload}초 / {count_text}")
    else:
        fmt = output.get("timing", "지속 {duration}초 / 쿨타임 {reload}초 / {count_text}")
    return render_consumable_rule_text(fmt, values)


def consumable_description(item, rules, target_names=None, db=None, lang="ko"):
    name_en = item.get("name", "")
    fallback_name = translate_consumable_name(name_en, db, lang=lang) if name_en else ""
    _, rule = find_consumable_rule(name_en, rules, target_names=target_names, ko_name=fallback_name)
    name_local = rule.get("ko") or fallback_name or name_en
    if lang != "ko":
        desc = item.get("effect", "") or rule.get("description", "")
    else:
        desc = rule.get("description", "") or item.get("effect", "")
    return name_local, render_consumable_rule_text(desc, item)


def consumable_has_target(item, rules, target_names, db=None, lang="ko"):
    name_en = item.get("name", "")
    ko_name = translate_consumable_name(name_en, db, lang=lang) if name_en else ""
    _, rule = find_consumable_rule(name_en, rules, target_names=target_names, ko_name=ko_name)
    return bool(rule)


def parse_consumables(raw_text):
    text = raw_text or ""
    lines = [ln.strip() for ln in text.splitlines()]
    rules = load_consumable_rules()
    def _norm_token(v):
        return re.sub(r"[^a-z0-9]", "", (v or "").lower())

    # Section boundaries.
    start = -1
    end = len(lines)
    end_markers = [
        r"^(Commander|Skills|Boosters|Store|Bureau|Patch Notes|Captains?)\b",
        r"^(?:WoWsLIconBlack\.png)?\s*Content Links\b",
        r"^Categories:\b",
        r"^This page was last modified on\b",
        r"^Privacy policy\b",
        r"^Powered by MediaWiki\b",
    ]
    for i, s in enumerate(lines):
        if re.match(r"^(?:WoWsLIconBlack\.png)?\s*Consumables\b", s, re.IGNORECASE):
            start = i + 1
            continue
        if start >= 0:
            if any(re.match(pat, s, re.IGNORECASE) for pat in end_markers):
                end = i
                break
    if start < 0:
        return {}

    section = lines[start:end]
    slots = {}
    excluded_names = {
        "return to carrier",
    }

    i = 0
    while i < len(section):
        s = section[i]
        if not s:
            i += 1
            continue

        # Consumable icon line (exclude dpad icon lines).
        s_low = s.lower()
        s_norm = _norm_token(s)
        if ".png" in s_low and "dpad" not in s_norm and "wowlsiconblack" not in s_low:
            # Next non-empty line is name.
            j = i + 1
            while j < len(section) and not section[j]:
                j += 1
            if j >= len(section):
                break
            name = section[j]
            # Skip navigation/footer rows that can appear after the consumables block.
            if "|" in name and ("wows legends" in name.lower() or "all ships" in name.lower()):
                i = j + 1
                continue
            if (name or "").strip().lower() in excluded_names:
                i = j + 1
                continue

            # Find slot indicator line.
            k = j + 1
            slot_key = ""
            while k < len(section):
                t = section[k]
                tl = t.lower()
                tl_norm = _norm_token(t)
                if "dpadleft" in tl_norm:
                    slot_key = "left"
                    k += 1
                    break
                if "dpadup" in tl_norm:
                    slot_key = "up"
                    k += 1
                    break
                if "dpadright" in tl_norm:
                    slot_key = "right"
                    k += 1
                    break
                if "dpaddown" in tl_norm:
                    slot_key = "down"
                    k += 1
                    break
                if ".png" in tl and "dpad" not in tl_norm:
                    break
                k += 1
            if not slot_key:
                # Some sources omit D-pad markers or use unexpected variants.
                # In that case, details start immediately after the consumable name.
                k = j + 1

            effect = ""
            detail_lines = []
            duration = ""
            reload_time = ""
            count_text = ""
            while k < len(section):
                t = section[k]
                tl = t.lower()
                if not t:
                    k += 1
                    continue
                if re.match(r"^(?:WoWsLIconBlack\.png)?\s*Content Links\b", t, re.IGNORECASE):
                    break
                if re.match(r"^Categories:\b", t, re.IGNORECASE):
                    break
                if ".png" in tl and "dpad" not in _norm_token(t):
                    break
                if tl.startswith("duration:"):
                    duration = _extract_first_number(t)
                    k += 1
                    continue
                if tl.startswith("reload time:") or tl.startswith("cooldown time:"):
                    reload_time = _extract_first_number(t)
                    k += 1
                    continue
                if "unlimited" in tl and ("consumable" in tl or "number of consumables" in tl):
                    count_text = "무제한 소모품"
                    k += 1
                    continue
                if re.search(r"number of consumables", tl):
                    cnt = _extract_first_number(t)
                    count_text = f"소모품 사용 횟수 {cnt}회" if cnt else "소모품 사용 횟수"
                    k += 1
                    continue
                if re.search(r"\bcharges?\b", tl):
                    cnt = _extract_first_number(t)
                    count_text = f"소모품 사용 횟수 {cnt}회" if cnt else "소모품 사용 횟수"
                    k += 1
                    continue
                if not effect:
                    effect = t
                detail_lines.append(t)
                k += 1

            parsed_fields = {
                "ship_detect_km": "",
                "torpedo_detect_km": "",
                "avg_aa_pct": "",
                "max_speed_pct": "",
                "hp_per_sec": "",
                "torp_reload_to_sec": "",
                "main_reload_pct": "",
                "dispersion_sec": "",
                "sec_grouping_pct": "",
                "sec_dispersion_pct": "",
                "sec_reload_pct": "",
            }
            parsed_fields.update(apply_external_consumable_parsers(name, detail_lines, rules))

            item_data = {
                "name": name,
                "effect": effect,
                "details": detail_lines,
                "duration": duration,
                "reload": reload_time,
                "count": count_text,
            }
            item_data.update(parsed_fields)
            if slot_key:
                slots.setdefault(slot_key, []).append(item_data)
            else:
                slots.setdefault("auto", []).append(item_data)
            i = k
            continue

        i += 1

    return slots


def build_consumables_block(cons_slots, border_color, db=None, lang="ko"):
    if not cons_slots:
        return ""
    rules = load_consumable_rules()

    def row_item(item):
        name_local, desc = consumable_description(item, rules, target_names=["normal"], db=db, lang=lang)
        if not name_local:
            return "", ""
        timing = consumable_timing_text(item, rules, cv=False)
        full_desc = f"{desc} [br] {timing}".strip()
        return name_local, full_desc

    slot_meta = [
        ("left", "1번 [br] (패드 ←)"),
        ("up", "2번 [br] (패드 ↑)"),
        ("right", "3번 [br] (패드 →)"),
        ("down", "4번 [br] (패드 ↓)"),
    ]
    row_lines = []
    for key, slot_label in slot_meta:
        items = cons_slots.get(key, [])
        if isinstance(items, dict):
            items = [items]
        rows = []
        for item in items:
            n, full_desc = row_item(item)
            if any((n, full_desc)):
                rows.append((n, full_desc))
        rows = dedupe_preserve_order(
            rows,
            key_fn=lambda r: tuple(re.sub(r"\s+", " ", (x or "").strip()).lower() for x in r),
        )
        if not rows:
            continue
        if len(rows) == 1:
            n, full_desc = rows[0]
            row_lines.append(
                "||<bgcolor=#"
                + border_color
                + "> {{{#ffffff "
                + slot_label
                + "}}} || "
                + n
                + " || "
                + full_desc
                + " ||"
            )
        else:
            n, full_desc = rows[0]
            row_lines.append(
                "||<|"
                + str(len(rows))
                + "><bgcolor=#"
                + border_color
                + "> {{{#ffffff "
                + slot_label
                + "}}} || "
                + n
                + " || "
                + full_desc
                + " ||"
            )
            for n, full_desc in rows[1:]:
                row_lines.append("|| " + n + " || " + full_desc + " ||")

    header = (
        "||<-4><tablewidth=100%><table bordercolor=#"
        + border_color
        + "><bgcolor=#"
        + border_color
        + "> {{{#ffffff 소모품}}} ||"
    )
    cols = (
        "||<tablewidth=100%><table bordercolor=#"
        + border_color
        + "><bgcolor=#"
        + border_color
        + "><width=15%> {{{#ffffff 슬롯 위치}}} ||<bgcolor=#"
        + border_color
        + "><width=25%> {{{#ffffff 명칭}}} ||<bgcolor=#"
        + border_color
        + "><width=60%> {{{#ffffff 설명}}} ||"
    )
    return header + "\n" + cols + ("\n" + "\n".join(row_lines) if row_lines else "")


def build_cv_consumables_block(cons_slots, border_color, db=None, lang="ko"):
    def _row(item):
        name_local, effect = consumable_description(
            item,
            rules,
            target_names=["cv_mothership", "cv_aircraft", "normal"],
            db=db,
            lang=lang,
        )
        if not name_local:
            return None
        timing = consumable_timing_text(item, rules, cv=True)
        return (name_local, (effect + " [br] " + timing).strip())

    rules = load_consumable_rules()

    auto_rows = []
    aircraft_rows = []
    slot_labels = [
        ("left", "1번 [br] (패드 ←)"),
        ("up", "2번 [br] (패드 ↑)"),
        ("right", "3번 [br] (패드 →)"),
        ("down", "4번 [br] (패드 ↓)"),
    ]

    for items in (cons_slots or {}).values():
        if isinstance(items, dict):
            items = [items]
        for it in items:
            if not consumable_has_target(it, rules, ["cv_mothership"], db=db, lang=lang):
                continue
            rr = _row(it)
            if rr:
                auto_rows.append(rr)
    auto_rows = dedupe_preserve_order(
        auto_rows,
        key_fn=lambda r: tuple(re.sub(r"\s+", " ", (x or "").strip()).lower() for x in r),
    )
    if not auto_rows:
        target = ((rules.get("targets", {}) or {}).get("cv_mothership", {}) or {})
        for row in target.get("fallback_rows", []) or []:
            if not isinstance(row, dict):
                continue
            name_local = row.get("ko") or row.get("name", "")
            desc = render_consumable_rule_text(row.get("description", ""), row)
            full_desc = f"{desc} [br] {consumable_timing_text(row, rules, cv=True)}".strip()
            if name_local and full_desc:
                auto_rows.append((name_local, full_desc))

    for k, lab in slot_labels:
        items = (cons_slots or {}).get(k, [])
        if isinstance(items, dict):
            items = [items]
        for it in items:
            if consumable_has_target(it, rules, ["cv_mothership"], db=db, lang=lang):
                continue
            rr = _row(it)
            if rr:
                aircraft_rows.append((lab, rr[0], rr[1]))
    # Fallback: when source text misses D-pad markers, keep non-mothership consumables under aircraft.
    if not aircraft_rows:
        auto_items = (cons_slots or {}).get("auto", [])
        if isinstance(auto_items, dict):
            auto_items = [auto_items]
        for it in auto_items:
            if consumable_has_target(it, rules, ["cv_mothership"], db=db, lang=lang):
                continue
            rr = _row(it)
            if rr:
                aircraft_rows.append(("자동", rr[0], rr[1]))
    aircraft_rows = dedupe_preserve_order(
        aircraft_rows,
        key_fn=lambda r: tuple(re.sub(r"\s+", " ", (x or "").strip()).lower() for x in r),
    )

    lines = []
    if auto_rows:
        n = len(auto_rows)
        first = auto_rows[0]
        lines.append(
            "||<|"
            + str(n)
            + "><bgcolor=#"
            + border_color
            + "> {{{#ffffff 모함}}} ||<|"
            + str(n)
            + "><bgcolor=#"
            + border_color
            + "> {{{#ffffff 자동}}} || "
            + first[0]
            + " || "
            + first[1]
            + " ||"
        )
        for nm, full_desc in auto_rows[1:]:
            lines.append(
                "|| "
                + nm
                + " || "
                + full_desc
                + " ||"
            )

    if aircraft_rows:
        n = len(aircraft_rows)
        first = aircraft_rows[0]
        lines.append(
            "||<|"
            + str(n)
            + "><bgcolor=#"
            + border_color
            + "> {{{#ffffff 함재기}}} ||<bgcolor=#"
            + border_color
            + "> {{{#ffffff "
            + first[0]
            + "}}} || "
            + first[1]
            + " || "
            + first[2]
            + " ||"
        )
        for lab, nm, full_desc in aircraft_rows[1:]:
            lines.append(
                "||<bgcolor=#"
                + border_color
                + "> {{{#ffffff "
                + lab
                + "}}} || "
                + nm
                + " || "
                + full_desc
                + " ||"
            )

    if not lines:
        return ""
    header = (
        "||<-4><tablewidth=100%><table bordercolor=#"
        + border_color
        + "><bgcolor=#"
        + border_color
        + "> {{{#ffffff 소모품}}} ||"
    )
    cols = (
        "||<tablewidth=100%><table bordercolor=#"
        + border_color
        + "><bgcolor=#"
        + border_color
        + "><width=7.5%> {{{#ffffff 대상}}} ||<bgcolor=#"
        + border_color
        + "><width=7.5%> {{{#ffffff 슬롯 위치}}} ||<bgcolor=#"
        + border_color
        + "> {{{#ffffff 명칭}}} ||<bgcolor=#"
        + border_color
        + "> {{{#ffffff 효과}}} ||"
    )
    return header + "\n" + cols + "\n" + "\n".join(lines)


def build_consumables_list_block(cons_slots, border_color, db=None, lang="ko"):
    if not cons_slots:
        return ""
    try:
        template = load_text(DEFAULT_CONSUMABLES_LIST_TEMPLATE_PATH)
    except Exception:
        return ""

    by_ko = {}
    items_flat = []
    if isinstance(cons_slots, dict):
        for v in cons_slots.values():
            if isinstance(v, dict):
                items_flat.append(v)
            elif isinstance(v, list):
                for it in v:
                    if isinstance(it, dict):
                        items_flat.append(it)
    elif isinstance(cons_slots, list):
        for it in cons_slots:
            if isinstance(it, dict):
                items_flat.append(it)

    for item in items_flat:
        name_en = item.get("name", "")
        if not name_en:
            continue
        name_ko = translate_consumable_name(name_en, db, lang=lang)
        if name_ko:
            by_ko[name_ko] = item

    out_lines = []
    for raw in template.splitlines():
        line = raw
        skip_line = False
        if line.strip().startswith("||") and line.count("||") >= 3:
            cells = [c.strip() for c in line.split("||")[1:-1]]
            if len(cells) >= 2:
                row_name = cells[0]
                desc = cells[1]
                item = by_ko.get(row_name)
                if item:
                    duration = item.get("duration", "")
                    reload_t = item.get("reload", "")
                    count = item.get("count", "")
                    ship_detect = item.get("ship_detect_km", "")
                    torp_detect = item.get("torpedo_detect_km", "")
                    aa_pct = item.get("avg_aa_pct", "")
                    speed_pct = item.get("max_speed_pct", "")
                    hp_ps = item.get("hp_per_sec", "")
                    torp_to = item.get("torp_reload_to_sec", "")
                    main_rel = item.get("main_reload_pct", "")

                    if torp_detect:
                        desc = re.sub(r"어뢰 강제 탐지\s*km", f"어뢰 강제 탐지 {torp_detect}km", desc)
                    if ship_detect:
                        desc = re.sub(r"군함 강제 탐지\s*km", f"군함 강제 탐지 {ship_detect}km", desc)
                    if aa_pct:
                        desc = desc.replace("+%", f"+{aa_pct}%")
                    if speed_pct:
                        desc = re.sub(r"\+\s*%", f"+ {speed_pct}%", desc)
                        desc = re.sub(r"\+\s*%", f"+{speed_pct}%", desc)
                    if hp_ps:
                        desc = re.sub(r"초당\s*체력\s*\+\s*[+\-]?\d*(?:\.\d+)?", f"초당 체력 +{hp_ps}", desc)
                    if torp_to:
                        desc = desc.replace("n초", f"{torp_to}초")
                    if main_rel:
                        mr = str(main_rel).strip().rstrip("%").lstrip("+-")
                        if mr:
                            desc = re.sub(r"-\s*%", f"-{mr}%", desc)
                    if duration:
                        desc = re.sub(r"지속\s*초", f"지속 {duration}초", desc)
                    if reload_t:
                        desc = re.sub(r"쿨타임\s*초", f"쿨타임 {reload_t}초", desc)
                    if count:
                        desc = re.sub(r"사용횟수\s*회", count, desc)

                    line = f"|| {row_name} || {desc} ||"
                else:
                    # Keep only consumable rows that actually exist in parsed data.
                    skip_line = True
        if skip_line:
            continue
        out_lines.append(line)

    # If no data row survived, don't render the list block.
    data_rows = [ln for ln in out_lines if ln.strip().startswith("||") and ln.count("||") >= 3 and len([c for c in ln.split("||")[1:-1] if c.strip()]) >= 2]
    if not data_rows:
        return ""
    return render_template("\n".join(out_lines), {"border_color": border_color})


def parse_modifications(raw_text):
    text = raw_text or ""
    lines = text.splitlines()

    start = -1
    end = len(lines)
    is_cv_mods = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if re.search(r"^Modifications\s+for\s+Aircraft\s+Carriers?\b", s, re.IGNORECASE):
            start = i + 1
            is_cv_mods = True
            continue
        if re.search(r"^Modifications\b", s, re.IGNORECASE):
            start = i + 1
            is_cv_mods = False
            continue
        if start >= 0 and re.search(r"^Consumables\b", s, re.IGNORECASE):
            end = i
            break
    if start < 0:
        return {}

    slots = {1: [], 2: [], 3: [], 4: []}
    current_slot = None
    for ln in lines[start:end]:
        s = ln.strip()
        if not s:
            continue
        m = re.match(r"^SLOT\s+([1-4])\b", s, re.IGNORECASE)
        if m:
            current_slot = int(m.group(1))
            continue
        if current_slot is None:
            continue
        if ".png" in s.lower():
            continue
        if re.search(r"[+\-]\d|%|:\s|^\d", s):
            continue
        if len(s) <= 2:
            continue
        if s not in slots[current_slot]:
            slots[current_slot].append(s)
    out = {k: v for k, v in slots.items() if v}
    out["__is_cv__"] = is_cv_mods
    return out


def build_mods_block(mods_by_slot, border_color, db=None, lang="ko"):
    if not isinstance(mods_by_slot, dict):
        return ""

    is_cv_mods = bool(mods_by_slot.get("__is_cv__"))
    slot_to_section = {1: 2, 2: 3, 3: 5, 4: 6} if is_cv_mods else {1: 3, 2: 4, 3: 5, 4: 6}

    def _get_mod_meta(name):
        mods = db.get("mods", {}) if isinstance(db, dict) else {}
        found = mods.get(name) if isinstance(mods, dict) else None
        if found is None and isinstance(mods, dict):
            needle = (name or "").strip().lower()
            for k, v in mods.items():
                if (k or "").strip().lower() == needle:
                    found = v
                    break
        if isinstance(found, dict):
            return found
        return {}

    def _mod_local_name(name):
        meta = _get_mod_meta(name)
        if lang == "ko":
            return meta.get("ko") or meta.get("en") or name
        return meta.get("en") or meta.get("ko") or name

    def _build_img_cell(mod_name, slot_idx, row_idx):
        meta = _get_mod_meta(mod_name)
        img = (meta.get("img", "") if isinstance(meta, dict) else "") or ""
        img = img.strip()
        img_width = (str(meta.get("img_width", "")).strip() if isinstance(meta, dict) else "") or "50"
        if not img:
            return ""
        section = slot_to_section.get(slot_idx, 6)
        anchor = f"s-{section}.{row_idx}"
        target = f"월드 오브 워쉽 레전드/강화#{anchor}"
        if "월드 오브 워쉽 레전드/강화#" in img:
            return img
        if not img.startswith("[["):
            img_name = img.replace("파일:", "").strip()
            img = f"[[파일:{img_name}|width={img_width}]]"
        return f"[[{target}|{img}]]"

    slot_cells = {}
    max_rows = 0
    for i in (1, 2, 3, 4):
        names = mods_by_slot.get(i, [])
        if isinstance(names, str):
            names = [names]
        if not isinstance(names, list):
            names = []
        names = dedupe_preserve_order([n for n in names if (n or "").strip()], key_fn=lambda x: normalize_token(x))
        cells = []
        for idx, n in enumerate(names, start=1):
            cell = _build_img_cell(n, i, idx)
            if cell:
                cells.append(cell)
        slot_cells[i] = cells
        max_rows = max(max_rows, len(cells))

    if max_rows == 0:
        return ""

    title = "강화 장치(항모)" if is_cv_mods else "강화 장치"
    lines = [
        "||<-4><tablewidth=100%><table bordercolor=#"
        + border_color
        + "><bgcolor=#"
        + border_color
        + "> {{{#ffffff "
        + title
        + "}}} ||",
        "||<tablewidth=100%><table bordercolor=#"
        + border_color
        + "><bgcolor=#"
        + border_color
        + "><width=25%> {{{#ffffff 1번 슬롯}}} ||<bgcolor=#"
        + border_color
        + "><width=25%> {{{#ffffff 2번 슬롯}}} ||<bgcolor=#"
        + border_color
        + "><width=25%> {{{#ffffff 3번 슬롯}}} ||<bgcolor=#"
        + border_color
        + "><width=25%> {{{#ffffff 4번 슬롯}}} ||",
    ]
    for r in range(1, max_rows + 1):
        row_cells = []
        for s in (1, 2, 3, 4):
            cells = slot_cells[s]
            if len(cells) >= r:
                row_cells.append(cells[r - 1])
            else:
                row_cells.append("")
        lines.append(f"|| {row_cells[0]} || {row_cells[1]} || {row_cells[2]} || {row_cells[3]} ||")
    return "\n".join(lines)


def build_aa_block(aa_rows, border_color):
    try:
        template = load_text(DEFAULT_AA_TEMPLATE_PATH)
    except Exception:
        return ""
    lines = []
    for row in aa_rows:
        arr = (row.get("arrangement", "") or "").replace("x", "×").replace("X", "×")
        name = row.get("name", "")
        dps = row.get("dps", "")
        rng = row.get("range (km)", "")
        if not any((name, arr, dps, rng)):
            continue
        lines.append(f"|| {name} || {arr} || {dps} || {rng}km ||")

    return render_template(
        template,
        {
            "border_color": border_color,
            "aa_rows": "\n".join(lines),
        },
    )


def parse_bomber_section(raw_text, start_patterns):
    return parse_key_values_between(
        raw_text,
        start_patterns,
        [
            r"^Torpedo Bombers?\b",
            r"^Bomb Airstrike\b",
            r"^BOMB AIRSTRIKE\b",
            r"^Main Artillery\b",
            r"^MAIN BATTERY\b",
            r"^Anti-Aircraft Artillery\b",
            r"^AA ARMAMENT\b",
            r"^WoWsLIconBlack\.pngModules\b",
            r"^Modules\b",
        ],
    )


def parse_torpedo_bomber_section(raw_text):
    return parse_key_values_between(
        raw_text,
        [r"^Torpedo Bombers?\b", r"^TORPEDO BOMBERS?\b", r"^TORPEDO BOMBER\b"],
        [
            r"^Dive Bombers?\b",
            r"^DIVE BOMBERS?\b",
            r"^Skip Bombers?\b",
            r"^SKIP BOMBERS?\b",
            r"^Low Altitude Bombers?\b",
            r"^Bomb Airstrike\b",
            r"^BOMB AIRSTRIKE\b",
            r"^Main Artillery\b",
            r"^MAIN BATTERY\b",
            r"^Anti-Aircraft Artillery\b",
            r"^AA ARMAMENT\b",
            r"^WoWsLIconBlack\.pngModules\b",
            r"^Modules\b",
        ],
    )


def parse_dive_bomber_section(raw_text):
    return parse_key_values_between(
        raw_text,
        [r"^Dive Bombers?\b", r"^DIVE BOMBERS?\b", r"^DIVE BOMBER\b", r"^Skip Bombers?\b", r"^SKIP BOMBERS?\b"],
        [
            r"^Torpedo Bombers?\b",
            r"^TORPEDO BOMBERS?\b",
            r"^Low Altitude Bombers?\b",
            r"^Bomb Airstrike\b",
            r"^BOMB AIRSTRIKE\b",
            r"^Main Artillery\b",
            r"^MAIN BATTERY\b",
            r"^Anti-Aircraft Artillery\b",
            r"^AA ARMAMENT\b",
            r"^WoWsLIconBlack\.pngModules\b",
            r"^Modules\b",
        ],
    )


def parse_skip_bomber_section(raw_text):
    data = parse_key_values_between(
        raw_text,
        [r"^Skip Bombers?\b", r"^SKIP BOMBERS?\b", r"^SKIP BOMBER\b"],
        [
            r"^Dive Bombers?\b",
            r"^DIVE BOMBERS?\b",
            r"^Torpedo Bombers?\b",
            r"^TORPEDO BOMBERS?\b",
            r"^Low Altitude Bombers?\b",
            r"^Bomb Airstrike\b",
            r"^BOMB AIRSTRIKE\b",
            r"^Main Artillery\b",
            r"^MAIN BATTERY\b",
            r"^Anti-Aircraft Artillery\b",
            r"^AA ARMAMENT\b",
            r"^WoWsLIconBlack\.pngModules\b",
            r"^Modules\b",
        ],
    )

    def extract_preferred(label):
        # Prefer tab-separated STOCK/UPGRADED values; fallback to 2+ spaces.
        pat_tab = rf"^\s*{re.escape(label)}\s*\t([^\t\r\n]*)\t([^\t\r\n]*)"
        m = re.search(pat_tab, raw_text or "", re.IGNORECASE | re.MULTILINE)
        if m:
            stock = (m.group(1) or "").strip()
            upgraded = (m.group(2) or "").strip()
            return upgraded if upgraded and upgraded != "-" else stock

        pat_sp = rf"^\s*{re.escape(label)}\s+([^\r\n]*?)\s{{2,}}([^\r\n]*)$"
        m = re.search(pat_sp, raw_text or "", re.IGNORECASE | re.MULTILINE)
        if m:
            stock = (m.group(1) or "").strip()
            upgraded = (m.group(2) or "").strip()
            return upgraded if upgraded and upgraded != "-" else stock
        return ""

    # Ensure all key stats for low-alt/skip bomber are populated by exact labels when present.
    label_to_key = {
        "Plane name": "plane name",
        "Hit points": "hit points",
        "Maximum speed (kt)": "maximum speed (kt)",
        "Attack unit size": "attack unit size",
        "Aircraft per squadron": "aircraft per squadron",
        "Detectability range (km)": "detectability range (km)",
        "Bombs in payload": "bombs in payload",
        "HE Maximum bomb damage": "he maximum bomb damage",
        "HE fire-setting chance (%)": "he fire-setting chance (%)",
        "HE bomb penetration (mm)": "he bomb penetration (mm)",
        "Aircraft maximum flight range (km)": "aircraft maximum flight range (km)",
        "Aircraft restoration time (sec)": "aircraft restoration time (sec)",
        "Aircraft on deck": "aircraft on deck",
        "Aircraft per restoration": "aircraft per restoration",
        "Bomb skip count": "bomb skip count",
    }

    for label, key in label_to_key.items():
        v = extract_preferred(label)
        if v:
            data[key] = v
    return data


def build_torpedo_bomber_block(b, border_color):
    try:
        template = load_text(DEFAULT_TORPEDO_BOMBER_TEMPLATE_PATH)
    except Exception:
        return ""
    return render_template(
        template,
        {
            "border_color": border_color,
            "name": pick_first(b, ["plane name", "name"]),
            "hp": fmt_num_with_comma(pick_first(b, ["hit points", "hitpoint", "hp"])),
            "speed": pick_first(b, ["maximum speed (kt)", "maximum speed"]),
            "detect_km": pick_first(b, ["detectability range (km)", "detectability by air (km)", "detectability (km)"]),
            "flight_km": pick_first(b, ["aircraft maximum flight range (km)", "maximum flight range (km)", "flight range (km)", "range (km)"]),
            "attack_size": pick_first(b, ["attack unit size", "attack squadron size"]),
            "per_squadron": pick_first(b, ["aircraft per squadron"]),
            "reserve": pick_first(b, ["aircraft on deck", "maximum reserve", "maximum reserves", "maximum hangar"]),
            "restoration_sec": pick_first(b, ["aircraft restoration time (sec)", "restoration time (sec)", "servicing time (sec)"]),
            "restoration_count": pick_first(b, ["aircraft per restoration", "aircraft per service", "restoration count"], "1"),
            "torp_damage": fmt_num_with_comma(pick_first(b, ["maximum torpedo damage", "torpedo maximum damage"])),
            "torp_range_km": pick_first(b, ["torpedo range (km)", "range (km)"]),
            "torp_speed": pick_first(b, ["torpedo speed (kt)", "speed (kt)", "torpedo speed"]),
            "payload": pick_first(b, ["torpedoes in payload", "payload"]),
        },
    )


def build_dive_bomber_block(b, border_color, bomb_type="고폭탄"):
    try:
        template = load_text(DEFAULT_DIVE_SKIP_BOMBER_TEMPLATE_PATH)
    except Exception:
        return ""
    use_ap = bomb_type == "철갑탄"
    bomb_damage = fmt_num_with_comma(
        pick_first(
            b,
            ["ap maximum bomb damage", "maximum bomb damage"] if use_ap else ["he maximum bomb damage", "maximum bomb damage", "ap maximum bomb damage"],
        )
    )
    fire = "x" if use_ap else pick_first(b, ["he fire-setting chance (%)", "fire-setting chances (%)", "fire chance (%)"])
    bomb_pen = "x" if use_ap else pick_first(b, ["he bomb penetration (mm)", "armor piercing (mm)", "bomb penetration (mm)", "penetration (mm)"])
    return render_template(
        template,
        {
            "border_color": border_color,
            "name": pick_first(b, ["plane name", "name"]),
            "hp": fmt_num_with_comma(pick_first(b, ["hit points", "hitpoint", "hp"])),
            "speed": pick_first(b, ["maximum speed (kt)", "maximum speed"]),
            "detect_km": pick_first(b, ["detectability range (km)", "detectability by air (km)", "detectability (km)"]),
            "flight_km": pick_first(b, ["aircraft maximum flight range (km)", "maximum flight range (km)", "flight range (km)", "range (km)"]),
            "attack_size": pick_first(b, ["attack unit size", "attack squadron size"]),
            "per_squadron": pick_first(b, ["aircraft per squadron"]),
            "reserve": pick_first(b, ["aircraft on deck", "maximum reserve", "maximum reserves", "maximum hangar"]),
            "restoration_sec": pick_first(b, ["aircraft restoration time (sec)", "restoration time (sec)", "servicing time (sec)"]),
            "restoration_count": pick_first(b, ["aircraft per restoration", "aircraft per service", "restoration count"], "1"),
            "bomb_type": bomb_type,
            "payload": pick_first(b, ["bombs in payload", "payload"]),
            "bomb_damage": bomb_damage,
            "bomb_pen_cell": fmt_unit_or_x(bomb_pen, "mm"),
            "fire_chance_cell": fmt_unit_or_x(fire, "%"),
        },
    )


def build_carpet_bomber_block(b, border_color, bomb_type="고폭탄", bombing_mode="융단"):
    try:
        template = load_text(DEFAULT_CARPET_BOMBER_TEMPLATE_PATH)
    except Exception:
        return ""

    name = pick_first(b, ["plane name", "name"])
    hp = fmt_num_with_comma(pick_first(b, ["hit points", "hitpoint", "hp"]))
    speed = pick_first(b, ["maximum speed (kt)", "maximum speed"])
    detect = pick_first(b, ["detectability range (km)", "detectability by air (km)", "detectability (km)"])
    flight = pick_first(
        b,
        [
            "aircraft maximum flight range (km)",
            "maximum flight range (km)",
            "flight range (km)",
            "maximum attack range (km)",
            "range (km)",
        ],
    )
    atk_size = pick_first(b, ["attack unit size", "attack squadron size"])
    per_sq = pick_first(b, ["aircraft per squadron"])
    reserve = pick_first(
        b,
        [
            "aircraft on deck",
            "maximum reserve",
            "maximum reserves",
            "maximum hangar",
            "maximum aircraft in hangar",
        ],
    )
    rest = pick_first(b, ["aircraft restoration time (sec)", "restoration time (sec)", "servicing time (sec)"])
    restoration_count = pick_first(b, ["aircraft per restoration", "aircraft per service", "restoration count"], "1")
    payload_total = pick_first(b, ["bombs in payload", "payload", "bomb payload"])
    use_ap = bomb_type == "철갑탄"
    bomb_dmg = fmt_num_with_comma(
        pick_first(
            b,
            ["ap maximum bomb damage", "maximum bomb damage"] if use_ap else ["he maximum bomb damage", "maximum bomb damage", "bomb maximum damage", "ap maximum bomb damage"],
        )
    )
    bomb_pen = "x" if use_ap else pick_first(
        b,
        [
            "he bomb penetration (mm)",
            "armor piercing (mm)",
            "bomb penetration (mm)",
            "penetration (mm)",
        ],
    )
    fire = "x" if use_ap else pick_first(b, ["he fire-setting chance (%)", "fire-setting chances (%)", "fire chance (%)"])

    return render_template(
        template,
        {
            "border_color": border_color,
            "name": name,
            "hp": hp,
            "speed": speed,
            "detect_km": detect,
            "flight_km": flight,
            "attack_size": atk_size,
            "per_squadron": per_sq,
            "reserve": reserve,
            "restoration_sec": rest,
            "restoration_count": restoration_count,
            "bombing_mode": bombing_mode,
            "bomb_type": bomb_type,
            "payload": payload_total,
            "bomb_damage": bomb_dmg,
            "bomb_pen_cell": fmt_unit_or_x(bomb_pen, "mm"),
            "fire_chance_cell": fmt_unit_or_x(fire, "%"),
        },
    )


def build_low_alt_bomber_block(b, border_color, bomb_type="고폭탄"):
    try:
        template = load_text(DEFAULT_LOW_ALT_BOMBER_TEMPLATE_PATH)
    except Exception:
        return ""
    rebound_count = pick_first(b, ["bomb skip count", "skip count", "rebound count"])
    fuze_rebound_count = pick_first(b, ["fuse skip count", "fuze rebound count", "fuse rebound count"])
    use_ap = bomb_type == "철갑탄"
    return render_template(
        template,
        {
            "border_color": border_color,
            "name": pick_first(b, ["plane name", "name"]),
            "hp": fmt_num_with_comma(pick_first(b, ["hit points", "hitpoint", "hp"])),
            "speed": pick_first(b, ["maximum speed (kt)", "maximum speed"]),
            "detect_km": pick_first(b, ["detectability range (km)", "detectability by air (km)", "detectability (km)"]),
            "flight_km": pick_first(b, ["aircraft maximum flight range (km)", "maximum flight range (km)", "flight range (km)", "range (km)"]),
            "attack_size": pick_first(b, ["attack unit size", "attack squadron size"]),
            "per_squadron": pick_first(b, ["aircraft per squadron"]),
            "reserve": pick_first(b, ["aircraft on deck", "maximum reserve", "maximum reserves", "maximum hangar"]),
            "restoration_sec": pick_first(b, ["aircraft restoration time (sec)", "restoration time (sec)", "servicing time (sec)"]),
            "restoration_count": pick_first(b, ["aircraft per restoration", "aircraft per service", "restoration count"], "1"),
            "bomb_type": bomb_type,
            "payload": pick_first(b, ["bombs in payload", "payload"]),
            "bomb_damage": fmt_num_with_comma(pick_first(b, ["he maximum bomb damage", "maximum bomb damage", "bomb maximum damage", "ap maximum bomb damage"])),
            "bomb_pen_cell": fmt_unit_or_x(
                "x" if use_ap else pick_first(b, ["he bomb penetration (mm)", "armor piercing (mm)", "bomb penetration (mm)", "penetration (mm)"]),
                "mm",
            ),
            "fire_chance_cell": fmt_unit_or_x(
                "x" if use_ap else pick_first(b, ["he fire-setting chance (%)", "fire-setting chances (%)", "fire chance (%)"]),
                "%",
            ),
            "rebound_count": rebound_count,
            "fuze_rebound_count": fuze_rebound_count,
        },
    )


def _aircraft_content_table(block, border_color):
    lines = (block or "").strip().splitlines()
    if not lines:
        return ""
    if re.search(r"\{\{\{#FFFFFF\s+(?:뇌격기|.*폭격기)\}\}\}", lines[0]):
        lines = lines[1:]
    if lines and lines[0].startswith("||") and "<tablewidth=" not in lines[0]:
        lines[0] = f"||<tablewidth=100%><table bordercolor=#{border_color}>" + lines[0][2:]
    return "\n".join(lines)


def build_aircraft_tabs_block(aircraft_entries, border_color, ship_name_en=""):
    entries = []
    used_roles = set()
    for index, entry in enumerate(aircraft_entries or [], start=1):
        if not isinstance(entry, (tuple, list)) or len(entry) != 3:
            continue
        role_raw, label, raw_block = entry
        content = _aircraft_content_table(raw_block, border_color)
        if not content:
            continue
        role_base = re.sub(r"[^A-Za-z0-9]+", "", role_raw or "") or f"Type{index}"
        role = role_base
        suffix = 2
        while role in used_roles:
            role = f"{role_base}{suffix}"
            suffix += 1
        used_roles.add(role)
        entries.append((role, str(label or role), raw_block, content))

    if not entries:
        return ""
    if len(entries) == 1:
        return entries[0][2]

    class_ship_name = re.sub(r"[^A-Za-z0-9]+", "", ship_name_en or "") or "Ship"
    class_prefix = f"air{class_ship_name}"
    button_palette = get_nation_button_palette(border_color)
    tab_width = f"{100 / len(entries):.6f}".rstrip("0").rstrip(".")

    button_blocks = []
    content_blocks = []
    for index, (role, label, _raw_block, content) in enumerate(entries):
        selected_class = f" {class_prefix}BtnSelected" if index == 0 else ""
        hidden_class = f" {class_prefix}Hide" if index > 0 else ""
        onclick = (
            f"remove-class,{class_prefix}Btn,{class_prefix}BtnSelected;"
            f"add-class,{class_prefix}Btn{role},{class_prefix}BtnSelected;"
            f"add-class,{class_prefix}Content,{class_prefix}Hide;"
            f"remove-class,{class_prefix}{role},{class_prefix}Hide"
        )
        button_blocks.append(
            "{{{#!wiki class=\"__BUTTON_CLASSES__\" onclick=\"__ONCLICK__\"\n"
            "{{{#!wiki style=\"margin: auto;\"\n"
            "__LABEL__}}}}}}"
            .replace("__BUTTON_CLASSES__", f"{class_prefix}Btn {class_prefix}Btn{role}{selected_class}")
            .replace("__ONCLICK__", onclick)
            .replace("__LABEL__", label)
        )
        content_blocks.append(
            "{{{#!wiki class=\"__CONTENT_CLASSES__\"\n__CONTENT__\n}}}"
            .replace("__CONTENT_CLASSES__", f"{class_prefix}Content {class_prefix}{role}{hidden_class}")
            .replace("__CONTENT__", content)
        )

    block = (
        "{{{#!style\n"
        ".__CLASS__Title {margin: 0 0 -10px;}\n"
        ".__CLASS__BtnWrap {background-color: #__WRAP_COLOR__; display: flex; flex-wrap: nowrap; width: 100%; margin: 0 0 -10px; justify-content: start; border-radius: 0; box-sizing: border-box;}\n"
        ".__CLASS__Btn {display: flex; flex: 1 1 __TAB_WIDTH__%; width: __TAB_WIDTH__%; color: #fff; border-bottom: 6px solid transparent; text-align: center; padding: 4px 8px; border-radius: 0; box-sizing: border-box; cursor: pointer; text-shadow: 0 0 2px #000;}\n"
        ".__CLASS__BtnSelected {background-color: #__SELECTED_COLOR__; border-bottom-color: #__ACCENT_COLOR__; color: #__SELECTED_TEXT_COLOR__; font-weight: bold; text-shadow: __SELECTED_TEXT_SHADOW__;}\n"
        ".__CLASS__Hide {display: none;}\n"
        "}}}\n"
        "{{{#!wiki class=\"__CLASS__Title\"\n"
        "||<tablewidth=100%><table bordercolor=#__BC__><#__BC__> {{{#FFFFFF 함재기}}} ||\n"
        "}}}{{{#!wiki class=\"__CLASS__BtnWrap\"\n"
        "__BUTTONS__}}}__CONTENTS__"
    )
    replacements = {
        "__CLASS__": class_prefix,
        "__WRAP_COLOR__": button_palette["wrap"],
        "__SELECTED_COLOR__": button_palette["selected"],
        "__ACCENT_COLOR__": button_palette["accent"],
        "__SELECTED_TEXT_COLOR__": button_palette["text"],
        "__SELECTED_TEXT_SHADOW__": button_palette["shadow"],
        "__BC__": border_color,
        "__TAB_WIDTH__": tab_width,
        "__BUTTONS__": "".join(button_blocks),
        "__CONTENTS__": "".join(content_blocks),
    }
    for key, value in replacements.items():
        block = block.replace(key, value)
    return block


def build_aircraft_switch_block(torpedo_block, bomber_block, border_color, ship_name_en=""):
    return build_aircraft_tabs_block(
        [("Torpedo", "뇌격기", torpedo_block), ("Bomber", "폭격기", bomber_block)],
        border_color,
        ship_name_en=ship_name_en,
    )


def pick_first(row, keys, default=""):
    for k in keys:
        v = row.get(k, "")
        if v:
            return v
    return default


def parse_armament_sections(raw_text, section_header_regex):
    text = raw_text or ""
    lines = text.splitlines()
    rows = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.search(section_header_regex, line, re.IGNORECASE):
            row = {}
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if re.search(section_header_regex, s, re.IGNORECASE):
                    break
                if re.search(r"^(WoWsLIconBlack\.pngModules|Modules|Consumables|Survivability|Maneuverability|Concealment|Bomb Airstrike|Main Artillery|Anti-Aircraft Artillery)\b", s, re.IGNORECASE):
                    break
                s2 = re.sub(r"^[^\w]+", "", s).strip()
                parts = [p.strip() for p in re.split(r"\t+", s2) if p.strip()]
                if len(parts) < 2:
                    parts = [p.strip() for p in re.split(r"\s{2,}", s2) if p.strip()]
                if len(parts) >= 2:
                    key = parts[0].lower()
                    val = parts[1]
                    row[key] = val
                j += 1
            rows.append(row)
            i = j
            continue
        i += 1
    return rows


def parse_secondary_armaments(raw_text):
    rows = parse_armament_sections(
        raw_text,
        r"^SECONDARY(\s+BATTERY|\s+ARMAMENT|\s+ARTILLERY)?\s+\d+",
    )
    if rows:
        return rows

    # Fallback: single secondary section without numbered armament blocks.
    single = parse_key_values_between(
        raw_text,
        [r"^Secondary Artillery\b", r"^SECONDARY ARTILLERY\b", r"^Secondary\b", r"^SECONDARY\b"],
        [
            r"^Torpedoes?\b",
            r"^TORPEDOES?\b",
            r"^Bomb Airstrike\b",
            r"^BOMB AIRSTRIKE\b",
            r"^Main Artillery\b",
            r"^MAIN BATTERY\b",
            r"^Anti-Aircraft Artillery\b",
            r"^AA ARMAMENT\b",
            r"^WoWsLIconBlack\.pngModules\b",
            r"^Modules\b",
        ],
    )
    if single and any(single.get(k) for k in ("name", "secondary battery name", "arrangement", "secondary battery arrangement")):
        return [single]
    return []


def parse_torpedo_armaments(raw_text):
    # Ship module table format, for example:
    # Legends_Torpedo.png  Launcher Arrangement  Reload Time (s) ...
    # 610mm quintuple      3x5                  131s            ...
    # 610mm quintuple      3x5                  153s            ...
    lines = (raw_text or "").splitlines()
    for i, raw_line in enumerate(lines):
        if not re.search(r"(?:^|\t)Legends_Torpedo\.png(?:\t|$)", raw_line, re.IGNORECASE):
            continue

        module_rows = []
        for data_line in lines[i + 1:]:
            stripped = data_line.strip()
            if not stripped:
                continue
            if re.search(r"(?:^|\t)Legends_[^\t]*\.png(?:\t|$)", data_line, re.IGNORECASE):
                break

            parts = [part.strip() for part in data_line.split("\t")]
            if len(parts) < 8:
                continue
            if normalize_token(parts[0]) in ("stock", "upgraded"):
                continue

            module_rows.append(
                {
                    "name": parts[0],
                    "arrangement": parts[1],
                    "reload time (sec)": re.sub(r"\s*s$", "", parts[2], flags=re.IGNORECASE),
                    "180° turn time (sec)": re.sub(r"\s*s$", "", parts[3], flags=re.IGNORECASE),
                    "maximum damage": parts[4],
                    "range (km)": re.sub(r"\s*km$", "", parts[5], flags=re.IGNORECASE),
                    "speed (kt)": re.sub(r"\s*(?:kn|kt|knots)$", "", parts[6], flags=re.IGNORECASE),
                    "detectability by sea (km)": re.sub(r"\s*km$", "", parts[7], flags=re.IGNORECASE),
                }
            )
        if module_rows:
            return module_rows

    rows = parse_armament_sections(raw_text, r"^(TORPEDO|TORPEDOES|TORPEDO TUBES?)\s+\d+")
    if rows:
        return rows

    # Fallback: single torpedo section without numbered armament blocks.
    single = parse_key_values_between(
        raw_text,
        [r"^TORPEDOES\b", r"^TORPEDO\b", r"^Torpedoes\b", r"^Torpedo\b"],
        [
            r"^Bomb Airstrike\b",
            r"^BOMB AIRSTRIKE\b",
            r"^Main Artillery\b",
            r"^MAIN BATTERY\b",
            r"^Secondary Artillery\b",
            r"^SECONDARY ARTILLERY\b",
            r"^Anti-Aircraft Artillery\b",
            r"^AA ARMAMENT\b",
            r"^WoWsLIconBlack\.pngModules\b",
            r"^Modules\b",
        ],
    )
    if single and any(single.get(k) for k in ("name", "arrangement", "range (km)", "speed (kt)")):
        return [single]
    return []


def build_secondary_block(sec_rows, border_color, ship_name_en=""):
    try:
        template = load_text(DEFAULT_SECONDARY_BATTERY_TEMPLATE_PATH)
    except Exception:
        return ""

    def map_row(r):
        name = pick_first(r, ["name", "secondary battery name", "secondary armament name"])
        arr = pick_first(r, ["arrangement", "mounting", "secondary battery arrangement"]).replace("x", "×").replace("X", "×")
        reload_s = pick_first(r, ["reload time (sec)", "reload time", "reload"])
        range_km = pick_first(r, ["range (km)", "firing range (km)"])
        sap_dmg_raw = pick_first(r, ["sap maximum damage"])
        sap_pen_raw = pick_first(r, ["sap penetration (mm)", "sap penetration"])
        if sap_dmg_raw or sap_pen_raw:
            shell_type = "반철갑탄"
            dmg = fmt_num_with_comma(sap_dmg_raw or pick_first(r, ["maximum damage", "damage"]))
            fire = "x"
            pen = (sap_pen_raw or "").strip()
        else:
            shell_type = "고폭탄"
            dmg = fmt_num_with_comma(pick_first(r, ["he maximum damage", "maximum damage", "damage"]))
            he_fire = pick_first(r, ["he fire chance (%)", "fire chance (%)", "fire chance"])
            fire = (he_fire + "%") if he_fire else "x"
            pen = pick_first(r, ["he penetration (mm)", "penetration (mm)", "penetration"])
        pen_cell = (pen + "mm") if pen else "x"
        return {
            "name": name,
            "arrangement": arr,
            "reload_s": reload_s,
            "range_km": range_km,
            "shell_type": shell_type,
            "dmg": dmg,
            "fire": fire,
            "pen": pen_cell,
        }

    mapped_rows = [map_row(r) for r in sec_rows if isinstance(r, dict)]
    mapped_rows = [r for r in mapped_rows if any((r["name"], r["arrangement"], r["reload_s"], r["range_km"], r["dmg"], r["pen"]))]

    # Each armament row is a separate selectable secondary-battery type.
    merged = [dict(r) for r in mapped_rows]

    if not merged:
        return ""

    def render_secondary_row(r):
        return render_template(
            template,
            {
            "border_color": border_color,
            "secondary1_name": r["name"],
            "secondary1_arrangement": r["arrangement"],
            "secondary1_reload_sec": r["reload_s"],
            "secondary1_range_km": r["range_km"],
            "secondary1_shell_type": r["shell_type"],
            "secondary1_damage": r["dmg"],
            "secondary1_fire": r["fire"],
            "secondary1_pen": r["pen"],
            "secondary2_block": "",
            },
        )

    rendered_rows = [render_secondary_row(r) for r in merged]
    if len(rendered_rows) == 1:
        return rendered_rows[0]

    class_ship_name = re.sub(r"[^A-Za-z0-9]+", "", ship_name_en or "") or "Ship"
    class_prefix = f"secondary{class_ship_name}"
    button_palette = get_nation_button_palette(border_color)
    tab_width = f"{100 / len(rendered_rows):.6f}".rstrip("0").rstrip(".")
    base_tab_labels = []
    for index, r in enumerate(merged, start=1):
        caliber_match = re.search(r"\d+(?:\.\d+)?\s*mm", r["name"] or "", re.IGNORECASE)
        if caliber_match:
            label = re.sub(r"\s+", "", caliber_match.group(0)).lower()
        else:
            label = (r["name"] or "").replace(" [br] ", " / ").strip() or f"부함포 {index}"
        base_tab_labels.append(label)

    label_counts = {label: base_tab_labels.count(label) for label in set(base_tab_labels)}
    label_seen = {}
    tab_labels = []
    for label in base_tab_labels:
        if label_counts[label] > 1:
            occurrence = label_seen.get(label, 0)
            label_seen[label] = occurrence + 1
            suffix = occurrence + 1
            label = f"{label}^^{{{{{{-1 {suffix}}}}}}}^^"
        tab_labels.append(label)

    button_blocks = []
    content_blocks = []
    for index, (r, raw_block, label) in enumerate(zip(merged, rendered_rows, tab_labels), start=1):
        role = f"Type{index}"
        selected_class = f" {class_prefix}BtnSelected" if index == 1 else ""
        hidden_class = f" {class_prefix}Hide" if index > 1 else ""
        onclick = (
            f"remove-class,{class_prefix}Btn,{class_prefix}BtnSelected;"
            f"add-class,{class_prefix}Btn{role},{class_prefix}BtnSelected;"
            f"add-class,{class_prefix}Content,{class_prefix}Hide;"
            f"remove-class,{class_prefix}{role},{class_prefix}Hide"
        )
        button_blocks.append(
            "{{{#!wiki class=\"__BUTTON_CLASSES__\" onclick=\"__ONCLICK__\"\n"
            "{{{#!wiki style=\"margin: auto;\"\n"
            "__LABEL__}}}}}}"
            .replace("__BUTTON_CLASSES__", f"{class_prefix}Btn {class_prefix}Btn{role}{selected_class}")
            .replace("__ONCLICK__", onclick)
            .replace("__LABEL__", label)
        )

        lines = raw_block.strip().splitlines()
        if lines and "{{{#FFFFFF 부함포}}}" in lines[0]:
            lines = lines[1:]
        if lines and lines[0].startswith("||") and "<tablewidth=" not in lines[0]:
            lines[0] = f"||<tablewidth=100%><table bordercolor=#{border_color}>" + lines[0][2:]
        content = "\n".join(lines)
        content_blocks.append(
            "{{{#!wiki class=\"__CONTENT_CLASSES__\"\n__CONTENT__\n}}}"
            .replace("__CONTENT_CLASSES__", f"{class_prefix}Content {class_prefix}{role}{hidden_class}")
            .replace("__CONTENT__", content)
        )

    block = (
        "{{{#!style\n"
        ".__CLASS__Title {margin: 0 0 -10px;}\n"
        ".__CLASS__BtnWrap {background-color: #__WRAP_COLOR__; display: flex; flex-wrap: nowrap; width: 100%; margin: 0 0 -10px; justify-content: start; border-radius: 0; box-sizing: border-box;}\n"
        ".__CLASS__Btn {display: flex; flex: 1 1 __TAB_WIDTH__%; width: __TAB_WIDTH__%; color: #fff; border-bottom: 6px solid transparent; text-align: center; padding: 4px 8px; border-radius: 0; box-sizing: border-box; cursor: pointer; text-shadow: 0 0 2px #000;}\n"
        ".__CLASS__BtnSelected {background-color: #__SELECTED_COLOR__; border-bottom-color: #__ACCENT_COLOR__; color: #__SELECTED_TEXT_COLOR__; font-weight: bold; text-shadow: __SELECTED_TEXT_SHADOW__;}\n"
        ".__CLASS__Hide {display: none;}\n"
        "}}}\n"
        "{{{#!wiki class=\"__CLASS__Title\"\n"
        "||<tablewidth=100%><table bordercolor=#__BC__><#__BC__> {{{#FFFFFF 부함포}}} ||\n"
        "}}}{{{#!wiki class=\"__CLASS__BtnWrap\"\n"
        "__BUTTONS__}}}__CONTENTS__"
    )
    replacements = {
        "__CLASS__": class_prefix,
        "__WRAP_COLOR__": button_palette["wrap"],
        "__SELECTED_COLOR__": button_palette["selected"],
        "__ACCENT_COLOR__": button_palette["accent"],
        "__SELECTED_TEXT_COLOR__": button_palette["text"],
        "__SELECTED_TEXT_SHADOW__": button_palette["shadow"],
        "__BC__": border_color,
        "__TAB_WIDTH__": tab_width,
        "__BUTTONS__": "".join(button_blocks),
        "__CONTENTS__": "".join(content_blocks),
    }
    for key, value in replacements.items():
        block = block.replace(key, value)
    return block


def build_torpedo_block(torp_rows, border_color, is_deep_water=False, ship_name_en=""):
    try:
        template = load_text(DEFAULT_TORPEDO_TEMPLATE_PATH)
    except Exception:
        return ""

    r1 = torp_rows[0] if len(torp_rows) >= 1 else {}
    r2 = torp_rows[1] if len(torp_rows) >= 2 else {}

    def map_row(r):
        name_raw = pick_first(r, ["name", "torpedo name", "torpedo tubes name"])
        arr_raw = pick_first(r, ["arrangement", "mounting", "torpedo arrangement"])
        name_parts = [p.strip() for p in name_raw.split(",") if p.strip()]
        arr_parts = [p.strip() for p in arr_raw.split(",") if p.strip()]
        name = " [br] ".join(name_parts) if name_parts else name_raw
        arr = " [br] ".join([a.replace("x", "×").replace("X", "×") for a in arr_parts]) if arr_parts else arr_raw.replace("x", "×").replace("X", "×")
        reload_s = pick_first(r, ["reload time (sec)", "reload time", "reload"])
        turn_s = pick_first(r, ["180° turn time (sec)", "180? turn time (sec)", "180 turn time (sec)"], "7.2")
        dmg = fmt_num_with_comma(pick_first(r, ["torpedo maximum damage", "maximum simulated damage", "maximum damage", "damage"]))
        detect = pick_first(r, ["detectability by sea (km)", "detectability range (km)", "torpedo detectability range (km)", "detectability (km)"])
        range_km = pick_first(r, ["range (km)", "torpedo range (km)"])
        speed = pick_first(r, ["speed (kt)", "speed (knots)", "speed"])
        return {
            "name": name,
            "arrangement": arr,
            "reload_s": reload_s,
            "turn_s": turn_s,
            "dmg": dmg,
            "detect": detect,
            "range_km": range_km,
            "speed": speed,
        }

    a = map_row(r1)
    b = map_row(r2)

    has_second_torpedo = bool(b["name"] or b["arrangement"] or b["reload_s"] or b["range_km"])
    if has_second_torpedo:
        class_ship_name = re.sub(r"[^A-Za-z0-9]+", "", ship_name_en or "") or "Ship"
        class_prefix = f"torp{class_ship_name}"
        button_palette = get_nation_button_palette(border_color)
        torpedo_title = "심해 어뢰" if is_deep_water else "어뢰"
        block = (
            "{{{#!style\n"
            ".__CLASS__BtnWrap {background-color: #__WRAP_COLOR__; display: flex; flex-wrap: nowrap; width: 320px; width: min(100%, calc(460px - 10vw)); min-width: 280px; max-width: 100%; margin: 0 0 -10px; justify-content: start; border-radius: 6px 6px 0 0; box-sizing: border-box;}\n"
            ".__CLASS__Btn {display: flex; flex: 1 1 50%; width: 50%; color: #fff; border-bottom: 6px solid transparent; text-align: center; padding: 4px 8px; border-radius: 0; box-sizing: border-box; cursor: pointer;}\n"
            ".__CLASS__BtnStock {border-radius: 6px 0 0 0;}\n"
            ".__CLASS__BtnUpgrade {border-radius: 0 6px 0 0;}\n"
            ".__CLASS__BtnSelected {background-color: #__SELECTED_COLOR__; border-bottom: 6px solid #__ACCENT_COLOR__; color: #__SELECTED_TEXT_COLOR__; font-weight: bold; text-shadow: __SELECTED_TEXT_SHADOW__;}\n"
            ".__CLASS__Hide {display: none;}\n"
            "}}}\n"
            "{{{#!wiki class=\"__CLASS__BtnWrap\"\n"
            "{{{#!wiki class=\"__CLASS__Btn __CLASS__BtnStock __CLASS__BtnSelected\" onclick=\"remove-class,__CLASS__Btn,__CLASS__BtnSelected;add-class,__CLASS__BtnStock,__CLASS__BtnSelected;add-class,__CLASS__Content,__CLASS__Hide;remove-class,__CLASS__Stock,__CLASS__Hide\"\n"
            "{{{#!wiki style=\"margin: auto;\"\n"
            "해제}}}}}}{{{#!wiki class=\"__CLASS__Btn __CLASS__BtnUpgrade\" onclick=\"remove-class,__CLASS__Btn,__CLASS__BtnSelected;add-class,__CLASS__BtnUpgrade,__CLASS__BtnSelected;add-class,__CLASS__Content,__CLASS__Hide;remove-class,__CLASS__Upgrade,__CLASS__Hide\"\n"
            "{{{#!wiki style=\"margin: auto;\"\n"
            "설치}}}}}}}}}{{{#!wiki class=\"__CLASS__Content __CLASS__Stock\"\n"
            "||<tablewidth=100%><table bordercolor=#__BC__><#__BC__><-4> {{{#FFFFFF __TITLE__}}} ||\n"
            "||<#__BC__><width=10%> {{{#FFFFFF 명칭}}} ||<width=90%><-3> __NAME1__ ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 어뢰 발사관}}} ||<#__BC__><width=30%> {{{#FFFFFF 탑재 수}}} ||<#__BC__><width=30%> {{{#FFFFFF 장전 시간}}} ||<#__BC__><width=30%> {{{#FFFFFF 180도 회전 시간}}} ||\n"
            "|| __ARR1__ || __RELOAD1__초 || __TURN1__초 ||\n"
            "||<-3> {{{#!wiki style=\"margin: -16px -11px;\"\n"
            "||<#__BC__><tablewidth=100%><width=25%> {{{#FFFFFF 어뢰 최대 공격력}}} ||<#__BC__><width=25%> {{{#FFFFFF 어뢰 대함 피탐지}}} ||<#__BC__><width=25%> {{{#FFFFFF 사거리}}} ||<#__BC__><width=25%> {{{#FFFFFF 속력}}} ||\n"
            "|| __DMG1__ || __DETECT1__km || __RANGE1__km || __SPEED1__knots ||}}} ||\n"
            "}}}{{{#!wiki class=\"__CLASS__Content __CLASS__Upgrade __CLASS__Hide\"\n"
            "||<tablewidth=100%><table bordercolor=#__BC__><#__BC__><-4> {{{#FFFFFF __TITLE__}}} ||\n"
            "||<#__BC__><width=10%> {{{#FFFFFF 명칭}}} ||<width=90%><-3> __NAME2__ ||\n"
            "||<#__BC__><width=10%><|3> {{{#FFFFFF 어뢰 발사관}}} ||<#__BC__><width=30%> {{{#FFFFFF 탑재 수}}} ||<#__BC__><width=30%> {{{#FFFFFF 장전 시간}}} ||<#__BC__><width=30%> {{{#FFFFFF 180도 회전 시간}}} ||\n"
            "|| __ARR2__ || __RELOAD2__초 || __TURN2__초 ||\n"
            "||<-3> {{{#!wiki style=\"margin: -16px -11px;\"\n"
            "||<#__BC__><tablewidth=100%><width=25%> {{{#FFFFFF 어뢰 최대 공격력}}} ||<#__BC__><width=25%> {{{#FFFFFF 어뢰 대함 피탐지}}} ||<#__BC__><width=25%> {{{#FFFFFF 사거리}}} ||<#__BC__><width=25%> {{{#FFFFFF 속력}}} ||\n"
            "|| __DMG2__ || __DETECT2__km || __RANGE2__km || __SPEED2__knots ||}}} ||\n"
            "}}}"
        )
        replacements = {
            "__CLASS__": class_prefix,
            "__WRAP_COLOR__": button_palette["wrap"],
            "__SELECTED_COLOR__": button_palette["selected"],
            "__ACCENT_COLOR__": button_palette["accent"],
            "__SELECTED_TEXT_COLOR__": button_palette["text"],
            "__SELECTED_TEXT_SHADOW__": button_palette["shadow"],
            "__BC__": border_color,
            "__TITLE__": torpedo_title,
            "__NAME1__": a["name"],
            "__ARR1__": a["arrangement"],
            "__RELOAD1__": a["reload_s"],
            "__TURN1__": a["turn_s"],
            "__DMG1__": a["dmg"],
            "__DETECT1__": a["detect"],
            "__RANGE1__": a["range_km"],
            "__SPEED1__": a["speed"],
            "__NAME2__": b["name"],
            "__ARR2__": b["arrangement"],
            "__RELOAD2__": b["reload_s"],
            "__TURN2__": b["turn_s"],
            "__DMG2__": b["dmg"],
            "__DETECT2__": b["detect"],
            "__RANGE2__": b["range_km"],
            "__SPEED2__": b["speed"],
        }
        for key, value in replacements.items():
            block = block.replace(key, value)
        return block

    torpedo2_block = ""
    if b["name"] or b["arrangement"] or b["reload_s"] or b["range_km"]:
        torpedo2_block = (
            "||<#__BC__><width=25%> {{{#FFFFFF 명칭}}} ||<#__BC__><width=25%> {{{#FFFFFF 탑재 수}}} ||<#__BC__><width=25%> {{{#FFFFFF 장전 시간}}} ||<#__BC__><width=25%> {{{#FFFFFF 180도 회전 시간}}} ||\n"
            "||<|2> __NAME__ || __ARR__ || __RELOAD__초 || __TURN__초 ||\n"
            "||<-3> {{{#!wiki style=\"margin: -16px -11px;\"\n"
            "||<#__BC__><tablewidth=100%><width=25%> {{{#FFFFFF 어뢰 최대 공격력}}} ||<#__BC__><width=25%> {{{#FFFFFF 어뢰 대함 피탐지}}} ||<#__BC__><width=25%> {{{#FFFFFF 사거리}}} ||<#__BC__><width=25%> {{{#FFFFFF 속력}}} ||\n"
            "|| __DMG__ || __DETECT__km || __RANGE__km || __SPEED__knots ||}}} ||"
        )
        torpedo2_block = (
            torpedo2_block
            .replace("__BC__", border_color)
            .replace("__NAME__", b["name"])
            .replace("__ARR__", b["arrangement"])
            .replace("__RELOAD__", b["reload_s"])
            .replace("__TURN__", b["turn_s"])
            .replace("__DMG__", b["dmg"])
            .replace("__DETECT__", b["detect"])
            .replace("__RANGE__", b["range_km"])
            .replace("__SPEED__", b["speed"])
        )

    out = render_template(
        template,
        {
            "border_color": border_color,
            "torpedo_title": "심해 어뢰" if is_deep_water else "어뢰",
            "torpedo1_name": a["name"],
            "torpedo1_arrangement": a["arrangement"],
            "torpedo1_reload_sec": a["reload_s"],
            "torpedo1_turn_sec": a["turn_s"],
            "torpedo1_damage": a["dmg"],
            "torpedo1_detect_km": a["detect"],
            "torpedo1_range_km": a["range_km"],
            "torpedo1_speed_knots": a["speed"],
            "torpedo2_block": torpedo2_block,
        },
    )
    return out


def build_incendiary_torpedo_block(torp_rows, border_color):
    try:
        template = load_text(DEFAULT_INCENDIARY_TORPEDO_TEMPLATE_PATH)
    except Exception:
        return ""
    r = torp_rows[0] if torp_rows else {}
    name = pick_first(r, ["name", "torpedo name", "torpedo tubes name"], "소이 가속 어뢰")
    arrangement = pick_first(r, ["arrangement", "mounting", "torpedo arrangement"], "×")
    arrangement = arrangement.replace("x", "×").replace("X", "×")
    reload_s = pick_first(r, ["reload time (sec)", "reload time", "reload"])
    turn_s = pick_first(r, ["180° turn time (sec)", "180? turn time (sec)", "180 turn time (sec)"], "7.2")
    damage = fmt_num_with_comma(pick_first(r, ["maximum simulated damage", "torpedo maximum damage", "maximum damage", "damage"]))
    range_km = pick_first(r, ["range (km)", "torpedo range (km)"])
    boost_km = pick_first(r, ["boost distance (km)", "maximum boost distance (km)", "boost range (km)"])
    fire_start = pick_first(r, ["fire-starting chance at launch (%)", "launch fire-starting chance (%)", "fire-starting chance (%)"])
    fire_max = pick_first(r, ["maximum fire-starting chance (%)", "max fire-starting chance (%)", "fire-starting chance (%)"])
    speed_start = pick_first(r, ["speed (kt)", "torpedo speed (kt)", "speed"])
    speed_max = pick_first(r, ["maximum torpedo speed (kt)", "maximum speed (kt)", "max torpedo speed (kt)", "torpedo max speed (kt)"])
    detect_start = pick_first(r, ["detectability by sea (km)", "detectability range (km)", "detectability (km)"])
    detect_max = pick_first(r, ["maximum detectability by sea (km)", "max detectability by sea (km)", "maximum detectability range (km)"])

    def with_unit_or_x(v, unit):
        s = (v or "").strip()
        return f"{s}{unit}" if s else f"x{unit}"

    return render_template(
        template,
        {
            "border_color": border_color,
            "inc_name": name or "소이 가속 어뢰",
            "inc_arrangement": arrangement or "×",
            "inc_reload_sec": f"{reload_s}초" if reload_s else "초",
            "inc_turn_sec": f"{turn_s}초" if turn_s else "7.2초",
            "inc_damage": damage or "0,000",
            "inc_range": with_unit_or_x(range_km, "km"),
            "inc_boost_range": with_unit_or_x(boost_km, "km"),
            "inc_fire_start": with_unit_or_x(fire_start, "%"),
            "inc_fire_max": with_unit_or_x(fire_max, "%"),
            "inc_speed_start": with_unit_or_x(speed_start, "knots"),
            "inc_speed_max": with_unit_or_x(speed_max, "knots"),
            "inc_detect_start": with_unit_or_x(detect_start, "km"),
            "inc_detect_max": with_unit_or_x(detect_max, "km"),
        },
    )


def roman_to_arabic(value):
    table = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }
    s = (value or "").strip().upper()
    if not s:
        return ""
    total = 0
    prev = 0
    for ch in reversed(s):
        cur = table.get(ch, 0)
        if cur == 0:
            return ""
        if cur < prev:
            total -= cur
        else:
            total += cur
            prev = cur
    return str(total)


def clean_ship_name(name):
    n = (name or "").strip()
    n = re.sub(r"\s+", " ", n)
    return n


def parse_name_and_tier(raw_text):
    text = raw_text or ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or "Tier" not in line:
            continue

        tier_match = re.search(r"\bTier\s+([IVXLCDM]+)\b", line, re.IGNORECASE)
        if not tier_match:
            continue
        tier = roman_to_arabic(tier_match.group(1))

        parts = re.split(r"\s+[—\-]\s+|\s+\?\s+", line, maxsplit=1)
        left = parts[0].strip() if parts else line
        # Strip image token prefix, e.g. "Legends_Cruiser_Icon2.png "
        left = re.sub(r"^.*?\.png\s+", "", left, count=1, flags=re.IGNORECASE)
        name = clean_ship_name(left)
        if name:
            return name, tier

    tier_match = re.search(r"\bTier\s+([IVXLCDM]+)\b", text, re.IGNORECASE)
    tier = roman_to_arabic(tier_match.group(1)) if tier_match else ""
    return "", tier


def _clean_nation_text(v):
    s = (v or "").strip().rstrip(".")
    if not s:
        return ""
    s = re.sub(r"(?<=[A-Za-z])\?(?=[A-Za-z])", "-", s)
    s = re.split(r"\s*[•·]\s*|\s+\?\s+|\s+-\s+", s, maxsplit=1)[0].strip()
    s = re.split(r"\b(?:premium|tech tree|special|event|tier)\b", s, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    s = s.rstrip("- ").strip()
    return s


def _canonical_nation_key(v):
    key = (v or "").strip().lower()
    key = key.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    key = re.sub(r"(?<=[a-z])\?(?=[a-z])", "-", key)
    key = re.sub(r"\s+", " ", key).strip()
    key = key.replace(" - ", "-")
    alias = {
        "usa": "american",
        "us": "american",
        "u.s.a.": "american",
        "u.s.": "american",
        "united states": "american",
        "japan": "japanese",
        "germany": "german",
        "france": "french",
        "soviet union": "soviet",
        "ussr": "soviet",
        "russia": "soviet",
        "italy": "italian",
        "spain": "spanish",
        "pan asia": "pan-asian",
        "pan-asia": "pan-asian",
        "pan america": "pan-american",
        "pan-america": "pan-american",
        "pan europe": "pan-european",
        "pan-europe": "pan-european",
        "europe": "pan-european",
    }
    return alias.get(key, key)


def parse_nation(raw_text, db=None):
    text = raw_text or ""
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00A0", " ")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    known_keys = set(DEFAULT_NATION_COLOR_MAP.keys())
    if not isinstance(db, dict):
        db = {}
    db_colors = db.get("nation_colors", {})
    if isinstance(db_colors, dict):
        known_keys.update([_canonical_nation_key(str(k)) for k in db_colors.keys() if k])

    # 1) Explicit metadata line: "Nation: X"
    for line in lines:
        m = re.search(r"\b(?:Nation|Ship|Navy):\s*(.+)$", line, re.IGNORECASE)
        if m:
            nation = _clean_nation_text(m.group(1))
            if nation and _canonical_nation_key(nation) in known_keys:
                return nation

    # 2) Overview line: "... — Nation • Tech Tree • Tier ..."
    for line in lines:
        if "tier" not in line.lower():
            continue
        m = re.search(r"\s+[—\-]\s+(.+)$", line)
        if not m:
            continue
        right = m.group(1)
        # Prefer first bullet token: Nation • Tech Tree • Tier ...
        tokens = [t.strip().rstrip(".") for t in re.split(r"\s*[•·]\s*", right) if t.strip()]
        if tokens:
            nation_token = _clean_nation_text(tokens[0])
            if nation_token and _canonical_nation_key(nation_token) in known_keys:
                return nation_token
        nation = _clean_nation_text(right)
        if nation and _canonical_nation_key(nation) in known_keys:
            return nation

    # 3) Fallback by keyword scan against known nation keys.
    lower_text = text.lower()
    for k in sorted(known_keys, key=len, reverse=True):
        pat = re.escape(k).replace(r"\ ", r"[\s\-‑–—]+").replace(r"\-", r"[\s\-‑–—]+")
        if re.search(rf"(?<![a-z]){pat}(?![a-z])", lower_text):
            return k
    return ""


def parse_ship_class(raw_text):
    text = raw_text or ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = re.search(r"\bClass:\s*(.+)$", line, re.IGNORECASE)
        if m:
            cls = (m.group(1) or "").strip().rstrip(".")
            cls = re.sub(r"^.*?\.png\s*", "", cls, flags=re.IGNORECASE)
            if cls:
                return cls

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or "Tier" not in line:
            continue
        parts = re.split(r"\s+[—\-]\s+|\s+\?\s+", line, maxsplit=1)
        if len(parts) < 2:
            continue
        right = parts[1].strip().rstrip(".")
        tokens = [t.strip() for t in re.split(r"\s*[•?]\s*", right) if t.strip()]
        for idx, tok in enumerate(tokens):
            if re.search(r"^Tier\s+[IVXLCDM]+$", tok, re.IGNORECASE):
                if idx + 1 < len(tokens):
                    return tokens[idx + 1].rstrip(".").strip()
    return ""


def nation_to_border_color(nation, db=None):
    key = _canonical_nation_key(_clean_nation_text(nation))
    if not isinstance(db, dict):
        db = {}
    nation_colors = db.get("nation_colors", {})
    if isinstance(nation_colors, dict):
        for k, v in nation_colors.items():
            kk = _canonical_nation_key(k)
            if kk == key and v:
                return str(v)
    return DEFAULT_NATION_COLOR_MAP.get(key, "808080")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._app_icon_img = None
        self.title("WoWsL Template UI")
        self.geometry("1550x860")

        self._pending_sashes = None
        self._pending_main_sashes = None
        self._pending_db_sashes = None
        self._pending_db_right_sashes = None
        self._convert_after_id = None
        self._save_ui_after_id = None
        self._focus_apply_after_id = None
        self._db_sync_locked = False
        self._focus_sync_locked = False
        self._last_focus_apply_sig = None
        self._closing = False
        self._restore_borderless_on_map = False
        self.db_path = DEFAULT_DB_PATH
        self.template_dir = DATA_DIR
        self.settings_win = None
        self.generated_output = ""
        self.db_search_var = tk.StringVar(value="")
        self.db_focus_font_size_var = tk.IntVar(value=11)
        self.redirect_target_var = tk.StringVar(value="")
        self.heading_equals_var = tk.IntVar(value=4)
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.custom_theme_var = tk.BooleanVar(value=False)
        self.white_mode_var = tk.BooleanVar(value=False)
        self.settings_topmost_var = tk.BooleanVar(value=False)
        self.auto_paste_input_var = tk.BooleanVar(value=False)
        self.auto_paste_description_var = tk.BooleanVar(value=False)
        self.auto_copy_after_convert_var = tk.BooleanVar(value=False)
        # Emergency stable mode: always use native window chrome.
        self.borderless_var = tk.BooleanVar(value=False)
        self._taskbar_refresh_pending = False
        self._taskbar_button_initialized = False
        self._is_maximized = False
        self._normal_geometry = ""
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.show_all_sections_var = tk.BooleanVar(value=True)
        self.show_head_var = tk.BooleanVar(value=True)
        self.show_description_var = tk.BooleanVar(value=True)
        self.show_traits_var = tk.BooleanVar(value=True)
        self.show_weapons_var = tk.BooleanVar(value=True)
        self.show_stats_var = tk.BooleanVar(value=True)
        self.show_aa_var = tk.BooleanVar(value=True)
        self.show_mods_var = tk.BooleanVar(value=True)
        self.show_consumables_var = tk.BooleanVar(value=True)
        self._db_last_search_pos = "1.0"
        self._focus_entries = []
        self._focus_index = 0
        self._focus_category = ""
        self._auto_paste_lock = False
        self._pending_auto_copy_after_convert = False
        self.preview_color_overrides = {}
        self.theme_color_overrides = {}
        self._preview_color_keys = ("pv_link", "pv_macro", "pv_folding", "pv_include")
        self._preview_color_labels = {
            "pv_link": "링크",
            "pv_macro": "매크로",
            "pv_folding": "폴딩",
            "pv_include": "Include",
        }
        self._theme_color_keys = ("bg", "panel", "fg", "border", "title_bg", "title_fg")
        self._theme_color_labels = {
            "bg": "배경",
            "panel": "패널",
            "fg": "글자",
            "border": "테두리",
            "title_bg": "타이틀BG",
            "title_fg": "타이틀FG",
        }

        self._init_windows_app_identity()
        self._build_ui()
        self.load_ui_state()
        self.after(100, self.apply_pending_ui_state)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Map>", self._on_map_event)

    def _init_windows_app_identity(self):
        if not IS_WINDOWS:
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WoWsL.Template.UI")
        except Exception:
            pass

        icon_candidates = [
            os.path.join(APP_DIR, "wowslnamu.ico"),
            os.path.join(DATA_DIR, "wowslnamu.ico"),
            os.path.join(BUNDLE_DIR, "wowslnamu.ico"),
            os.path.join(BUNDLE_DATA_DIR, "wowslnamu.ico"),
            os.path.join(APP_DIR, "wowslnamu.png"),
            os.path.join(DATA_DIR, "wowslnamu.png"),
        ]
        for path in icon_candidates:
            if not path or not os.path.exists(path):
                continue
            try:
                if path.lower().endswith(".ico"):
                    self.iconbitmap(path)
                else:
                    self._app_icon_img = tk.PhotoImage(file=path)
                    self.iconphoto(True, self._app_icon_img)
                break
            except Exception:
                continue

    def _set_db_text_json(self, data):
        self._db_sync_locked = True
        try:
            self.db_text.delete("1.0", tk.END)
            self.db_text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
        finally:
            self._db_sync_locked = False

    def _set_focus_text(self, txt):
        self._focus_sync_locked = True
        try:
            self.db_focus_text.delete("1.0", tk.END)
            self.db_focus_text.insert("1.0", txt)
        finally:
            self._focus_sync_locked = False

    def _build_ui(self):
        self.titlebar = tk.Frame(self, highlightthickness=0, bd=0)
        self.titlebar.pack(fill=tk.X, side=tk.TOP)
        self.titlebar.bind("<ButtonPress-1>", self._on_title_press)
        self.titlebar.bind("<B1-Motion>", self._on_title_drag)
        self.titlebar.bind("<Double-Button-1>", self._on_title_double_click)

        self.title_label = tk.Label(self.titlebar, text="WOWSL 나무위키 편집기", anchor="w")
        self.title_label.pack(side=tk.LEFT, padx=(10, 0), pady=2)
        self.title_label.bind("<ButtonPress-1>", self._on_title_press)
        self.title_label.bind("<B1-Motion>", self._on_title_drag)
        self.title_label.bind("<Double-Button-1>", self._on_title_double_click)

        self.title_btn_close = tk.Button(self.titlebar, text="✕", width=3, command=self.on_close, bd=0, relief="flat")
        self.title_btn_max = tk.Button(self.titlebar, text="□", width=3, command=self._toggle_maximize, bd=0, relief="flat")
        self.title_btn_min = tk.Button(self.titlebar, text="—", width=3, command=self._minimize_window, bd=0, relief="flat")
        self.title_btn_min.bind("<Enter>", self._on_title_btn_enter)
        self.title_btn_min.bind("<Leave>", self._on_title_btn_leave)
        self.title_btn_max.bind("<Enter>", self._on_title_btn_enter)
        self.title_btn_max.bind("<Leave>", self._on_title_btn_leave)
        self.title_btn_close.bind("<Enter>", self._on_close_btn_enter)
        self.title_btn_close.bind("<Leave>", self._on_close_btn_leave)
        self.title_btn_close.pack(side=tk.RIGHT, padx=(0, 2), pady=2)
        self.title_btn_max.pack(side=tk.RIGHT, padx=0, pady=2)
        self.title_btn_min.pack(side=tk.RIGHT, padx=0, pady=2)

        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=(10, 6))

        name_frame = ttk.Frame(self)
        name_frame.pack(fill=tk.X, padx=10, pady=(0, 6))
        ttk.Label(name_frame, text="English Ship Name (auto)").pack(side=tk.LEFT)
        self.ship_name_en_var = tk.StringVar(value="")
        self.ship_name_en_entry = tk.Entry(name_frame, textvariable=self.ship_name_en_var, state="readonly", width=42)
        self.ship_name_en_entry.pack(side=tk.LEFT, padx=6)
        ttk.Label(name_frame, text="Korean Name (manual)").pack(side=tk.LEFT, padx=(12, 0))
        self.ship_name_ko_var = tk.StringVar(value="")
        self.ship_name_ko_entry = tk.Entry(name_frame, textvariable=self.ship_name_ko_var, width=28)
        self.ship_name_ko_entry.pack(side=tk.LEFT, padx=6)
        ttk.Label(name_frame, text="Redirect").pack(side=tk.LEFT, padx=(8, 0))
        self.redirect_entry = tk.Entry(name_frame, textvariable=self.redirect_target_var, width=18)
        self.redirect_entry.pack(side=tk.LEFT, padx=4)
        ttk.Label(name_frame, text="Heading =").pack(side=tk.LEFT, padx=(10, 0))
        self.heading_equals_spin = ttk.Spinbox(
            name_frame,
            from_=2,
            to=6,
            width=4,
            textvariable=self.heading_equals_var,
            command=self.on_heading_equals_change,
        )
        self.heading_equals_spin.pack(side=tk.LEFT, padx=4)
        self.heading_equals_spin.bind("<Return>", self.on_heading_equals_change)
        self.heading_equals_spin.bind("<FocusOut>", self.on_heading_equals_change)
        self.settings_btn = ttk.Button(name_frame, text="⚙", width=3, command=self.toggle_settings_window)
        self.settings_btn.pack(side=tk.RIGHT, padx=(4, 0))

        self.db_path_var = tk.StringVar(value=self.db_path)

        self.template_dir_var = tk.StringVar(value=self.template_dir)

        self.main_vpanes = ttk.Panedwindow(self, orient=tk.VERTICAL)
        self.main_vpanes.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        upper = ttk.Frame(self.main_vpanes)
        db_frame = ttk.LabelFrame(self.main_vpanes, text="DB JSON Viewer")
        self.main_vpanes.add(upper, weight=8)
        self.main_vpanes.add(db_frame, weight=3)

        self.panes = ttk.Panedwindow(upper, orient=tk.HORIZONTAL)
        self.panes.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(self.panes)
        center = ttk.Frame(self.panes)
        right = ttk.Frame(self.panes)
        self.panes.add(left, weight=4)
        self.panes.add(center, weight=2)
        self.panes.add(right, weight=6)

        ttk.Label(left, text="Raw Input").pack(anchor=tk.W)
        self.input_text = tk.Text(left, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.bind("<ButtonRelease-1>", self._on_input_auto_paste_click, add="+")

        ttk.Label(center, text="Description").pack(anchor=tk.W)
        self.description_text = tk.Text(center, wrap=tk.WORD)
        self.description_text.pack(fill=tk.BOTH, expand=True)
        self.description_text.bind("<ButtonRelease-1>", self._on_description_auto_paste_click, add="+")

        ttk.Label(right, text="Preview").pack(anchor=tk.W)
        preview_toolbar = ttk.Frame(right)
        preview_toolbar.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
        ttk.Button(preview_toolbar, text="전체 복사", command=self.copy_all_to_clipboard).pack(side=tk.RIGHT)
        ttk.Checkbutton(
            preview_toolbar,
            text="전체",
            variable=self.show_all_sections_var,
            command=lambda: self.on_section_filter_changed("all"),
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Checkbutton(preview_toolbar, text="헤드", variable=self.show_head_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)
        ttk.Checkbutton(preview_toolbar, text="설명", variable=self.show_description_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)
        ttk.Checkbutton(preview_toolbar, text="특성", variable=self.show_traits_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)
        ttk.Checkbutton(preview_toolbar, text="무장", variable=self.show_weapons_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)
        ttk.Checkbutton(preview_toolbar, text="기본스탯", variable=self.show_stats_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)
        ttk.Checkbutton(preview_toolbar, text="대공", variable=self.show_aa_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)
        ttk.Checkbutton(preview_toolbar, text="강화장치", variable=self.show_mods_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)
        ttk.Checkbutton(preview_toolbar, text="소모품", variable=self.show_consumables_var, command=lambda: self.on_section_filter_changed("item")).pack(side=tk.LEFT)

        self.preview_tabs = ttk.Notebook(right)
        self.preview_tabs.pack(fill=tk.BOTH, expand=True)

        text_tab = ttk.Frame(self.preview_tabs)
        graphic_tab = ttk.Frame(self.preview_tabs)
        self.preview_tabs.add(text_tab, text="Rendered Text")
        self.preview_tabs.add(graphic_tab, text="Graphic")

        self.preview_text = tk.Text(text_tab, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.tag_configure("pv_heading", foreground="#111111")
        self.preview_text.tag_configure("pv_link", foreground="#c62828")
        self.preview_text.tag_configure("pv_angle", foreground="#111111")
        self.preview_text.tag_configure("pv_macro", foreground="#2e7d32")
        self.preview_text.tag_configure("pv_folding", foreground="#6a1b9a")
        self.preview_text.tag_configure("pv_include", foreground="#1565c0")

        self.graph_canvas = tk.Canvas(graphic_tab, bg="#f2f2f2", highlightthickness=0)
        self.graph_scroll = ttk.Scrollbar(graphic_tab, orient=tk.VERTICAL, command=self.graph_canvas.yview)
        self.graph_canvas.configure(yscrollcommand=self.graph_scroll.set)
        self.graph_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.graph_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.graph_canvas.bind("<Configure>", self.refresh_graphic_preview)

        db_top = ttk.Frame(db_frame)
        db_top.pack(fill=tk.X, padx=6, pady=(4, 4))
        ttk.Label(db_top, text="검색").pack(side=tk.LEFT)
        self.db_search_entry = ttk.Entry(db_top, textvariable=self.db_search_var, width=28)
        self.db_search_entry.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Button(db_top, text="다음", command=self.search_db_next).pack(side=tk.LEFT)
        ttk.Label(db_top, text="Selected Entry 폰트").pack(side=tk.LEFT, padx=(10, 2))
        self.db_focus_font_spin = ttk.Spinbox(
            db_top,
            from_=8,
            to=32,
            width=4,
            textvariable=self.db_focus_font_size_var,
            command=self.on_db_focus_font_size_change,
        )
        self.db_focus_font_spin.pack(side=tk.LEFT)
        self.db_focus_font_spin.bind("<Return>", self.on_db_focus_font_size_change)
        self.db_focus_font_spin.bind("<FocusOut>", self.on_db_focus_font_size_change)
        ttk.Button(db_top, text="DB 저장", command=self.save_db_from_viewer).pack(side=tk.RIGHT)
        ttk.Button(db_top, text="DB 다시읽기", command=self.reload_db_from_path).pack(side=tk.RIGHT, padx=(0, 6))
        ttk.Button(db_top, text="New", command=self.create_new_db_entry).pack(side=tk.RIGHT, padx=(0, 6))

        self.db_panes = ttk.Panedwindow(db_frame, orient=tk.HORIZONTAL)
        self.db_panes.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        db_left = ttk.Frame(self.db_panes)
        db_right = ttk.Frame(self.db_panes)
        self.db_panes.add(db_left, weight=2)
        self.db_panes.add(db_right, weight=8)

        db_left_top = ttk.Frame(db_left)
        db_left_top.pack(fill=tk.X)
        ttk.Label(db_left_top, text="Categories").pack(side=tk.LEFT, anchor=tk.W)
        self.db_category_list = tk.Listbox(db_left, exportselection=False)
        self.db_category_list.pack(fill=tk.BOTH, expand=True)
        self.db_category_list.bind("<<ListboxSelect>>", self.on_db_category_select)

        self.db_right_panes = ttk.Panedwindow(db_right, orient=tk.HORIZONTAL)
        self.db_right_panes.pack(fill=tk.BOTH, expand=True)
        self.db_panes.bind("<ButtonRelease-1>", self._schedule_save_ui_state)
        self.db_right_panes.bind("<ButtonRelease-1>", self._schedule_save_ui_state)
        self.main_vpanes.bind("<ButtonRelease-1>", self._schedule_save_ui_state)
        self.panes.bind("<ButtonRelease-1>", self._schedule_save_ui_state)

        db_edit_frame = ttk.Frame(self.db_right_panes)
        db_focus_frame = ttk.LabelFrame(self.db_right_panes, text="Selected Entry")
        self.db_right_panes.add(db_edit_frame, weight=6)
        self.db_right_panes.add(db_focus_frame, weight=4)

        self.db_text = tk.Text(db_edit_frame, height=12, wrap=tk.NONE)
        self.db_text.pack(fill=tk.BOTH, expand=True)
        self.db_text.tag_configure("search_hit", background="#fff59d", foreground="#000000")
        self._db_text_default_bg = self.db_text.cget("bg")
        self._db_text_default_fg = self.db_text.cget("fg")
        self.db_text.bind("<KeyRelease>", self.on_db_text_changed)

        self.db_focus_text = tk.Text(
            db_focus_frame,
            height=8,
            wrap=tk.NONE,
            font=("Malgun Gothic", self.db_focus_font_size_var.get()),
        )
        self.db_focus_text.pack(fill=tk.BOTH, expand=True)
        self._db_focus_default_bg = self.db_focus_text.cget("bg")
        self._db_focus_default_fg = self.db_focus_text.cget("fg")
        self.db_focus_text.bind("<KeyRelease>", self.on_focus_text_changed)
        self.db_focus_text.bind("<MouseWheel>", self.on_focus_wheel)
        self.db_focus_text.bind("<Button-4>", self.on_focus_wheel)
        self.db_focus_text.bind("<Button-5>", self.on_focus_wheel)
        self.db_focus_text.bind("<Control-MouseWheel>", self.on_focus_wheel)
        self.db_focus_text.bind("<Control-Button-4>", self.on_focus_wheel)
        self.db_focus_text.bind("<Control-Button-5>", self.on_focus_wheel)

        self._bind_auto_convert()
        self.bind_all("<Control-s>", self.on_ctrl_s)
        self._apply_theme()
        self._apply_window_chrome()

    def pick_db(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        self.db_path_var.set(path)
        self.reload_db_from_path()
        self.schedule_convert()

    def pick_template(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.template_dir_var.set(path)
        self.schedule_convert()

    def _resolve_db_path_for_read(self):
        cur = (self.db_path_var.get() or "").strip()
        candidates = [cur, DEFAULT_DB_PATH, os.path.join(DATA_DIR, "wowsl_terms.json"), os.path.join(BUNDLE_DATA_DIR, "wowsl_terms.json")]
        for p in candidates:
            if not p:
                continue
            rp = resolve_runtime_data_path(p)
            if rp and os.path.exists(rp):
                # Keep UI path sane for next sessions.
                if cur != rp:
                    self.db_path_var.set(rp)
                return rp
        return cur or DEFAULT_DB_PATH

    def _resolve_template_dir_for_read(self):
        cur = (self.template_dir_var.get() or "").strip()
        candidates = [
            cur,
            DATA_DIR,
            BUNDLE_DATA_DIR,
        ]
        for p in candidates:
            if not p:
                continue
            rp = p
            if rp and os.path.isdir(rp):
                return rp
        return cur or DATA_DIR

    def reload_db_from_path(self):
        try:
            data = load_json(self._resolve_db_path_for_read())
            self.db_text.delete("1.0", tk.END)
            self.db_text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
            self.refresh_db_categories(data)
            try:
                validate_consumable_rule_files()
            except Exception as e:
                messagebox.showerror("Error", f"소모품 파서 data reload failed: {e}")
            self.schedule_convert()
        except Exception as e:
            messagebox.showerror("Error", f"DB load failed: {e}")

    def save_db_from_viewer(self):
        raw = self.db_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showerror("Error", "DB viewer is empty.")
            return
        try:
            data = strict_json_loads(raw)
        except DuplicateJsonKeyError as e:
            # Auto-resolve duplicated keys by parsing with last-key-wins semantics.
            try:
                data = json.loads(raw)
            except Exception:
                messagebox.showerror("Error", f"DB 중복 키 오류: {e}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"DB JSON 파싱 오류: {e}")
            return
        data = dedupe_json_data(data)
        try:
            path = self._resolve_db_path_for_read()
            safe_save_json(path, data)
            self.db_text.delete("1.0", tk.END)
            self.db_text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
            self.refresh_db_categories(data)
            self.schedule_convert()
        except Exception as e:
            messagebox.showerror("Error", f"DB save failed: {e}")

    def on_ctrl_s(self, _event=None):
        self.save_db_from_viewer()
        return "break"

    def apply_focus_entry_to_db(self, _event=None, notify=True, preserve_focus_text=False):
        cat_key = (self._focus_category or "").strip()
        if not cat_key:
            return "break"

        db_raw = self.db_text.get("1.0", tk.END).strip()
        try:
            data = strict_json_loads(db_raw or "{}")
        except DuplicateJsonKeyError as e:
            if notify:
                messagebox.showerror("Error", f"DB 중복 키 오류: {e}")
            return "break"
        except Exception as e:
            if notify:
                messagebox.showerror("Error", f"DB JSON 파싱 오류: {e}")
            return "break"

        snippet_raw = self.db_focus_text.get("1.0", tk.END).strip()
        if not snippet_raw:
            return "break"
        try:
            snippet_obj = strict_json_loads("{\n" + snippet_raw + "\n}")
        except DuplicateJsonKeyError as e:
            if notify:
                messagebox.showerror("Error", f"Selected Entry 중복 키 오류: {e}")
            return "break"
        except Exception as e:
            if notify:
                messagebox.showerror("Error", f"Selected Entry JSON 파싱 오류: {e}")
            return "break"
        if not isinstance(snippet_obj, dict) or len(snippet_obj) != 1:
            if notify:
                messagebox.showerror("Error", "Selected Entry는 단일 엔트리(JSON 1개)여야 합니다.")
            return "break"

        new_key, new_val = next(iter(snippet_obj.items()))
        old_key = ""
        if self._focus_entries and 0 <= self._focus_index < len(self._focus_entries):
            old_key = self._focus_entries[self._focus_index][0]

        cat_val = data.get(cat_key)
        if isinstance(cat_val, dict):
            if old_key and old_key != new_key and new_key in cat_val:
                if notify:
                    messagebox.showerror("Error", f"중복 엔트리 키: {new_key}")
                return "break"
            if old_key and old_key != new_key and old_key in cat_val:
                del cat_val[old_key]
            cat_val[new_key] = new_val
        else:
            data[cat_key] = new_val
        data = dedupe_json_data(data)

        self.db_text.delete("1.0", tk.END)
        self.db_text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
        self.refresh_db_categories(data)
        if not preserve_focus_text:
            self.update_db_focus_entry(cat_key, data)
            if self._focus_entries:
                for i, (k, _) in enumerate(self._focus_entries):
                    if k == new_key:
                        self._focus_index = i
                        break
                self._render_focus_entry_text()
        self.schedule_convert()
        return "break"

    def on_focus_text_changed(self, _event=None):
        self._apply_focus_nation_color(from_editor=True)
        # Auto-apply Selected Entry edits with debounce.
        if self._focus_apply_after_id:
            try:
                self.after_cancel(self._focus_apply_after_id)
            except Exception:
                pass
        self._focus_apply_after_id = self.after(250, self._apply_focus_text_debounced)

    def _apply_focus_text_debounced(self):
        self._focus_apply_after_id = None
        self.apply_focus_entry_to_db(notify=False, preserve_focus_text=True)

    def on_heading_equals_change(self, _event=None):
        try:
            n = int(str(self.heading_equals_var.get()).strip())
        except Exception:
            n = 4
        n = max(2, min(6, n))
        self.heading_equals_var.set(n)
        self.save_ui_state()
        self.schedule_convert()
        return "break"

    def on_dark_mode_change(self):
        if bool(self.dark_mode_var.get()):
            self.custom_theme_var.set(False)
            self.white_mode_var.set(False)
        self._apply_theme()
        self.save_ui_state()

    def on_custom_theme_change(self):
        if bool(self.custom_theme_var.get()):
            self.dark_mode_var.set(False)
            self.white_mode_var.set(False)
        self._apply_theme()
        self.save_ui_state()

    def on_white_mode_change(self):
        if bool(self.white_mode_var.get()):
            self.dark_mode_var.set(False)
            self.custom_theme_var.set(False)
        self._apply_theme()
        self.save_ui_state()

    def on_settings_topmost_change(self):
        try:
            if self.settings_win is not None and self.settings_win.winfo_exists():
                self.settings_win.attributes("-topmost", bool(self.settings_topmost_var.get()))
        except Exception:
            pass
        self.save_ui_state()

    def on_auto_paste_option_change(self):
        self.save_ui_state()

    def on_auto_copy_option_change(self):
        self.save_ui_state()

    def _auto_paste_from_clipboard(self, target):
        if self._auto_paste_lock:
            return False
        try:
            clip = self.clipboard_get()
        except Exception:
            return False
        if not isinstance(clip, str):
            return False
        clip = clip.replace("\r\n", "\n")
        if not clip.strip():
            return False
        widget = self.input_text if target == "input" else self.description_text
        self._auto_paste_lock = True
        try:
            widget.delete("1.0", tk.END)
            widget.insert("1.0", clip)
            widget.mark_set("insert", "1.0")
            widget.see("1.0")
            if bool(self.auto_copy_after_convert_var.get()):
                self._pending_auto_copy_after_convert = True
            self.schedule_convert()
            return True
        finally:
            self._auto_paste_lock = False

    def _on_input_auto_paste_click(self, _event=None):
        if bool(self.auto_paste_input_var.get()):
            self._auto_paste_from_clipboard("input")

    def _on_description_auto_paste_click(self, _event=None):
        if bool(self.auto_paste_description_var.get()):
            self._auto_paste_from_clipboard("description")

    def _build_settings_scrollable_panel(self, parent):
        outer = tk.Frame(parent, bd=0, highlightthickness=0)
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas, bd=0)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_config(_event=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
            except Exception:
                pass

        def _on_canvas_config(event=None):
            try:
                w = event.width if event is not None else canvas.winfo_width()
                canvas.itemconfigure(win_id, width=w)
            except Exception:
                pass

        def _on_mousewheel(event):
            try:
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif getattr(event, "num", None) == 4:
                    canvas.yview_scroll(-1, "units")
                elif getattr(event, "num", None) == 5:
                    canvas.yview_scroll(1, "units")
            except Exception:
                pass
            return "break"

        inner.bind("<Configure>", _on_inner_config)
        canvas.bind("<Configure>", _on_canvas_config)
        def _on_enter(_event=None):
            try:
                canvas.focus_set()
            except Exception:
                pass

        outer.bind("<Enter>", _on_enter)
        canvas.bind("<Enter>", _on_enter)
        inner.bind("<Enter>", _on_enter)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)
        inner.bind("<Button-4>", _on_mousewheel)
        inner.bind("<Button-5>", _on_mousewheel)
        return outer, canvas, scrollbar, inner

    def _bind_mousewheel_recursive(self, widget, callback):
        try:
            widget.bind("<MouseWheel>", callback)
            widget.bind("<Button-4>", callback)
            widget.bind("<Button-5>", callback)
        except Exception:
            pass
        try:
            for ch in widget.winfo_children():
                self._bind_mousewheel_recursive(ch, callback)
        except Exception:
            pass

    def _normalize_hex_color(self, value):
        s = str(value or "").strip()
        if not s:
            return ""
        if not s.startswith("#"):
            s = "#" + s
        if re.fullmatch(r"#[0-9A-Fa-f]{6}", s):
            return s.upper()
        return ""

    def _default_preview_palette(self, dark, fg):
        return {
            "pv_heading": fg,
            "pv_angle": fg,
            "pv_link": "#d98c86" if dark else "#c62828",
            "pv_macro": "#8fbe8f" if dark else "#2e7d32",
            "pv_folding": "#b9a0d9" if dark else "#6a1b9a",
            "pv_include": "#8fb3d9" if dark else "#1565c0",
        }

    def _get_preview_palette(self, dark, fg):
        pal = self._default_preview_palette(dark, fg)
        for k, v in (self.preview_color_overrides or {}).items():
            if k in pal:
                nv = self._normalize_hex_color(v)
                if nv:
                    pal[k] = nv
        return pal

    def _default_theme_palette(self, dark):
        white_var = getattr(self, "white_mode_var", None)
        if bool(white_var.get()) if white_var is not None else False:
            return {
                "bg": "#ffffff",
                "panel": "#ffffff",
                "fg": "#111111",
                "border": "#cfd6e2",
                "title_bg": "#f4f6fa",
                "title_fg": "#111111",
                "title_btn_bg": "#e9eef7",
                "canvas_bg": "#ffffff",
                "insert_fg": "#111111",
            }
        return {
            "bg": "#1b1d21" if dark else "#f3f5f8",
            "panel": "#23262d" if dark else "#ffffff",
            "fg": "#dce1ea" if dark else "#1d2330",
            "border": "#3a3f4b" if dark else "#cfd6e2",
            "title_bg": "#2a2f38" if dark else "#e8edf5",
            "title_fg": "#f2f5fa" if dark else "#1a2230",
            "title_btn_bg": "#343a44" if dark else "#dfe6f1",
            "canvas_bg": "#1f2228" if dark else "#eef2f7",
            "insert_fg": "#ffffff" if dark else "#111111",
        }

    def _get_theme_palette(self, dark):
        pal = self._default_theme_palette(dark)
        if not bool(self.custom_theme_var.get()):
            return pal
        for k in self._theme_color_keys:
            nv = self._normalize_hex_color((self.theme_color_overrides or {}).get(k, ""))
            if nv:
                pal[k] = nv
        # Keep derived colors readable in custom mode.
        pal["title_btn_bg"] = pal["panel"]
        pal["canvas_bg"] = pal["bg"]
        pal["insert_fg"] = pal["fg"]
        return pal

    def _on_preview_color_manual_change(self, tag, var):
        norm = self._normalize_hex_color(var.get())
        if norm:
            self.preview_color_overrides[tag] = norm
            var.set(norm)
        else:
            self.preview_color_overrides.pop(tag, None)
        self._apply_theme()
        self.save_ui_state()

    def _pick_preview_color(self, tag, var):
        current = self._normalize_hex_color(var.get())
        if not current:
            dark = bool(self.dark_mode_var.get())
            fg = "#dce1ea" if dark else "#1d2330"
            current = self._default_preview_palette(dark, fg).get(tag, "#FFFFFF")
        try:
            picked = colorchooser.askcolor(color=current, parent=self.settings_win)
        except Exception:
            picked = (None, None)
        hx = (picked[1] or "").strip()
        if not hx:
            return
        norm = self._normalize_hex_color(hx)
        if not norm:
            return
        var.set(norm)
        self.preview_color_overrides[tag] = norm
        self._apply_theme()
        self.save_ui_state()

    def _reset_preview_color(self, tag, var):
        self.preview_color_overrides.pop(tag, None)
        var.set("")
        self._apply_theme()
        self.save_ui_state()

    def _on_theme_color_manual_change(self, key, var):
        norm = self._normalize_hex_color(var.get())
        if norm:
            self.theme_color_overrides[key] = norm
            var.set(norm)
        else:
            self.theme_color_overrides.pop(key, None)
        self._apply_theme()
        self.save_ui_state()

    def _pick_theme_color(self, key, var):
        current = self._normalize_hex_color(var.get())
        if not current:
            dark = bool(self.dark_mode_var.get())
            current = self._default_theme_palette(dark).get(key, "#FFFFFF")
        try:
            picked = colorchooser.askcolor(color=current, parent=self.settings_win)
        except Exception:
            picked = (None, None)
        hx = (picked[1] or "").strip()
        norm = self._normalize_hex_color(hx)
        if not norm:
            return
        var.set(norm)
        self.theme_color_overrides[key] = norm
        self._apply_theme()
        self.save_ui_state()

    def _reset_theme_color(self, key, var):
        self.theme_color_overrides.pop(key, None)
        var.set("")
        self._apply_theme()
        self.save_ui_state()

    def toggle_settings_window(self):
        if self.settings_win is not None:
            try:
                if self.settings_win.winfo_exists():
                    self._close_settings_window()
                    return
            except Exception:
                pass
        self.open_settings_window()

    def open_settings_window(self):
        if self.settings_win is not None:
            try:
                if self.settings_win.winfo_exists():
                    self._position_settings_window(self.settings_win)
                    self.settings_win.lift()
                    self.settings_win.focus_force()
                    return
            except Exception:
                pass
        win = tk.Toplevel(self)
        self.settings_win = win
        win.title("설정")
        win.resizable(False, False)
        try:
            win.geometry("520x420")
            win.minsize(520, 420)
            win.maxsize(520, 420)
        except Exception:
            pass
        try:
            win.overrideredirect(True)
        except Exception:
            pass
        try:
            win.transient(self)
        except Exception:
            pass
        self.settings_frame = tk.Frame(win, bd=0, highlightthickness=1)
        self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.settings_notebook = None
        self.settings_tab_theme = None
        self.settings_tab_convenience = None
        (
            self.settings_theme_outer,
            self.settings_theme_canvas,
            self.settings_theme_scrollbar,
            self.settings_theme_root,
        ) = self._build_settings_scrollable_panel(self.settings_frame)

        self.settings_theme_header = tk.Frame(self.settings_theme_root, bd=0, highlightthickness=1)
        self.settings_theme_header.pack(fill=tk.X)
        self.settings_theme_label = tk.Label(self.settings_theme_header, text="Theme", anchor="w")
        self.settings_theme_label.pack(fill=tk.X, padx=8, pady=5)

        self.settings_theme_body = tk.Frame(self.settings_theme_root, bd=0, highlightthickness=1)
        self.settings_theme_body.pack(fill=tk.X)
        self.settings_dark_chk = tk.Checkbutton(
            self.settings_theme_body,
            text="Dark mode",
            variable=self.dark_mode_var,
            command=self.on_dark_mode_change,
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        self.settings_dark_chk.pack(fill=tk.X, padx=8, pady=(6, 8))

        self.settings_white_chk = tk.Checkbutton(
            self.settings_theme_body,
            text="White mode",
            variable=self.white_mode_var,
            command=self.on_white_mode_change,
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        self.settings_white_chk.pack(fill=tk.X, padx=8, pady=(0, 6))

        self.settings_custom_chk = tk.Checkbutton(
            self.settings_theme_body,
            text="Custom theme",
            variable=self.custom_theme_var,
            command=self.on_custom_theme_change,
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        self.settings_custom_chk.pack(fill=tk.X, padx=8, pady=(0, 6))

        self.settings_theme_color_rows = tk.Frame(self.settings_theme_body, bd=0)
        self.settings_theme_color_rows.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.settings_theme_color_vars = {}
        self.settings_theme_color_entries = {}
        self.settings_theme_color_pick_btns = {}
        self.settings_theme_color_reset_btns = {}
        for key in self._theme_color_keys:
            row = tk.Frame(self.settings_theme_color_rows, bd=0)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=self._theme_color_labels.get(key, key), anchor="w", width=8).pack(side=tk.LEFT)
            v = tk.StringVar(value=self.theme_color_overrides.get(key, ""))
            self.settings_theme_color_vars[key] = v
            ent = tk.Entry(row, textvariable=v, width=10)
            ent.pack(side=tk.LEFT, padx=(6, 6))
            ent.bind("<Return>", lambda _e, k=key, vv=v: self._on_theme_color_manual_change(k, vv))
            ent.bind("<FocusOut>", lambda _e, k=key, vv=v: self._on_theme_color_manual_change(k, vv))
            self.settings_theme_color_entries[key] = ent
            btn_pick = tk.Button(row, text="Pick", width=7, command=lambda k=key, vv=v: self._pick_theme_color(k, vv), bd=0, relief="flat")
            btn_pick.pack(side=tk.LEFT, padx=(0, 4))
            self.settings_theme_color_pick_btns[key] = btn_pick
            btn_reset = tk.Button(row, text="기본", width=5, command=lambda k=key, vv=v: self._reset_theme_color(k, vv), bd=0, relief="flat")
            btn_reset.pack(side=tk.LEFT)
            self.settings_theme_color_reset_btns[key] = btn_reset

        self.settings_color_header = tk.Frame(self.settings_theme_root, bd=0, highlightthickness=1)
        self.settings_color_header.pack(fill=tk.X, pady=(8, 0))
        self.settings_color_label = tk.Label(self.settings_color_header, text="Preview Colors", anchor="w")
        self.settings_color_label.pack(fill=tk.X, padx=8, pady=5)

        self.settings_color_body = tk.Frame(self.settings_theme_root, bd=0, highlightthickness=1)
        self.settings_color_body.pack(fill=tk.X, pady=(0, 8))
        self.settings_color_vars = {}
        self.settings_color_entries = {}
        self.settings_color_pick_btns = {}
        self.settings_color_reset_btns = {}
        for tag in self._preview_color_keys:
            row = tk.Frame(self.settings_color_body, bd=0)
            row.pack(fill=tk.X, padx=8, pady=3)
            tk.Label(row, text=self._preview_color_labels.get(tag, tag), anchor="w", width=8).pack(side=tk.LEFT)
            v = tk.StringVar(value=self.preview_color_overrides.get(tag, ""))
            self.settings_color_vars[tag] = v
            ent = tk.Entry(row, textvariable=v, width=10)
            ent.pack(side=tk.LEFT, padx=(6, 6))
            ent.bind("<Return>", lambda _e, t=tag, vv=v: self._on_preview_color_manual_change(t, vv))
            ent.bind("<FocusOut>", lambda _e, t=tag, vv=v: self._on_preview_color_manual_change(t, vv))
            self.settings_color_entries[tag] = ent
            btn_pick = tk.Button(row, text="Pick", width=7, command=lambda t=tag, vv=v: self._pick_preview_color(t, vv), bd=0, relief="flat")
            btn_pick.pack(side=tk.LEFT, padx=(0, 4))
            self.settings_color_pick_btns[tag] = btn_pick
            btn_reset = tk.Button(row, text="기본", width=5, command=lambda t=tag, vv=v: self._reset_preview_color(t, vv), bd=0, relief="flat")
            btn_reset.pack(side=tk.LEFT)
            self.settings_color_reset_btns[tag] = btn_reset

        self.settings_convenience_outer = self.settings_theme_outer
        self.settings_convenience_canvas = self.settings_theme_canvas
        self.settings_convenience_scrollbar = self.settings_theme_scrollbar
        self.settings_convenience_root = self.settings_theme_root

        self.settings_convenience_header = tk.Frame(self.settings_convenience_root, bd=0, highlightthickness=1)
        self.settings_convenience_header.pack(fill=tk.X)
        self.settings_convenience_label = tk.Label(self.settings_convenience_header, text="편의성", anchor="w")
        self.settings_convenience_label.pack(fill=tk.X, padx=8, pady=5)

        self.settings_convenience_body = tk.Frame(self.settings_convenience_root, bd=0, highlightthickness=1)
        self.settings_convenience_body.pack(fill=tk.X, pady=(0, 8))
        self.settings_auto_paste_input_chk = tk.Checkbutton(
            self.settings_convenience_body,
            text="인풋 자동 붙여넣기",
            variable=self.auto_paste_input_var,
            command=self.on_auto_paste_option_change,
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        self.settings_auto_paste_input_chk.pack(fill=tk.X, padx=8, pady=(6, 4))
        self.settings_auto_paste_desc_chk = tk.Checkbutton(
            self.settings_convenience_body,
            text="설명 자동 붙여넣기",
            variable=self.auto_paste_description_var,
            command=self.on_auto_paste_option_change,
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        self.settings_auto_paste_desc_chk.pack(fill=tk.X, padx=8, pady=4)
        self.settings_auto_copy_chk = tk.Checkbutton(
            self.settings_convenience_body,
            text="붙여넣기 후 변환되면 자동 전체복사",
            variable=self.auto_copy_after_convert_var,
            command=self.on_auto_copy_option_change,
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        self.settings_auto_copy_chk.pack(fill=tk.X, padx=8, pady=(4, 8))
        self.settings_db_path_row = tk.Frame(self.settings_convenience_root, bd=0, highlightthickness=1)
        self.settings_db_path_row.pack(fill=tk.X, pady=(0, 8))
        self.settings_db_path_label = tk.Label(self.settings_db_path_row, text="DB source path", anchor="w", width=16)
        self.settings_db_path_label.pack(side=tk.LEFT, padx=(8, 4), pady=6)
        self.settings_db_path_entry = tk.Entry(self.settings_db_path_row, textvariable=self.db_path_var)
        self.settings_db_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), pady=6)
        self.settings_db_pick_btn = tk.Button(
            self.settings_db_path_row,
            text="Pick",
            width=7,
            command=self.pick_db,
            bd=0,
            relief="flat",
        )
        self.settings_db_pick_btn.pack(side=tk.LEFT, padx=(0, 8), pady=6)
        self.settings_template_path_row = tk.Frame(self.settings_convenience_root, bd=0, highlightthickness=1)
        self.settings_template_path_row.pack(fill=tk.X, pady=(0, 8))
        self.settings_template_path_label = tk.Label(self.settings_template_path_row, text="Template folder", anchor="w", width=16)
        self.settings_template_path_label.pack(side=tk.LEFT, padx=(8, 4), pady=6)
        self.settings_template_path_entry = tk.Entry(self.settings_template_path_row, textvariable=self.template_dir_var)
        self.settings_template_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), pady=6)
        self.settings_template_pick_btn = tk.Button(
            self.settings_template_path_row,
            text="Pick",
            width=7,
            command=self.pick_template,
            bd=0,
            relief="flat",
        )
        self.settings_template_pick_btn.pack(side=tk.LEFT, padx=(0, 8), pady=6)
        self.settings_topmost_chk = None
        self.settings_quick_btn_row = None
        self.settings_quick_save_btn = None
        self.settings_quick_reload_btn = None
        self.settings_quick_dbsave_btn = None
        self.settings_quick_repos_btn = None

        def _settings_wheel(event):
            canvas = getattr(self, "settings_theme_canvas", None)
            if canvas is None:
                return "break"
            try:
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif getattr(event, "num", None) == 4:
                    canvas.yview_scroll(-1, "units")
                elif getattr(event, "num", None) == 5:
                    canvas.yview_scroll(1, "units")
            except Exception:
                pass
            return "break"

        self._bind_mousewheel_recursive(self.settings_theme_root, _settings_wheel)

        win.protocol("WM_DELETE_WINDOW", self._close_settings_window)
        self._apply_theme_to_settings()
        self._position_settings_window(win)
        try:
            win.deiconify()
            win.lift()
            win.focus_force()
        except Exception:
            pass

    def _position_settings_window(self, win):
        try:
            btn = getattr(self, "settings_btn", None)
            if btn is None or not btn.winfo_exists():
                return
            self.update_idletasks()
            win.update_idletasks()
            bx = btn.winfo_rootx()
            by = btn.winfo_rooty()
            bh = btn.winfo_height()
            ww = win.winfo_width() or 220
            wh = win.winfo_height() or 120
            sx = self.winfo_screenwidth()
            sy = self.winfo_screenheight()
            x = max(0, min(bx - ww + btn.winfo_width(), sx - ww - 8))
            y = max(0, min(by + bh + 6, sy - wh - 8))
            win.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _close_settings_window(self):
        if self.settings_win is None:
            return
        try:
            self.settings_win.destroy()
        except Exception:
            pass
        self.settings_frame = None
        self.settings_notebook = None
        self.settings_tab_theme = None
        self.settings_tab_convenience = None
        self.settings_theme_outer = None
        self.settings_theme_canvas = None
        self.settings_theme_scrollbar = None
        self.settings_theme_root = None
        self.settings_theme_header = None
        self.settings_theme_label = None
        self.settings_theme_body = None
        self.settings_dark_chk = None
        self.settings_white_chk = None
        self.settings_custom_chk = None
        self.settings_theme_color_rows = None
        self.settings_theme_color_vars = None
        self.settings_theme_color_entries = None
        self.settings_theme_color_pick_btns = None
        self.settings_theme_color_reset_btns = None
        self.settings_color_header = None
        self.settings_color_label = None
        self.settings_color_body = None
        self.settings_color_vars = None
        self.settings_color_entries = None
        self.settings_color_pick_btns = None
        self.settings_color_reset_btns = None
        self.settings_convenience_outer = None
        self.settings_convenience_canvas = None
        self.settings_convenience_scrollbar = None
        self.settings_convenience_root = None
        self.settings_convenience_header = None
        self.settings_convenience_label = None
        self.settings_convenience_body = None
        self.settings_auto_paste_input_chk = None
        self.settings_auto_paste_desc_chk = None
        self.settings_auto_copy_chk = None
        self.settings_db_path_row = None
        self.settings_db_path_label = None
        self.settings_db_path_entry = None
        self.settings_db_pick_btn = None
        self.settings_template_path_row = None
        self.settings_template_path_label = None
        self.settings_template_path_entry = None
        self.settings_template_pick_btn = None
        self.settings_topmost_chk = None
        self.settings_quick_btn_row = None
        self.settings_quick_save_btn = None
        self.settings_quick_reload_btn = None
        self.settings_quick_dbsave_btn = None
        self.settings_quick_repos_btn = None
        self.settings_close_btn = None
        self.settings_win = None

    def _apply_theme_to_settings(self):
        if self.settings_win is None:
            return
        try:
            dark = bool(self.dark_mode_var.get())
            tpal = self._get_theme_palette(dark)
            bg = tpal["bg"]
            panel = tpal["panel"]
            fg = tpal["fg"]
            border = tpal["border"]
            section_bg = "#2f5d95" if dark else "#547fb9"
            section_fg = "#f4f7fc"
            btn_bg = tpal["title_btn_bg"]

            self.settings_win.configure(bg=bg)
            if self.settings_frame is not None:
                self.settings_frame.configure(bg=panel, highlightbackground=border, highlightcolor=border)
            theme_canvas = getattr(self, "settings_theme_canvas", None)
            if theme_canvas is not None:
                try:
                    theme_canvas.configure(bg=panel, highlightthickness=0, bd=0)
                except Exception:
                    pass
            conv_canvas = getattr(self, "settings_convenience_canvas", None)
            if conv_canvas is not None:
                try:
                    conv_canvas.configure(bg=panel, highlightthickness=0, bd=0)
                except Exception:
                    pass
            if getattr(self, "settings_theme_root", None) is not None:
                self.settings_theme_root.configure(bg=panel)
            if self.settings_theme_header is not None:
                self.settings_theme_header.configure(bg=section_bg, highlightbackground=border, highlightcolor=border)
            if self.settings_theme_label is not None:
                self.settings_theme_label.configure(bg=section_bg, fg=section_fg)
            if self.settings_theme_body is not None:
                self.settings_theme_body.configure(bg=panel, highlightbackground=border, highlightcolor=border)
            if self.settings_dark_chk is not None:
                self.settings_dark_chk.configure(
                    bg=panel,
                    fg=fg,
                    activebackground=panel,
                    activeforeground=fg,
                    selectcolor=panel,
                )
            if getattr(self, "settings_white_chk", None) is not None:
                self.settings_white_chk.configure(
                    bg=panel,
                    fg=fg,
                    activebackground=panel,
                    activeforeground=fg,
                    selectcolor=panel,
                )
            if getattr(self, "settings_custom_chk", None) is not None:
                self.settings_custom_chk.configure(
                    bg=panel,
                    fg=fg,
                    activebackground=panel,
                    activeforeground=fg,
                    selectcolor=panel,
                )
            if getattr(self, "settings_theme_color_rows", None) is not None:
                self.settings_theme_color_rows.configure(bg=panel)
            if getattr(self, "settings_convenience_root", None) is not None:
                self.settings_convenience_root.configure(bg=panel)
            if getattr(self, "settings_convenience_header", None) is not None:
                self.settings_convenience_header.configure(bg=section_bg, highlightbackground=border, highlightcolor=border)
            if getattr(self, "settings_convenience_label", None) is not None:
                self.settings_convenience_label.configure(bg=section_bg, fg=section_fg)
            if getattr(self, "settings_convenience_body", None) is not None:
                self.settings_convenience_body.configure(bg=panel, highlightbackground=border, highlightcolor=border)
            for chk_name in ("settings_auto_paste_input_chk", "settings_auto_paste_desc_chk", "settings_auto_copy_chk"):
                chk = getattr(self, chk_name, None)
                if chk is not None:
                    chk.configure(
                        bg=panel,
                        fg=fg,
                        activebackground=panel,
                        activeforeground=fg,
                        selectcolor=panel,
                    )
            if getattr(self, "settings_db_path_row", None) is not None:
                self.settings_db_path_row.configure(bg=panel, highlightbackground=border, highlightcolor=border)
            if getattr(self, "settings_db_path_label", None) is not None:
                self.settings_db_path_label.configure(bg=panel, fg=fg)
            if getattr(self, "settings_db_path_entry", None) is not None:
                self.settings_db_path_entry.configure(
                    bg=panel,
                    fg=fg,
                    insertbackground=fg,
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=border,
                    highlightcolor=border,
                )
            if getattr(self, "settings_db_pick_btn", None) is not None:
                self.settings_db_pick_btn.configure(bg=btn_bg, fg=fg, activebackground=panel, activeforeground=fg)
            if getattr(self, "settings_template_path_row", None) is not None:
                self.settings_template_path_row.configure(bg=panel, highlightbackground=border, highlightcolor=border)
            if getattr(self, "settings_template_path_label", None) is not None:
                self.settings_template_path_label.configure(bg=panel, fg=fg)
            if getattr(self, "settings_template_path_entry", None) is not None:
                self.settings_template_path_entry.configure(
                    bg=panel,
                    fg=fg,
                    insertbackground=fg,
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=border,
                    highlightcolor=border,
                )
            if getattr(self, "settings_template_pick_btn", None) is not None:
                self.settings_template_pick_btn.configure(bg=btn_bg, fg=fg, activebackground=panel, activeforeground=fg)
            if getattr(self, "settings_topmost_chk", None) is not None:
                self.settings_topmost_chk.configure(
                    bg=panel,
                    fg=fg,
                    activebackground=panel,
                    activeforeground=fg,
                    selectcolor=panel,
                )
            if getattr(self, "settings_quick_btn_row", None) is not None:
                self.settings_quick_btn_row.configure(bg=panel)
            for btn_name in ("settings_quick_save_btn", "settings_quick_reload_btn", "settings_quick_dbsave_btn", "settings_quick_repos_btn"):
                btn = getattr(self, btn_name, None)
                if btn is not None:
                    try:
                        btn.configure(bg=btn_bg, fg=fg, activebackground=panel, activeforeground=fg)
                    except Exception:
                        pass
            if getattr(self, "settings_color_header", None) is not None:
                self.settings_color_header.configure(bg=section_bg, highlightbackground=border, highlightcolor=border)
            if getattr(self, "settings_color_label", None) is not None:
                self.settings_color_label.configure(bg=section_bg, fg=section_fg)
            if getattr(self, "settings_color_body", None) is not None:
                self.settings_color_body.configure(bg=panel, highlightbackground=border, highlightcolor=border)
            color_vars = getattr(self, "settings_color_vars", {}) or {}
            color_entries = getattr(self, "settings_color_entries", {}) or {}
            color_pick_btns = getattr(self, "settings_color_pick_btns", {}) or {}
            color_reset_btns = getattr(self, "settings_color_reset_btns", {}) or {}

            theme_vars = getattr(self, "settings_theme_color_vars", {}) or {}
            theme_entries = getattr(self, "settings_theme_color_entries", {}) or {}
            theme_pick_btns = getattr(self, "settings_theme_color_pick_btns", {}) or {}
            theme_reset_btns = getattr(self, "settings_theme_color_reset_btns", {}) or {}
            custom_on = bool(self.custom_theme_var.get())
            state_theme = "normal" if custom_on else "disabled"
            for key in self._theme_color_keys:
                tvar = theme_vars.get(key)
                tent = theme_entries.get(key)
                if tvar is not None:
                    norm = self._normalize_hex_color(tvar.get())
                    if norm != tvar.get():
                        tvar.set(norm)
                if tent is not None:
                    try:
                        row = tent.master
                        row.configure(bg=panel)
                        row_label = row.winfo_children()[0] if row.winfo_children() else None
                        if row_label is not None:
                            row_label.configure(bg=panel, fg=fg)
                    except Exception:
                        pass
                    try:
                        tent.configure(
                            bg=panel,
                            fg=fg,
                            insertbackground=fg,
                            relief="flat",
                            highlightthickness=1,
                            highlightbackground=border,
                            highlightcolor=border,
                            state=state_theme,
                        )
                    except Exception:
                        pass
                tpbtn = theme_pick_btns.get(key)
                if tpbtn is not None:
                    try:
                        tpbtn.configure(bg=btn_bg, fg=fg, activebackground=panel, activeforeground=fg, state=state_theme)
                    except Exception:
                        pass
                trbtn = theme_reset_btns.get(key)
                if trbtn is not None:
                    try:
                        trbtn.configure(bg=btn_bg, fg=fg, activebackground=panel, activeforeground=fg, state=state_theme)
                    except Exception:
                        pass
            for tag in self._preview_color_keys:
                var = color_vars.get(tag)
                ent = color_entries.get(tag)
                if var is not None:
                    norm = self._normalize_hex_color(var.get())
                    if norm != var.get():
                        var.set(norm)
                if ent is not None:
                    try:
                        row = ent.master
                        row.configure(bg=panel)
                        row_label = row.winfo_children()[0] if row.winfo_children() else None
                        if row_label is not None:
                            row_label.configure(bg=panel, fg=fg)
                    except Exception:
                        pass
                    try:
                        ent.configure(
                            bg=panel,
                            fg=fg,
                            insertbackground=fg,
                            relief="flat",
                            highlightthickness=1,
                            highlightbackground=border,
                            highlightcolor=border,
                        )
                    except Exception:
                        pass
                pbtn = color_pick_btns.get(tag)
                if pbtn is not None:
                    try:
                        pbtn.configure(bg=btn_bg, fg=fg, activebackground=panel, activeforeground=fg)
                    except Exception:
                        pass
                rbtn = color_reset_btns.get(tag)
                if rbtn is not None:
                    try:
                        rbtn.configure(bg=btn_bg, fg=fg, activebackground=panel, activeforeground=fg)
                    except Exception:
                        pass
            close_btn = getattr(self, "settings_close_btn", None)
            if close_btn is not None:
                close_btn.configure(
                    bg=btn_bg,
                    fg=fg,
                    activebackground=panel,
                    activeforeground=fg,
                )
        except Exception:
            pass

    def on_borderless_hotkey(self, _event=None):
        self.borderless_var.set(False)
        self.on_borderless_change()
        return "break"

    def _on_title_press(self, event):
        # If maximized, restore first so drag-to-move works immediately.
        if self._is_maximized:
            self._toggle_maximize()
            self.update_idletasks()
        self._drag_start_x = int(getattr(event, "x_root", 0) or 0)
        self._drag_start_y = int(getattr(event, "y_root", 0) or 0)

    def _on_title_drag(self, event):
        x_root = int(getattr(event, "x_root", 0) or 0)
        y_root = int(getattr(event, "y_root", 0) or 0)
        dx = x_root - self._drag_start_x
        dy = y_root - self._drag_start_y
        if dx == 0 and dy == 0:
            return
        self._drag_start_x = x_root
        self._drag_start_y = y_root
        cur_x = self.winfo_x()
        cur_y = self.winfo_y()
        self.geometry(f"+{cur_x + dx}+{cur_y + dy}")

    def _on_title_double_click(self, _event=None):
        self._toggle_maximize()
        return "break"

    def _on_close_btn_enter(self, _event=None):
        try:
            self.title_btn_close.configure(bg="#d9534f", fg="#ffffff", activebackground="#c64541", activeforeground="#ffffff")
        except Exception:
            pass

    def _on_close_btn_leave(self, _event=None):
        try:
            bg = getattr(self, "_title_btn_bg", "#dddddd")
            fg = getattr(self, "_title_fg", "#111111")
            active_bg = getattr(self, "_title_bg", bg)
            self.title_btn_close.configure(bg=bg, fg=fg, activebackground=active_bg, activeforeground=fg)
        except Exception:
            pass

    def _on_title_btn_enter(self, event=None):
        try:
            w = getattr(event, "widget", None)
            if w:
                w.configure(bg="#4a4f55", fg="#ffffff", activebackground="#4a4f55", activeforeground="#ffffff")
        except Exception:
            pass

    def _on_title_btn_leave(self, event=None):
        try:
            w = getattr(event, "widget", None)
            if w:
                bg = getattr(self, "_title_btn_bg", "#dddddd")
                fg = getattr(self, "_title_fg", "#111111")
                active_bg = getattr(self, "_title_bg", bg)
                w.configure(bg=bg, fg=fg, activebackground=active_bg, activeforeground=fg)
        except Exception:
            pass

    def _minimize_window(self):
        try:
            if self.borderless_var.get():
                self._restore_borderless_on_map = True
                self.overrideredirect(False)
                self.iconify()
            else:
                self.state("iconic")
        except Exception:
            pass

    def _on_map_event(self, _event=None):
        if self._closing:
            return
        if not self._restore_borderless_on_map:
            return
        self._restore_borderless_on_map = False
        try:
            self.after(30, self._apply_window_chrome)
        except Exception:
            pass

    def _toggle_maximize(self):
        # Native window mode: use Tk states directly.
        if not self.borderless_var.get():
            try:
                if self.state() == "zoomed":
                    self.state("normal")
                    self._is_maximized = False
                else:
                    self.state("zoomed")
                    self._is_maximized = True
            except Exception:
                try:
                    if self._is_maximized:
                        self.state("normal")
                        self._is_maximized = False
                    else:
                        self.state("zoomed")
                        self._is_maximized = True
                except Exception:
                    pass
            try:
                self.title_btn_max.configure(text="❐" if self._is_maximized else "□")
            except Exception:
                pass
            return

        # Borderless + Tk "zoomed" can be unstable on Windows.
        try:
            if IS_WINDOWS:
                hwnd = int(self.winfo_id())
                user32 = ctypes.windll.user32
                SW_MAXIMIZE = 3
                SW_RESTORE = 9
                if self._is_maximized:
                    user32.ShowWindow(hwnd, SW_RESTORE)
                    self._is_maximized = False
                    if self._normal_geometry:
                        try:
                            self.geometry(self._normal_geometry)
                        except Exception:
                            pass
                else:
                    try:
                        self._normal_geometry = self.geometry()
                    except Exception:
                        self._normal_geometry = ""
                    user32.ShowWindow(hwnd, SW_MAXIMIZE)
                    self._is_maximized = True
            else:
                if self._is_maximized:
                    self.state("normal")
                    self._is_maximized = False
                    if self._normal_geometry:
                        try:
                            self.geometry(self._normal_geometry)
                        except Exception:
                            pass
                else:
                    try:
                        self._normal_geometry = self.geometry()
                    except Exception:
                        self._normal_geometry = ""
                    self.state("zoomed")
                    self._is_maximized = True
        except Exception:
            # Last fallback
            try:
                if self._is_maximized:
                    self.state("normal")
                    self._is_maximized = False
                    if self._normal_geometry:
                        try:
                            self.geometry(self._normal_geometry)
                        except Exception:
                            pass
                else:
                    try:
                        self._normal_geometry = self.geometry()
                    except Exception:
                        self._normal_geometry = ""
                    sw = self.winfo_screenwidth()
                    sh = self.winfo_screenheight()
                    self.geometry(f"{sw}x{sh}+0+0")
                    self._is_maximized = True
            except Exception:
                pass
        try:
            self.title_btn_max.configure(text="❐" if self._is_maximized else "□")
        except Exception:
            pass

    def on_borderless_change(self):
        self.borderless_var.set(False)
        self._taskbar_button_initialized = False
        self._apply_window_chrome()
        self.save_ui_state()

    def _force_windows_appwindow(self):
        if not IS_WINDOWS:
            return
        try:
            self.update_idletasks()
            hwnd = int(self.winfo_id())
            if hwnd <= 0:
                return
            GWL_EXSTYLE = -20
            GWL_HWNDPARENT = -8
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_APPWINDOW = 0x00040000
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020
            SW_HIDE = 0
            SW_SHOW = 5

            user32 = ctypes.windll.user32
            try:
                if hasattr(user32, "SetWindowLongPtrW"):
                    user32.SetWindowLongPtrW(hwnd, GWL_HWNDPARENT, 0)
                else:
                    user32.SetWindowLongW(hwnd, GWL_HWNDPARENT, 0)
            except Exception:
                pass
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
            )
            # Borderless windows often miss taskbar buttons until re-shown.
            if self.borderless_var.get() and (not self._taskbar_button_initialized) and (not self._taskbar_refresh_pending):
                self._taskbar_refresh_pending = True
                try:
                    user32.ShowWindow(hwnd, SW_HIDE)
                    user32.ShowWindow(hwnd, SW_SHOW)
                    self.after(40, self._restore_after_taskbar_refresh)
                except Exception:
                    self.withdraw()
                    self.after(40, self._restore_after_taskbar_refresh)
        except Exception:
            pass

    def _restore_after_taskbar_refresh(self):
        try:
            self.deiconify()
        except Exception:
            pass
        self._taskbar_refresh_pending = False
        self._taskbar_button_initialized = True

    def _bring_window_front(self):
        try:
            self.lift()
        except Exception:
            pass
        # Avoid aggressive focus/topmost forcing; it can lock some borderless setups.

    def _apply_window_chrome(self):
        try:
            # Emergency stable mode: force native title bar.
            self.overrideredirect(False)
            if self.titlebar.winfo_ismapped():
                self.titlebar.pack_forget()
        except Exception:
            pass
        # Keep taskbar patch inactive in native-window mode.

    def _apply_theme(self):
        dark = bool(self.dark_mode_var.get())
        pal = self._get_theme_palette(dark)
        bg = pal["bg"]
        panel = pal["panel"]
        fg = pal["fg"]
        insert_fg = pal["insert_fg"]
        canvas_bg = pal["canvas_bg"]
        title_bg = pal["title_bg"]
        title_fg = pal["title_fg"]
        title_btn_bg = pal["title_btn_bg"]
        border = pal["border"]
        self._title_bg = title_bg
        self._title_fg = title_fg
        self._title_btn_bg = title_btn_bg

        try:
            self.configure(bg=bg)
        except Exception:
            pass

        try:
            self.titlebar.configure(bg=title_bg)
            self.title_label.configure(bg=title_bg, fg=title_fg)
            self.title_btn_min.configure(bg=title_btn_bg, fg=title_fg, activebackground=title_bg, activeforeground=title_fg)
            self.title_btn_max.configure(bg=title_btn_bg, fg=title_fg, activebackground=title_bg, activeforeground=title_fg)
            self.title_btn_close.configure(bg=title_btn_bg, fg=title_fg, activebackground=title_bg, activeforeground=title_fg)
        except Exception:
            pass

        try:
            style = ttk.Style(self)
            style.theme_use("clam")
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TLabelframe", background=bg, foreground=fg)
            style.configure("TLabelframe.Label", background=bg, foreground=fg)
            style.configure("TCheckbutton", background=bg, foreground=fg)
            style.configure("TButton", background=bg, foreground=fg)
            style.configure("TNotebook", background=bg)
            style.configure("TNotebook.Tab", background=panel, foreground=fg)
            style.map(
                "TNotebook.Tab",
                background=[("selected", "#2e3440" if dark else "#dde4f0"), ("active", "#2a2f38" if dark else "#e8edf5")],
                foreground=[("selected", "#f0f3f8" if dark else "#1a2230"), ("active", fg)],
            )
            style.configure("TEntry", fieldbackground=panel, foreground=fg)
            style.configure("TSpinbox", fieldbackground=panel, foreground=fg)
            style.configure("TCombobox", fieldbackground=panel, foreground=fg)
            style.configure("TButton", padding=(10, 4))
            style.configure("TCheckbutton", padding=(4, 2))
            style.configure("TLabelframe", borderwidth=1)
            style.configure("TLabelframe.Label", font=("Malgun Gothic", 10, "bold"))
            # Panedwindow sash does not follow Text/Entry colors automatically.
            style.configure("App.TPanedwindow", background=border)
            style.configure("App.Horizontal.TPanedwindow", background=border)
            style.configure("App.Vertical.TPanedwindow", background=border)
            style.map(
                "TEntry",
                fieldbackground=[("readonly", panel), ("disabled", "#3a3a3a" if dark else "#e6e6e6")],
                foreground=[("readonly", fg), ("disabled", "#aaaaaa" if dark else "#777777")],
            )
            style.map(
                "TSpinbox",
                fieldbackground=[("readonly", panel), ("disabled", "#3a3a3a" if dark else "#e6e6e6")],
                foreground=[("readonly", fg), ("disabled", "#aaaaaa" if dark else "#777777")],
            )
        except Exception:
            pass

        def _apply_entry_insert_color(widget):
            try:
                children = widget.winfo_children()
            except Exception:
                return
            for ch in children:
                try:
                    cls = ch.winfo_class()
                except Exception:
                    cls = ""
                if cls in ("TEntry", "Entry", "TSpinbox", "Spinbox"):
                    # ttk Entry/Spinbox: insert cursor color is not controlled by style only.
                    try:
                        ch.configure(insertcolor=insert_fg, insertwidth=2)
                    except Exception:
                        try:
                            ch.configure(insertbackground=insert_fg, insertwidth=2)
                        except Exception:
                            pass
                    if cls == "Entry":
                        try:
                            ch.configure(
                                bg=panel,
                                fg=fg,
                                insertbackground=insert_fg,
                                readonlybackground=panel,
                                disabledforeground="#9aa3b2" if dark else "#666666",
                                relief="flat",
                                highlightthickness=1,
                                highlightbackground=border,
                                highlightcolor=border,
                            )
                        except Exception:
                            pass
                _apply_entry_insert_color(ch)

        _apply_entry_insert_color(self)

        # Bind custom paned style explicitly so sash/separator follows theme.
        for p in (
            getattr(self, "main_vpanes", None),
            getattr(self, "panes", None),
            getattr(self, "db_panes", None),
            getattr(self, "db_right_panes", None),
        ):
            if not p:
                continue
            try:
                p.configure(style="App.TPanedwindow")
            except Exception:
                pass

        widgets = [
            getattr(self, "input_text", None),
            getattr(self, "description_text", None),
            getattr(self, "preview_text", None),
            getattr(self, "db_text", None),
            getattr(self, "db_focus_text", None),
            getattr(self, "db_category_list", None),
        ]
        for w in widgets:
            if not w:
                continue
            try:
                w.configure(
                    bg=panel,
                    fg=fg,
                    insertbackground=insert_fg,
                    relief="flat",
                    bd=0,
                    highlightthickness=1,
                    highlightbackground=border,
                    highlightcolor=border,
                )
            except Exception:
                try:
                    w.configure(bg=panel, fg=fg)
                except Exception:
                    pass

        # Keep "default" focus colors in sync with current theme so
        # _apply_focus_nation_color() does not revert to old (white) colors.
        self._db_focus_default_bg = panel
        self._db_focus_default_fg = fg

        try:
            self.graph_canvas.configure(bg=canvas_bg)
        except Exception:
            pass

        try:
            if dark:
                self.db_text.tag_configure("search_hit", background="#6d5b00", foreground="#ffffff")
            else:
                self.db_text.tag_configure("search_hit", background="#fff59d", foreground="#000000")
        except Exception:
            pass

        try:
            pal = self._get_preview_palette(dark, fg)
            self.preview_text.tag_configure("pv_heading", foreground=pal["pv_heading"])
            self.preview_text.tag_configure("pv_link", foreground=pal["pv_link"])
            self.preview_text.tag_configure("pv_angle", foreground=pal["pv_angle"])
            self.preview_text.tag_configure("pv_macro", foreground=pal["pv_macro"])
            self.preview_text.tag_configure("pv_folding", foreground=pal["pv_folding"])
            self.preview_text.tag_configure("pv_include", foreground=pal["pv_include"])
        except Exception:
            pass

        # Re-apply nation color tint if active.
        self._apply_focus_nation_color(from_editor=False)
        self._apply_db_nation_color_highlight()
        self._apply_theme_to_settings()

    def on_section_filter_changed(self, source="item"):
        section_vars = [
            self.show_head_var,
            self.show_description_var,
            self.show_traits_var,
            self.show_weapons_var,
            self.show_stats_var,
            self.show_aa_var,
            self.show_mods_var,
            self.show_consumables_var,
        ]
        if source == "all":
            if self.show_all_sections_var.get():
                for v in section_vars:
                    v.set(True)
            else:
                for v in section_vars:
                    v.set(False)
        else:
            self.show_all_sections_var.set(all(v.get() for v in section_vars))
        self.save_ui_state()
        self.schedule_convert()

    def _is_section_enabled(self, key):
        if self.show_all_sections_var.get():
            return True
        mapping = {
            "head": self.show_head_var.get(),
            "description": self.show_description_var.get(),
            "traits": self.show_traits_var.get(),
            "main_battery": self.show_weapons_var.get(),
            "secondary": self.show_weapons_var.get(),
            "torpedo": self.show_weapons_var.get(),
            "bomber": self.show_weapons_var.get(),
            "airstrike": self.show_weapons_var.get(),
            "stats": self.show_stats_var.get(),
            "aa": self.show_aa_var.get(),
            "mods": self.show_mods_var.get(),
            "consumables": self.show_consumables_var.get(),
        }
        return bool(mapping.get(key, True))

    def on_db_focus_font_size_change(self, _event=None):
        try:
            sz = int(str(self.db_focus_font_size_var.get()).strip())
        except Exception:
            sz = 11
        sz = max(8, min(32, sz))
        self.db_focus_font_size_var.set(sz)
        try:
            self.db_focus_text.configure(font=("Malgun Gothic", sz))
        except Exception:
            pass
        self.save_ui_state()
        return "break"

    def validate_db_viewer(self):
        raw = self.db_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("DB 검사", "DB viewer is empty.")
            return
        try:
            strict_json_loads(raw)
            messagebox.showinfo("DB 검사", "유효한 JSON이며 중복 키가 없습니다.")
        except DuplicateJsonKeyError as e:
            messagebox.showerror("DB 검사", f"중복 키 오류: {e}")
        except Exception as e:
            messagebox.showerror("DB 검사", f"JSON 파싱 오류: {e}")

    def search_db_next(self):
        q = self.db_search_var.get().strip()
        if not q:
            return
        start = self._db_last_search_pos
        pos = self.db_text.search(q, start, stopindex=tk.END, nocase=True)
        if not pos:
            pos = self.db_text.search(q, "1.0", stopindex=tk.END, nocase=True)
            if not pos:
                return
        end = f"{pos}+{len(q)}c"
        self.db_text.tag_remove("sel", "1.0", tk.END)
        self.db_text.tag_remove("search_hit", "1.0", tk.END)
        self.db_text.tag_add("sel", pos, end)
        self.db_text.tag_add("search_hit", pos, end)
        self.db_text.mark_set(tk.INSERT, end)
        self.db_text.see(pos)
        self._db_last_search_pos = end

    def on_db_text_changed(self, _event=None):
        raw = self.db_text.get("1.0", tk.END).strip()
        if not raw:
            self.refresh_db_categories({})
            self.update_db_focus_entry(None, {})
            self.schedule_convert()
            return
        try:
            data = strict_json_loads(raw)
        except Exception:
            # Keep editing 자유; 카테고리만 유지하고 변환은 시도하지 않음.
            return
        self.refresh_db_categories(data)
        sel = self.db_category_list.curselection()
        if sel:
            key = self.db_category_list.get(sel[0])
            self.update_db_focus_entry(key, data)
        else:
            self.update_db_focus_entry(None, data)
        self.schedule_convert()

    def refresh_db_categories(self, data):
        prev_key = None
        sel = self.db_category_list.curselection()
        if sel:
            try:
                prev_key = self.db_category_list.get(sel[0])
            except Exception:
                prev_key = None
        self.db_category_list.delete(0, tk.END)
        if isinstance(data, dict):
            for k in data.keys():
                self.db_category_list.insert(tk.END, str(k))
        if prev_key:
            for i in range(self.db_category_list.size()):
                if self.db_category_list.get(i) == prev_key:
                    self.db_category_list.selection_clear(0, tk.END)
                    self.db_category_list.selection_set(i)
                    self.db_category_list.activate(i)
                    self.db_category_list.see(i)
                    break

    def _blank_like(self, v):
        if isinstance(v, dict):
            return {k: self._blank_like(val) for k, val in v.items()}
        if isinstance(v, list):
            return []
        if isinstance(v, bool):
            return False
        if isinstance(v, (int, float)):
            return 0
        return ""

    def _default_block_for_category(self, cat_key, cat_val):
        ck = (cat_key or "").strip()
        if ck in ("traits", "mods", "consumables"):
            return {"ko": "", "en": "", "include": ""}
        if ck == "nation_colors":
            return "808080"
        if isinstance(cat_val, dict) and cat_val:
            first_v = next(iter(cat_val.values()))
            return self._blank_like(first_v)
        return {"ko": "", "en": "", "include": ""}

    def _default_new_key_for_category(self, cat_key):
        ck = (cat_key or "").strip()
        if ck in ("traits", "mods", "consumables"):
            return "(영문명)"
        if ck == "nation_colors":
            return "new-nation"
        return "new_key"

    def _next_unique_key(self, base_key, container):
        key = (base_key or "new_key").strip() or "new_key"
        if key not in container:
            return key
        n = 2
        while f"{key} {n}" in container:
            n += 1
        return f"{key} {n}"

    def _select_category(self, key):
        for i in range(self.db_category_list.size()):
            if self.db_category_list.get(i) == key:
                self.db_category_list.selection_clear(0, tk.END)
                self.db_category_list.selection_set(i)
                self.db_category_list.activate(i)
                self.db_category_list.see(i)
                return True
        return False

    def create_new_db_entry(self):
        sel = self.db_category_list.curselection()
        if not sel:
            messagebox.showwarning("New", "카테고리를 먼저 선택하세요.")
            return
        cat_key = self.db_category_list.get(sel[0])
        if not cat_key:
            return

        raw = self.db_text.get("1.0", tk.END).strip()
        try:
            data = strict_json_loads(raw or "{}")
        except Exception:
            try:
                data = json.loads(raw or "{}")
            except Exception as e:
                messagebox.showerror("Error", f"DB JSON 파싱 오류: {e}")
                return
        if not isinstance(data, dict):
            messagebox.showerror("Error", "DB 최상위는 객체(JSON object)여야 합니다.")
            return

        cat_val = data.get(cat_key)
        if cat_val is None:
            data[cat_key] = {}
            cat_val = data[cat_key]
        if not isinstance(cat_val, dict):
            messagebox.showwarning("New", f"'{cat_key}' 카테고리는 엔트리 추가형(dict)이 아닙니다.")
            return

        new_key = self._next_unique_key(self._default_new_key_for_category(cat_key), cat_val)

        cat_val[new_key] = self._default_block_for_category(cat_key, cat_val)
        data = dedupe_json_data(data)

        self.db_text.delete("1.0", tk.END)
        self.db_text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
        self.refresh_db_categories(data)
        self._select_category(cat_key)
        self.update_db_focus_entry(cat_key, data)
        if self._focus_entries:
            for i, (k, _) in enumerate(self._focus_entries):
                if k == new_key:
                    self._focus_index = i
                    break
            self._render_focus_entry_text()
        self.schedule_convert()

    def on_db_category_select(self, _event=None):
        sel = self.db_category_list.curselection()
        if not sel:
            self.update_db_focus_entry(None, None)
            return
        key = self.db_category_list.get(sel[0])
        if not key:
            self.update_db_focus_entry(None, None)
            return
        start = "1.0"
        needle = f"\"{key}\""
        pos = self.db_text.search(needle, start, stopindex=tk.END)
        if pos:
            line = pos.split(".")[0]
            self.db_text.see(f"{line}.0")
            self.db_text.tag_remove("sel", "1.0", tk.END)
            self.db_text.tag_add("sel", pos, f"{pos}+{len(needle)}c")
        try:
            data = strict_json_loads(self.db_text.get("1.0", tk.END).strip() or "{}")
        except Exception:
            data = {}
        self.update_db_focus_entry(key, data)

    def update_db_focus_entry(self, key, data):
        if data is None:
            try:
                data = strict_json_loads(self.db_text.get("1.0", tk.END).strip() or "{}")
            except Exception:
                data = {}
        txt = ""
        self._focus_entries = []
        self._focus_index = 0
        self._focus_category = key or ""
        if key and isinstance(data, dict) and key in data:
            cat_val = data.get(key)
            if isinstance(cat_val, dict):
                # Show one entry at a time: e.g. "Toasty Torpedoes": {...}
                self._focus_entries = list(cat_val.items())
            else:
                self._focus_entries = [(key, cat_val)]
            txt = self._format_focus_entry()
        self._render_focus_entry_text(txt)
        self._apply_db_nation_color_highlight()

    def _render_focus_entry_text(self, txt=None):
        if txt is None:
            txt = self._format_focus_entry()
        self.db_focus_text.delete("1.0", tk.END)
        self.db_focus_text.insert("1.0", txt)
        self._apply_focus_nation_color(from_editor=False)
        self._apply_db_nation_color_highlight()

    def _clear_db_nation_color_highlight(self):
        try:
            self.db_text.tag_remove("nation_color_line", "1.0", tk.END)
        except Exception:
            pass
        try:
            self.db_text.tag_remove("nation_color_key", "1.0", tk.END)
        except Exception:
            pass

    def _apply_db_nation_color_highlight(self):
        self._clear_db_nation_color_highlight()
        if (self._focus_category or "").strip() != "nation_colors":
            return
        if not self._focus_entries or not (0 <= self._focus_index < len(self._focus_entries)):
            return

        key, value = self._focus_entries[self._focus_index]
        k = str(key or "").strip()
        s = str(value or "").strip()
        if s.startswith("#"):
            s = s[1:]
        if not k or not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
            return

        color = "#" + s
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        fg = "#000000" if brightness >= 170 else "#ffffff"

        needle = f"\"{k}\""
        pos = self.db_text.search(needle, "1.0", stopindex=tk.END)
        if not pos:
            return
        line = pos.split(".")[0]
        line_start = f"{line}.0"
        line_end = f"{line}.end"
        key_end = f"{pos}+{len(needle)}c"
        try:
            self.db_text.tag_configure("nation_color_line", background=color, foreground=fg)
            self.db_text.tag_configure("nation_color_key", background=color, foreground=fg)
            self.db_text.tag_add("nation_color_line", line_start, line_end)
            self.db_text.tag_add("nation_color_key", pos, key_end)
        except Exception:
            pass

    def _apply_focus_nation_color(self, from_editor=False):
        # Highlight nation_colors entries with their actual color.
        try:
            self.db_focus_text.configure(
                bg=self._db_focus_default_bg,
                fg=self._db_focus_default_fg,
                insertbackground=self._db_focus_default_fg,
            )
        except Exception:
            pass

        if (self._focus_category or "").strip() != "nation_colors":
            return

        value = ""
        if from_editor:
            snippet_raw = self.db_focus_text.get("1.0", tk.END).strip()
            try:
                obj = strict_json_loads("{\n" + snippet_raw + "\n}")
                if isinstance(obj, dict) and obj:
                    value = str(next(iter(obj.values())))
            except Exception:
                value = ""
        if not value and self._focus_entries and 0 <= self._focus_index < len(self._focus_entries):
            value = str(self._focus_entries[self._focus_index][1])

        s = (value or "").strip()
        if s.startswith("#"):
            s = s[1:]
        s = s.strip()
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
            return

        color = "#" + s
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        # Perceived brightness threshold for readable foreground.
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        fg = "#000000" if brightness >= 170 else "#ffffff"
        try:
            self.db_focus_text.configure(bg=color, fg=fg, insertbackground=fg)
        except Exception:
            pass

    def _format_focus_entry(self):
        if not self._focus_entries:
            return ""
        k, v = self._focus_entries[self._focus_index]
        wrapped = json.dumps({k: v}, ensure_ascii=False, indent=2)
        if wrapped.startswith("{\n") and wrapped.endswith("\n}"):
            return wrapped[2:-2].rstrip()
        return wrapped

    def on_focus_wheel(self, event):
        ctrl_pressed = bool(getattr(event, "state", 0) & 0x0004)
        delta = 0
        if hasattr(event, "delta") and event.delta:
            delta = -1 if event.delta < 0 else 1
        elif getattr(event, "num", None) == 5:
            delta = -1
        elif getattr(event, "num", None) == 4:
            delta = 1
        if delta == 0:
            return "break"

        if ctrl_pressed:
            try:
                cur = int(self.db_focus_font_size_var.get())
            except Exception:
                cur = 11
            self.db_focus_font_size_var.set(max(8, min(32, cur + delta)))
            self.on_db_focus_font_size_change()
            return "break"

        size = len(self._focus_entries)
        if size <= 1:
            return "break"
        self._focus_index = max(0, min(size - 1, self._focus_index - delta))
        self._render_focus_entry_text()
        return "break"

    def _bind_auto_convert(self):
        self.input_text.bind("<KeyRelease>", self.schedule_convert)
        self.input_text.bind("<<Paste>>", self.schedule_convert)
        self.input_text.bind("<<Cut>>", self.schedule_convert)
        self.description_text.bind("<KeyRelease>", self.schedule_convert)
        self.description_text.bind("<<Paste>>", self.schedule_convert)
        self.description_text.bind("<<Cut>>", self.schedule_convert)
        self.ship_name_ko_var.trace_add("write", lambda *_: self.schedule_convert())
        self.redirect_target_var.trace_add("write", lambda *_: self.schedule_convert())
        self.heading_equals_var.trace_add("write", lambda *_: self.schedule_convert())
        self.db_path_var.trace_add("write", lambda *_: self.schedule_convert())
        self.template_dir_var.trace_add("write", lambda *_: self.schedule_convert())
        self.db_search_var.trace_add("write", lambda *_: self._reset_db_search_pos())
        self.db_search_entry.bind("<Return>", lambda _e: (self.search_db_next(), "break")[1])

    def _reset_db_search_pos(self):
        self._db_last_search_pos = "1.0"


    def schedule_convert(self, _event=None):
        if self._closing:
            return
        if self._convert_after_id:
            try:
                self.after_cancel(self._convert_after_id)
            except Exception:
                pass
        self._convert_after_id = self.after(250, self._do_scheduled_convert)

    def _do_scheduled_convert(self):
        self._convert_after_id = None
        try:
            self.convert()
            if self._pending_auto_copy_after_convert and bool(self.auto_copy_after_convert_var.get()):
                self.copy_all_to_clipboard()
            self._pending_auto_copy_after_convert = False
        except Exception as e:
            # Keep auto-convert loop alive even if one conversion fails.
            tb = traceback.format_exc(limit=2)
            self.generated_output = f"[convert error] {e}\n{tb}"
            self._pending_auto_copy_after_convert = False
            self.refresh_preview()

    def copy_all_to_clipboard(self):
        text = self.generated_output or ""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()

    def convert(self):
        src = self.input_text.get("1.0", tk.END).strip()
        db = None
        db_raw = self.db_text.get("1.0", tk.END).strip()
        if db_raw:
            try:
                db = strict_json_loads(db_raw)
            except Exception:
                db = None
        if db is None:
            try:
                db = load_json(self._resolve_db_path_for_read())
            except Exception:
                db = {}
        if not isinstance(db, dict):
            db = {}
        name_en, tier_num = parse_name_and_tier(src)
        nation = parse_nation(src, db=db)
        ship_class = parse_ship_class(src)
        border = nation_to_border_color(nation, db=db)
        rules = get_db_rules(db)
        self.ship_name_en_var.set(name_en)
        name_display = self.ship_name_ko_var.get().strip() or name_en or "(메뉴얼 함선명)"
        desc_text = self.description_text.get("1.0", tk.END).strip()
        tier_display = tier_num or ""
        set_template_dir_override(self._resolve_template_dir_for_read())
        try:
            template = load_text(DEFAULT_TEMPLATE_PATH)
        except Exception:
            template = (
                "==== [[{{ship_name}}]] - {{tier}}티어 ====\n\n"
                "||<tablewidth=100%><width=40%><table bordercolor=#{{border_color}}> "
                "[[파일:워쉽 레전드 {{ship_name}}.png|width=80%]] ||<width=60%> ||"
            )

        out = render_template(
            template,
            {
                "ship_name": name_display,
                "tier": tier_display,
                "tier_suffix": f" - {tier_display}티어" if tier_display else "",
                "border_color": border,
                "nation": nation,
                "ship_name_en": name_en,
                "description": desc_text,
            },
        )
        desc = desc_text
        if desc and self._is_section_enabled("description"):
            out = re.sub(r"(\|\|<width=60%>)\s*\|\|", r"\1 " + desc + " ||", out, count=1)
        elif not self._is_section_enabled("description"):
            out = re.sub(r"^.*\|\|<width=60%>.*\|\|.*$", "", out, count=1, flags=re.MULTILINE)
        if not tier_display:
            out = re.sub(r"\s*-\s*n티어", "", out)
            out = re.sub(r"\s*-\s*티어", "", out)
        redirect_target = (self.redirect_target_var.get() or "").strip()
        try:
            heading_eq_n = int(str(self.heading_equals_var.get()).strip())
        except Exception:
            heading_eq_n = 4
        heading_eq_n = max(2, min(6, heading_eq_n))
        heading_mark = "=" * heading_eq_n
        heading_tier = f" - {tier_display}티어" if tier_display else ""
        if self._is_section_enabled("head"):
            if redirect_target:
                out = re.sub(
                    r"^=+.*?=+$",
                    f"{heading_mark} [[{redirect_target}|{name_display}]]{heading_tier} {heading_mark}",
                    out,
                    count=1,
                    flags=re.MULTILINE,
                )
            else:
                out = re.sub(
                    r"^=+.*?=+$",
                    f"{heading_mark} {name_display}{heading_tier} {heading_mark}",
                    out,
                    count=1,
                    flags=re.MULTILINE,
                )
        else:
            out = re.sub(r"^=+.*?=+\s*(?:\n+)?", "", out, count=1, flags=re.MULTILINE)
            out = re.sub(r"^\n+", "", out)
        trait_names_en = parse_trait_names(src)
        lang = "ko"
        trait_include_names = [translate_trait_include(n, db, lang=lang) for n in trait_names_en]
        trait_include_names = dedupe_preserve_order(trait_include_names, key_fn=lambda x: normalize_token(x))
        traits_block = build_traits_block(trait_include_names, border)
        main_bat = parse_main_battery(src)

        section_blocks = [("traits", traits_block)]

        if main_bat.get("main artillery name"):
            section_blocks.append(("main_battery", build_main_battery_block(main_bat, border, ship_name_en=name_en)))

        secondary_rows = parse_secondary_armaments(src)
        if secondary_rows and any((r.get("name") or r.get("secondary battery name") or r.get("arrangement")) for r in secondary_rows):
            section_blocks.append(("secondary", build_secondary_block(secondary_rows, border, ship_name_en=name_en)))

        if has_section(src, [r"^Torpedoes?\b", r"^TORPEDOES?\b", r"Torpedo Armament", r"Legends_Torpedo\.png"]):
            has_deep_water = any(normalize_token(t) in ("deep water", "deepwater") for t in trait_names_en)
            has_toasty_torpedoes = any(normalize_token(t) == "toasty torpedoes" for t in trait_names_en)
            torp_rows = parse_torpedo_armaments(src)
            if has_toasty_torpedoes:
                section_blocks.append(("torpedo", build_incendiary_torpedo_block(torp_rows, border)))
            else:
                section_blocks.append(("torpedo", build_torpedo_block(torp_rows, border, is_deep_water=has_deep_water, ship_name_en=name_en)))

        if has_section(src, [r"Incendiary Torpedo", r"Flame Torpedo"]) and not any(
            normalize_token(t) == "toasty torpedoes" for t in trait_names_en
        ):
            section_blocks.append(("torpedo", build_simple_block(DEFAULT_INCENDIARY_TORPEDO_TEMPLATE_PATH, border)))

        aircraft_entries = []
        if has_section(src, [r"^Torpedo Bombers?\b", r"^TORPEDO BOMBERS?\b", r"^TORPEDO BOMBER\b"]):
            torpedo_aircraft_block = build_torpedo_bomber_block(parse_torpedo_bomber_section(src), border)
            if torpedo_aircraft_block and torpedo_aircraft_block.strip():
                aircraft_entries.append(("Torpedo", "뇌격기", torpedo_aircraft_block))

        has_carpet_bombing = any(normalize_token(t) in rules["carpet_trait_keys"] for t in trait_names_en)
        has_ap_bomb = any(normalize_token(t) in rules["ap_trait_keys"] for t in trait_names_en)
        bomber_bomb_type = rules["bomb_type_ap_ko"] if has_ap_bomb else rules["bomb_type_default_ko"]
        has_skip_bombers = has_section(src, [r"^Skip Bombers?\b", r"^SKIP BOMBERS?\b", r"^SKIP BOMBER\b"]) or any(
            normalize_token(t) in rules["low_alt_trait_keys"] for t in trait_names_en
        )
        if has_section(src, [r"^Dive Bombers?\b", r"^Skip Bombers?\b", r"^DIVE BOMBERS?\b", r"^SKIP BOMBERS?\b", r"^DIVE BOMBER\b"]):
            if has_carpet_bombing:
                dive_stats = parse_bomber_section(src, [r"^Dive Bombers?\b", r"^DIVE BOMBERS?\b", r"^Skip Bombers?\b", r"^SKIP BOMBERS?\b"])
                bombing_mode = rules["mode_low_alt_ko"] if has_skip_bombers else rules["mode_carpet_ko"]
                carpet_block = build_carpet_bomber_block(dive_stats, border, bomb_type=bomber_bomb_type, bombing_mode=bombing_mode)
                if carpet_block and carpet_block.strip():
                    aircraft_entries.append(("Carpet", "융단 폭격기", carpet_block))
            else:
                if has_skip_bombers:
                    skip_data = parse_skip_bomber_section(src)
                    low_alt_block = build_low_alt_bomber_block(skip_data, border, bomb_type=bomber_bomb_type)
                    if low_alt_block and low_alt_block.strip():
                        aircraft_entries.append(("LowAltitude", "저공 폭격기", low_alt_block))
                else:
                    dive_data = parse_dive_bomber_section(src)
                    dive_block = build_dive_bomber_block(dive_data, border, bomb_type=bomber_bomb_type)
                    if dive_block and dive_block.strip():
                        aircraft_entries.append(("Dive", "급강하 폭격기", dive_block))

        if has_section(src, [r"Low Altitude Bombers?", r"LOW ALTITUDE BOMBERS?"]) and not has_skip_bombers:
            low_alt_data = parse_bomber_section(src, [r"^Low Altitude Bombers?\b", r"^LOW ALTITUDE BOMBERS?\b"])
            low_alt_block = build_low_alt_bomber_block(low_alt_data, border, bomb_type=bomber_bomb_type)
            if low_alt_block and low_alt_block.strip():
                aircraft_entries.append(("LowAltitude", "저공 폭격기", low_alt_block))

        if aircraft_entries:
            section_blocks.append(("bomber", build_aircraft_tabs_block(aircraft_entries, border, ship_name_en=name_en)))

        if has_section(src, [r"^Bomb Airstrike\b", r"^BOMB AIRSTRIKE\b"]):
            section_blocks.append(("airstrike", build_airstrike_block(parse_bomb_airstrike(src), border, mode="bomb")))
        if has_section(src, [r"^Torpedo Airstrike\b", r"^TORPEDO AIRSTRIKE\b"]):
            section_blocks.append(("airstrike", build_airstrike_block(parse_torpedo_airstrike(src), border, mode="torpedo")))

        if has_section(src, [r"^Survivability\b", r"^Maneuverability\b", r"^Concealment\b"]):
            section_blocks.append(("stats", build_surv_maneuver_conceal_block(parse_surv_maneuver_conceal(src), border, ship_class=ship_class)))

        if has_section(src, [r"^Anti-Aircraft Artillery\b", r"^AA ARMAMENT\b"]):
            section_blocks.append(("aa", build_aa_block(parse_aa_armaments(src), border)))

        if has_section(src, [r"^Modifications\b", r"^MODIFICATIONS\b", r"^Modifications\s+for\s+Aircraft\s+Carriers?\b"]):
            mods_block = build_mods_block(parse_modifications(src), border, db=db, lang=lang)
            if mods_block:
                section_blocks.append(("mods", wrap_folding_block(mods_block)))

        if has_section(src, [r"^Consumables\b", r"^CONSUMABLES\b"]):
            cons_slots = parse_consumables(src)
            if normalize_token(ship_class) == "aircraft carrier":
                cv_cons_block = build_cv_consumables_block(cons_slots, border, db=db, lang=lang)
                if cv_cons_block:
                    section_blocks.append(("consumables", wrap_folding_block(cv_cons_block)))
            else:
                cons_block = build_consumables_block(cons_slots, border, db=db, lang=lang)
                if cons_block:
                    section_blocks.append(("consumables", wrap_folding_block(cons_block)))

        filtered_blocks = []
        for section_key, block_text in section_blocks:
            if not self._is_section_enabled(section_key):
                continue
            if block_text and block_text.strip():
                filtered_blocks.append(block_text.strip())

        clean_blocks = filtered_blocks
        clean_blocks = dedupe_preserve_order(
            clean_blocks,
            key_fn=lambda x: re.sub(r"\s+", " ", x.strip()),
        )
        out = out.rstrip()
        if clean_blocks:
            blocks_text = "\n\n".join(clean_blocks)
            out = f"{out}\n\n{blocks_text}" if out else blocks_text
        self.generated_output = out
        self.refresh_preview()

    def refresh_preview(self, _event=None):
        src = self.generated_output
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", src)
        self._apply_preview_syntax_highlight(src)
        self.refresh_graphic_preview()

    def _apply_preview_syntax_highlight(self, src):
        try:
            for tag in ("pv_heading", "pv_link", "pv_angle", "pv_macro", "pv_folding", "pv_include"):
                self.preview_text.tag_remove(tag, "1.0", tk.END)
        except Exception:
            return
        if not src:
            return

        def _idx(pos):
            return f"1.0+{pos}c"

        for m in re.finditer(r"^=+.*?=+\s*$", src, re.MULTILINE):
            self.preview_text.tag_add("pv_heading", _idx(m.start()), _idx(m.end()))
        for m in re.finditer(r"\[\[.*?\]\]", src):
            self.preview_text.tag_add("pv_link", _idx(m.start()), _idx(m.end()))
        for m in re.finditer(r"\[include\([^\]]+\)\]", src):
            self.preview_text.tag_add("pv_include", _idx(m.start()), _idx(m.end()))
        for m in re.finditer(r"<[^>\n]+>", src):
            self.preview_text.tag_add("pv_angle", _idx(m.start()), _idx(m.end()))
        for m in re.finditer(r"\{\{\{.*?\}\}\}", src):
            self.preview_text.tag_add("pv_macro", _idx(m.start()), _idx(m.end()))
        for m in re.finditer(r"\{\{\{#!folding.*?$", src, re.MULTILINE):
            self.preview_text.tag_add("pv_folding", _idx(m.start()), _idx(m.end()))

    def refresh_graphic_preview(self, _event=None):
        text = (self.generated_output or "").strip()
        dark_preview = bool(self.dark_mode_var.get())
        self.graph_canvas.delete("all")
        w = max(self.graph_canvas.winfo_width(), 900)
        x0, x1 = 20, w - 20
        y = 20

        def clean_cell(cell):
            s = cell or ""
            s = s.replace("[br]", "\n")
            s = re.sub(r"\[include\((.*?)\)\]", r"\1", s)
            s = re.sub(r"\{\{\{#([0-9A-Fa-f]{6})\s*", "", s)
            s = s.replace("{{{", "").replace("}}}", "")
            return s.strip()

        def parse_cell(raw_cell):
            s = (raw_cell or "").strip()
            cell = {
                "text": "",
                "colspan": 1,
                "rowspan": 1,
                "width_pct": None,
                "bgcolor": None,
                "text_color": "#111111",
                "is_header": False,
            }
            while s.startswith("<"):
                m = re.match(r"^<([^>]+)>", s)
                if not m:
                    break
                token = m.group(1).strip()
                low = token.lower()
                if low.startswith("-") and low[1:].isdigit():
                    cell["colspan"] = max(1, int(low[1:]))
                elif low.startswith("|") and low[1:].isdigit():
                    cell["rowspan"] = max(1, int(low[1:]))
                elif low.startswith("width="):
                    wv = token.split("=", 1)[1].strip().rstrip("%")
                    try:
                        cell["width_pct"] = float(wv)
                    except Exception:
                        pass
                elif low.startswith("bgcolor="):
                    v = token.split("=", 1)[1].strip()
                    if not v.startswith("#"):
                        v = "#" + v
                    if re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
                        cell["bgcolor"] = v
                elif token.startswith("#") and re.fullmatch(r"#[0-9A-Fa-f]{6}", token):
                    cell["bgcolor"] = token
                    cell["is_header"] = True
                s = s[m.end():].lstrip()

            tcol = re.search(r"\{\{\{#([0-9A-Fa-f]{6})", s)
            if tcol:
                cell["text_color"] = "#" + tcol.group(1)
            if "{{{#FFFFFF" in s or "{{{#ffffff" in s:
                cell["is_header"] = True
            if cell["bgcolor"]:
                cell["is_header"] = cell["is_header"] or cell["bgcolor"].lower() != "#f7f7f7"
            cell["text"] = clean_cell(s)
            return cell

        def parse_table_row(line):
            raw_cells = [c for c in line.split("||")[1:-1]]
            return [parse_cell(c) for c in raw_cells]

        def layout_rows(rows):
            placed = []
            span_tracker = {}
            ncols = 0
            for r, cells in enumerate(rows):
                # advance rowspan tracker to this row
                occupied = set()
                for c in list(span_tracker.keys()):
                    if span_tracker[c] > 0:
                        occupied.add(c)
                        span_tracker[c] -= 1
                    else:
                        del span_tracker[c]

                col = 0
                row_cells = []
                for cell in cells:
                    while col in occupied:
                        col += 1
                    cell_col = col
                    cs = max(1, int(cell.get("colspan", 1)))
                    rs = max(1, int(cell.get("rowspan", 1)))
                    for cc in range(cell_col, cell_col + cs):
                        if rs > 1:
                            span_tracker[cc] = rs - 1
                    row_cells.append((cell_col, cell))
                    col = cell_col + cs
                    ncols = max(ncols, col)
                placed.append(row_cells)
            return placed, max(1, ncols)

        lines = text.splitlines() if text else []
        table_lines = []
        row_h = 42

        def flush_table():
            nonlocal y, table_lines
            if not table_lines:
                return
            parsed_rows = [parse_table_row(ln) for ln in table_lines]
            placed_rows, ncols = layout_rows(parsed_rows)
            col_w = (x1 - x0) / max(1, ncols)
            border_color = "#cfcfcf"
            first_line = table_lines[0]
            m = re.search(r"bordercolor=#([0-9A-Fa-f]{6})", first_line)
            if m:
                border_color = "#" + m.group(1)

            for r, row_cells in enumerate(placed_rows):
                for c, cell in row_cells:
                    cs = max(1, int(cell.get("colspan", 1)))
                    rs = max(1, int(cell.get("rowspan", 1)))
                    cx0 = x0 + c * col_w
                    cx1 = x0 + (c + cs) * col_w
                    cy0 = y + r * row_h
                    cy1 = y + (r + rs) * row_h
                    if dark_preview:
                        fill = cell.get("bgcolor") or ("#313844" if cell.get("is_header") else "#272d36")
                        tcolor = cell.get("text_color") or ("#f2f5fa" if cell.get("is_header") else "#dce1ea")
                        # Avoid dazzling white cells in dark preview.
                        low_fill = fill.lower()
                        if low_fill in ("#ffffff", "#fff", "#f7f7f7", "#ececec", "#f2f2f2"):
                            fill = "#2b313a" if cell.get("is_header") else "#252b33"
                            tcolor = "#dce1ea"
                    else:
                        fill = cell.get("bgcolor") or ("#ececec" if cell.get("is_header") else "#f7f7f7")
                        tcolor = cell.get("text_color") or ("#ffffff" if cell.get("is_header") else "#111111")
                        if fill.lower() in ("#ffffff", "#fff"):
                            tcolor = "#111111"
                    self.graph_canvas.create_rectangle(cx0, cy0, cx1, cy1, outline=border_color, fill=fill, width=1)
                    self.graph_canvas.create_text(
                        (cx0 + cx1) / 2,
                        (cy0 + cy1) / 2,
                        text=cell.get("text", ""),
                        fill=tcolor,
                        font=("Malgun Gothic", 10),
                        width=max(40, int((cx1 - cx0) - 10)),
                        justify="center",
                    )
            y += len(placed_rows) * row_h + 6
            table_lines = []

        for raw in lines:
            line = raw.strip()
            if not line:
                flush_table()
                y += 8
                continue

            if line.startswith("||") and line.endswith("||"):
                table_lines.append(line)
            else:
                flush_table()
                self.graph_canvas.create_text(
                    x0,
                    y,
                    anchor="nw",
                    text=clean_cell(line),
                    fill="#dce1ea" if dark_preview else "#222222",
                    font=("Malgun Gothic", 10),
                    width=x1 - x0,
                )
                y += 24

        flush_table()
        self.graph_canvas.configure(scrollregion=(0, 0, w, max(300, y + 20)))

    def load_ui_state(self):
        if not os.path.exists(UI_STATE_PATH):
            return
        try:
            state = load_json(UI_STATE_PATH)
        except Exception:
            return

        geom = state.get("geometry", "")
        if geom:
            self.geometry(geom)

        self.db_path_var.set(state.get("db_path", self.db_path_var.get()))
        template_dir_state = (state.get("template_dir", "") or "").strip()
        if not template_dir_state:
            old_template_path = (state.get("template_path", "") or "").strip()
            if old_template_path:
                template_dir_state = old_template_path if os.path.isdir(old_template_path) else os.path.dirname(old_template_path)
        self.template_dir_var.set(template_dir_state or self.template_dir_var.get())
        self.ship_name_ko_var.set(state.get("ship_name_ko", ""))
        self.redirect_target_var.set(state.get("redirect_target", ""))
        self.dark_mode_var.set(bool(state.get("dark_mode", False)))
        self.white_mode_var.set(bool(state.get("white_mode", False)))
        self.settings_topmost_var.set(bool(state.get("settings_topmost", False)))
        self.auto_paste_input_var.set(bool(state.get("auto_paste_input", False)))
        self.auto_paste_description_var.set(bool(state.get("auto_paste_description", False)))
        self.auto_copy_after_convert_var.set(bool(state.get("auto_copy_after_convert", False)))
        self.custom_theme_var.set(bool(state.get("custom_theme", False)))
        if self.dark_mode_var.get():
            self.white_mode_var.set(False)
            self.custom_theme_var.set(False)
        elif self.custom_theme_var.get():
            self.dark_mode_var.set(False)
            self.white_mode_var.set(False)
        elif self.white_mode_var.get():
            self.dark_mode_var.set(False)
            self.custom_theme_var.set(False)
        self.theme_color_overrides = {}
        tc = state.get("theme_colors", {})
        if isinstance(tc, dict):
            for k, v in tc.items():
                if k in self._theme_color_keys:
                    nv = self._normalize_hex_color(v)
                    if nv:
                        self.theme_color_overrides[k] = nv
        self.preview_color_overrides = {}
        pc = state.get("preview_colors", {})
        if isinstance(pc, dict):
            for k, v in pc.items():
                if k in self._preview_color_keys:
                    nv = self._normalize_hex_color(v)
                    if nv:
                        self.preview_color_overrides[k] = nv
        self.borderless_var.set(False)
        old_weapon_all = bool(state.get("show_main_battery", True)) and bool(state.get("show_secondary", True)) and bool(state.get("show_torpedo", True)) and bool(state.get("show_bomber", True)) and bool(state.get("show_airstrike", True))
        self.show_head_var.set(bool(state.get("show_head", True)))
        self.show_description_var.set(bool(state.get("show_description", True)))
        self.show_traits_var.set(bool(state.get("show_traits", True)))
        self.show_weapons_var.set(bool(state.get("show_weapons", old_weapon_all)))
        self.show_stats_var.set(bool(state.get("show_stats", True)))
        self.show_aa_var.set(bool(state.get("show_aa", True)))
        self.show_mods_var.set(bool(state.get("show_mods", True)))
        self.show_consumables_var.set(bool(state.get("show_consumables", True)))
        self.show_all_sections_var.set(bool(state.get("show_all_sections", all([
            self.show_head_var.get(),
            self.show_description_var.get(),
            self.show_traits_var.get(),
            self.show_weapons_var.get(),
            self.show_stats_var.get(),
            self.show_aa_var.get(),
            self.show_mods_var.get(),
            self.show_consumables_var.get(),
        ]))))
        try:
            n = int(state.get("heading_equals", self.heading_equals_var.get()))
        except Exception:
            n = 4
        self.heading_equals_var.set(max(2, min(6, n)))
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", state.get("description_text", ""))
        self._pending_sashes = state.get("pane_sashes")
        self._pending_main_sashes = state.get("main_pane_sashes")
        self._pending_db_sashes = state.get("db_pane_sashes")
        self._pending_db_right_sashes = state.get("db_right_pane_sashes")
        try:
            fs = int(state.get("db_focus_font_size", self.db_focus_font_size_var.get()))
            fs = max(8, min(32, fs))
            self.db_focus_font_size_var.set(fs)
            self.db_focus_text.configure(font=("Malgun Gothic", fs))
        except Exception:
            pass

        tab_idx = state.get("preview_tab")
        if isinstance(tab_idx, int):
            try:
                self.preview_tabs.select(tab_idx)
            except Exception:
                pass

        # preload DB viewer
        try:
            data = load_json(self._resolve_db_path_for_read())
            self.db_text.delete("1.0", tk.END)
            self.db_text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
            self.refresh_db_categories(data)
        except Exception:
            pass
        self._apply_theme()
        self._apply_window_chrome()

    def apply_pending_ui_state(self):
        self.update_idletasks()
        self._apply_saved_sashes_once()
        # Re-apply after layout stabilizes; prevents "Selected Entry eats body" on startup.
        self.after(250, self._apply_saved_sashes_once)
        self.after(600, self._apply_saved_sashes_once)
        self.schedule_convert()

    def _apply_saved_sashes_once(self):
        try:
            if isinstance(self._pending_sashes, list):
                for i, pos in enumerate(self._pending_sashes):
                    if isinstance(pos, int):
                        self.panes.sashpos(i, pos)
            if isinstance(self._pending_main_sashes, list):
                for i, pos in enumerate(self._pending_main_sashes):
                    if isinstance(pos, int):
                        self.main_vpanes.sashpos(i, pos)
            if isinstance(self._pending_db_sashes, list):
                for i, pos in enumerate(self._pending_db_sashes):
                    if isinstance(pos, int):
                        self.db_panes.sashpos(i, pos)
            if isinstance(self._pending_db_right_sashes, list):
                for i, pos in enumerate(self._pending_db_right_sashes):
                    if isinstance(pos, int):
                        self.db_right_panes.sashpos(i, pos)
        except Exception:
            pass

    def _schedule_save_ui_state(self, _event=None):
        if self._closing:
            return
        if self._save_ui_after_id:
            try:
                self.after_cancel(self._save_ui_after_id)
            except Exception:
                pass
        self._save_ui_after_id = self.after(200, self._save_ui_state_debounced)

    def _save_ui_state_debounced(self):
        self._save_ui_after_id = None
        self.save_ui_state()

    def save_ui_state(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        sashes = []
        main_sashes = []
        db_sashes = []
        db_right_sashes = []
        try:
            sash_count = max(0, len(self.panes.panes()) - 1)
            sashes = [self.panes.sashpos(i) for i in range(sash_count)]
        except Exception:
            pass
        try:
            sash_count = max(0, len(self.main_vpanes.panes()) - 1)
            main_sashes = [self.main_vpanes.sashpos(i) for i in range(sash_count)]
        except Exception:
            pass
        try:
            sash_count = max(0, len(self.db_panes.panes()) - 1)
            db_sashes = [self.db_panes.sashpos(i) for i in range(sash_count)]
        except Exception:
            pass
        try:
            sash_count = max(0, len(self.db_right_panes.panes()) - 1)
            db_right_sashes = [self.db_right_panes.sashpos(i) for i in range(sash_count)]
        except Exception:
            pass

        tab_idx = 0
        try:
            tab_idx = self.preview_tabs.index(self.preview_tabs.select())
        except Exception:
            pass

        state = {
            "geometry": self.geometry(),
            "db_path": self.db_path_var.get().strip(),
            "template_dir": self.template_dir_var.get().strip(),
            "ship_name_ko": self.ship_name_ko_var.get().strip(),
            "redirect_target": self.redirect_target_var.get().strip(),
            "dark_mode": bool(self.dark_mode_var.get()),
            "white_mode": bool(self.white_mode_var.get()),
            "settings_topmost": bool(self.settings_topmost_var.get()),
            "auto_paste_input": bool(self.auto_paste_input_var.get()),
            "auto_paste_description": bool(self.auto_paste_description_var.get()),
            "auto_copy_after_convert": bool(self.auto_copy_after_convert_var.get()),
            "custom_theme": bool(self.custom_theme_var.get()),
            "theme_colors": {k: v for k, v in (self.theme_color_overrides or {}).items() if self._normalize_hex_color(v)},
            "preview_colors": {k: v for k, v in (self.preview_color_overrides or {}).items() if self._normalize_hex_color(v)},
            "borderless": bool(self.borderless_var.get()),
            "heading_equals": int(self.heading_equals_var.get()),
            "show_all_sections": bool(self.show_all_sections_var.get()),
            "show_head": bool(self.show_head_var.get()),
            "show_description": bool(self.show_description_var.get()),
            "show_traits": bool(self.show_traits_var.get()),
            "show_weapons": bool(self.show_weapons_var.get()),
            "show_stats": bool(self.show_stats_var.get()),
            "show_aa": bool(self.show_aa_var.get()),
            "show_mods": bool(self.show_mods_var.get()),
            "show_consumables": bool(self.show_consumables_var.get()),
            "description_text": self.description_text.get("1.0", tk.END).strip(),
            "pane_sashes": sashes,
            "main_pane_sashes": main_sashes,
            "db_pane_sashes": db_sashes,
            "db_right_pane_sashes": db_right_sashes,
            "preview_tab": tab_idx,
            "db_focus_font_size": int(self.db_focus_font_size_var.get()),
        }
        try:
            save_json(UI_STATE_PATH, state)
        except Exception:
            pass

    def on_close(self):
        self._closing = True
        for aid_name in ("_convert_after_id", "_save_ui_after_id", "_focus_apply_after_id"):
            aid = getattr(self, aid_name, None)
            if aid:
                try:
                    self.after_cancel(aid)
                except Exception:
                    pass
                setattr(self, aid_name, None)
        try:
            self.save_ui_state()
        except Exception:
            pass
        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
