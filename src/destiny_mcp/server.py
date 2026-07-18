"""destiny-mcp: Bazi + Huangli calculation server.

All-in-one Chinese metaphysics MCP. `uvx destiny-mcp` to install.
纯 Python 实现，零外部依赖（除 mcp 包），八字四柱 + 黄历查询。
"""

from __future__ import annotations

import json
from datetime import date, datetime

# ── Constants ────────────────────────────────────────────────────

HEAVENLY_STEMS = list("甲乙丙丁戊己庚辛壬癸")
EARTHLY_BRANCHES = list("子丑寅卯辰巳午未申酉戌亥")
ZODIAC = list("鼠牛虎兔龙蛇马羊猴鸡狗猪")
WU_XING_STEM = list("木木火火土土金金水水")  # 甲乙木, 丙丁火, ...
WU_XING_BRANCH = list("水土木木土火火土金金土水")  # 子水, 丑土, ...
NAYIN = [
    "海中金","炉中火","大林木","路旁土","剑锋金","山头火",
    "涧下水","城头土","白蜡金","杨柳木","泉中水","屋上土",
    "霹雳火","松柏木","流年水","砂石金","山下火","平地木",
    "壁上土","金箔金","覆灯火","天河水","大驿土","钗钏金",
    "桑柘木","柘榴木","大海水","石榴木","大海水",
]

# Solar term approximate dates (month, day) for 节气月划分
SOLAR_TERMS = [
    (2, 4), (3, 6), (4, 5), (5, 6), (6, 6), (7, 7),
    (8, 8), (9, 8), (10, 8), (11, 7), (12, 7), (1, 6),
]

# Month stem starting point based on year stem
# 甲己年→丙寅, 乙庚年→戊寅, 丙辛年→庚寅, 丁壬年→壬寅, 戊癸年→甲寅
MONTH_STEM_BASE = [2, 4, 6, 8, 0]  # index in HEAVENLY_STEMS for 寅月

# Hour stem starting point based on day stem
# 甲己日→甲子, 乙庚日→丙子, 丙辛日→戊子, 丁壬日→庚子, 戊癸日→壬子
HOUR_STEM_BASE = [0, 2, 4, 6, 8]

# ── Core Calculation ─────────────────────────────────────────────

def _days_from_ref(d: date) -> int:
    """Days since 1900-01-01, which is 甲戌日 (index 10)."""
    return (d - date(1900, 1, 1)).days

def _day_pillar_index(d: date) -> int:
    """Return sexagenary index (0-59) for given date."""
    return (10 + _days_from_ref(d)) % 60

def _year_pillar_index(year: int) -> int:
    """Sexagenary index for year pillar."""
    return (year - 4) % 60

def _month_pillar_index(year_stem_idx: int, month_num: int) -> int:
    """Month pillar sexagenary index.

    month_num: 1=寅月(Feb), 2=卯月(Mar), ..., 12=丑月(Jan)
    """
    base = MONTH_STEM_BASE[year_stem_idx % 5]
    stem = (base + month_num - 1) % 10
    branch = (month_num + 1) % 12  # 寅=2, 卯=3, ...
    return _sexagenary_index(stem, branch)

def _hour_pillar_index(day_stem_idx: int, hour: int) -> int:
    """Hour pillar sexagenary index. hour is 0-23."""
    branch = ((hour + 1) // 2) % 12 if hour != 23 else 0  # 23→子(0)
    if hour == 23:
        branch = 0
    base = HOUR_STEM_BASE[day_stem_idx % 5]
    stem = (base + branch) % 10
    return _sexagenary_index(stem, branch)

def _sexagenary_index(stem: int, branch: int) -> int:
    """Convert stem (0-9) + branch (0-11) to sexagenary index (0-59)."""
    # Find the index where stem and branch match
    for i in range(60):
        if i % 10 == stem and i % 12 == branch:
            return i
    return 0

def _get_lunar_month(d: date) -> int:
    """Approximate lunar month from solar terms. 1=寅...12=丑."""
    m, day = d.month, d.day
    for i, (tm, td) in enumerate(SOLAR_TERMS):
        if (m == tm and day >= td) or (m == (tm % 12) + 1 and day < td):
            continue
        # Find the solar term we're in
        ...
    # Simplified: use solar term lookup
    for idx, (sm, sd) in enumerate(SOLAR_TERMS):
        if (m > sm) or (m == sm and day >= sd):
            continue
        return idx + 1 if idx < 11 else 12
    return 12 if m == 1 else m  # fallback

def _solar_term_month(d: date) -> int:
    """Determine which 节气 month a date falls in. Returns 1-12 (寅=1)."""
    terms = [
        (2,4,1), (3,6,2), (4,5,3), (5,6,4), (6,6,5),
        (7,7,6), (8,8,7), (9,8,8), (10,8,9), (11,7,10),
        (12,7,11), (1,6,12),
    ]
    # Find which term we're AFTER (i.e., the current term month)
    candidates = []
    for sm, sd, month_idx in terms:
        if (d.month > sm) or (d.month == sm and d.day >= sd):
            candidates.append((sm, sd, month_idx))
        else:
            # For terms in months before current, add 12 to compare
            candidates.append((sm + 12 if sm < d.month else sm, sd, month_idx))
    # Sort by effective month order
    candidates.sort(key=lambda x: (x[0], x[1]))
    # Find the latest term before or on this date
    result = 1
    for sm, sd, mi in candidates:
        eff_month = sm if sm <= 12 else sm - 12
        if (eff_month < d.month) or (eff_month == d.month and sd <= d.day):
            result = mi
    return result


def calculate_bazi(year: int, month: int, day: int, hour: int = 12) -> dict:
    """Calculate Four Pillars (八字) from birth datetime.

    Args:
        year: Birth year (Gregorian)
        month: Birth month (1-12)
        day: Birth day (1-31)
        hour: Birth hour (0-23), default noon
    """
    d = date(year, month, day)

    # Handle Lichun boundary: before Feb 4, use previous Chinese year
    # 立春前日期仍属前一年的干支
    if month < 2 or (month == 2 and day < 4):
        bazi_year = year - 1
    else:
        bazi_year = year

    # Year pillar
    y_idx = _year_pillar_index(bazi_year)
    year_stem = HEAVENLY_STEMS[y_idx % 10]
    year_branch = EARTHLY_BRANCHES[y_idx % 12]

    # Month pillar (using solar term month)
    term_month = _solar_term_month(d)
    m_idx = _month_pillar_index(y_idx % 10, term_month)
    month_stem = HEAVENLY_STEMS[m_idx % 10]
    month_branch = EARTHLY_BRANCHES[m_idx % 12]

    # Day pillar
    d_idx = _day_pillar_index(d)
    day_stem = HEAVENLY_STEMS[d_idx % 10]
    day_branch = EARTHLY_BRANCHES[d_idx % 12]

    # Hour pillar
    h_idx = _hour_pillar_index(d_idx % 10, hour)
    hour_stem = HEAVENLY_STEMS[h_idx % 10]
    hour_branch = EARTHLY_BRANCHES[h_idx % 12]

    # Nayin (音律五行) for each pillar
    nayin_y = NAYIN[y_idx // 2]  # Each nayin covers 2 sexagenary indices
    nayin_m = NAYIN[m_idx // 2]
    nayin_d = NAYIN[d_idx // 2]
    nayin_h = NAYIN[h_idx // 2]

    # Day Master 五行
    day_wx = WU_XING_STEM[d_idx % 10]

    # Zodiac
    zodiac = ZODIAC[y_idx % 12]

    return {
        "year_pillar": f"{year_stem}{year_branch}",
        "month_pillar": f"{month_stem}{month_branch}",
        "day_pillar": f"{day_stem}{day_branch}",
        "hour_pillar": f"{hour_stem}{hour_branch}",
        "day_master": f"{day_stem}（{day_wx}）",
        "zodiac": f"{zodiac}",
        "nayin": {
            "year": f"{year_stem}{year_branch} {nayin_y}",
            "month": f"{month_stem}{month_branch} {nayin_m}",
            "day": f"{day_stem}{day_branch} {nayin_d}",
            "hour": f"{hour_stem}{hour_branch} {nayin_h}",
        },
        "full_bazi": f"{year_stem}{year_branch} {month_stem}{month_branch} {day_stem}{day_branch} {hour_stem}{hour_branch}",
        "note": "⚠️ 月份按节气近似计算，精确排盘请使用 openfate-bazi MCP（含真太阳时校正）",
    }


def huangli_today() -> dict:
    """Return today's Chinese almanac (黄历) information."""
    today = date.today()
    d_idx = _day_pillar_index(today)
    stem = HEAVENLY_STEMS[d_idx % 10]
    branch = EARTHLY_BRANCHES[d_idx % 12]
    zodiac = ZODIAC[_year_pillar_index(today.year) % 12]

    return {
        "date": today.isoformat(),
        "day_pillar": f"{stem}{branch}",
        "year_zodiac": zodiac,
        "lunar_note": "⚠️ 完整黄历（农历日期、宜忌、冲煞）请使用 mingai MCP 的 almanac 工具",
    }


# ── MCP Server ────────────────────────────────────────────────────

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("destiny-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bazi_paipan",
            description="八字排盘：根据公历出生时间计算四柱（年柱、月柱、日柱、时柱）、日主、纳音五行、生肖。Calculate Four Pillars of Destiny (Bazi) from Gregorian birth datetime.",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "出生年 / Birth year", "minimum": 1900, "maximum": 2100},
                    "month": {"type": "integer", "description": "出生月 / Birth month (1-12)", "minimum": 1, "maximum": 12},
                    "day": {"type": "integer", "description": "出生日 / Birth day (1-31)", "minimum": 1, "maximum": 31},
                    "hour": {"type": "integer", "description": "出生时 / Birth hour (0-23), 默认12点", "minimum": 0, "maximum": 23, "default": 12},
                },
                "required": ["year", "month", "day"],
            },
        ),
        Tool(
            name="huangli",
            description="黄历查询：查看今日的干支、生肖等基础黄历信息。Get today's Chinese almanac info (day pillar, zodiac).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "bazi_paipan":
        result = calculate_bazi(
            year=arguments["year"],
            month=arguments["month"],
            day=arguments["day"],
            hour=arguments.get("hour", 12),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "huangli":
        result = huangli_today()
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def cli():
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    cli()
