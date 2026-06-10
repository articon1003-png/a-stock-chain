#!/usr/bin/env python3
"""
AI 超级机柜产业链行情数据拉取
数据源：腾讯行情 API
输出：data.json 供仪表盘使用
"""

import json
import urllib.request
import time
import os
import sys
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
DATA_PATH = os.path.join(SCRIPT_DIR, "data.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def tencent_prefix(exchange, code):
    """Convert exchange + code to Tencent API prefix format."""
    if exchange == "sh":
        return f"sh{code}"
    elif exchange == "sz":
        return f"sz{code}"
    return f"sz{code}"


def fetch_realtime(stocks):
    """Fetch real-time quotes from Tencent finance API.

    Returns dict keyed by code with: name, price, change_pct, prev_close, volume, market_cap
    """
    # Build batch query (max 50 per batch)
    codes = [tencent_prefix(s["exchange"], s["code"]) for s in stocks]
    results = {}

    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        url = f"http://qt.gtimg.cn/q={','.join(batch)}"
        try:
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=10)
            raw = resp.read().decode("gbk")
            for line in raw.strip().split(";"):
                line = line.strip()
                if not line or "=" not in line:
                    continue
                var_name, val = line.split("=", 1)
                val = val.strip('"')
                if not val or val == "pv_none_match":
                    continue
                fields = val.split("~")
                if len(fields) < 45:
                    continue
                code = fields[2]
                try:
                    price = float(fields[3]) if fields[3] else 0
                    prev_close = float(fields[4]) if fields[4] else 0
                    change_pct = float(fields[32]) if fields[32] else 0
                    volume = float(fields[36]) if fields[36] else 0  # 万手
                    market_cap_str = fields[44] if len(fields) > 44 else "0"
                    market_cap = float(market_cap_str) if market_cap_str else 0  # 亿
                except (ValueError, IndexError):
                    continue

                results[code] = {
                    "name": fields[1],
                    "price": price,
                    "change_pct": change_pct,
                    "prev_close": prev_close,
                    "volume": volume,
                    "market_cap": market_cap,  # 亿
                }
        except Exception as e:
            print(f"  [WARN] Realtime batch fetch error: {e}", file=sys.stderr)
        time.sleep(0.2)

    return results


def fetch_history(code, exchange, days=30):
    """Fetch daily K-line from Tencent (前复权).

    Returns list of [date, open, close, high, low, volume].
    """
    prefix = tencent_prefix(exchange, code)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days + 15)).strftime("%Y-%m-%d")
    url = (
        f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={prefix},day,{start_date},{end_date},{days + 15},qfq"
    )
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        stock_data = data.get("data", {}).get(prefix, {})
        klines = stock_data.get("qfqday", stock_data.get("day", []))
        # Format: [date, open, close, high, low, volume]
        return klines[-days:] if len(klines) > days else klines
    except Exception as e:
        print(f"  [WARN] History fetch error for {code}: {e}", file=sys.stderr)
        return []


def compute_group_metrics(group_stocks, realtime_data, history_cache):
    """Compute group-level metrics.

    1. Today's weighted average return
    2. Cumulative returns over 3/5/10 trading days (compounded)
    """
    # --- Today's weighted average return ---
    total_weight = 0
    weighted_return = 0
    valid_count = 0
    stock_details = []

    for s in group_stocks:
        code = s["code"]
        rt = realtime_data.get(code)
        if rt and rt["price"] > 0 and rt["market_cap"] > 0:
            w = rt["market_cap"]
            weighted_return += rt["change_pct"] * w
            total_weight += w
            valid_count += 1
            stock_details.append({
                "code": code,
                "name": s["name"],
                "price": rt["price"],
                "change_pct": rt["change_pct"],
                "market_cap": rt["market_cap"],
                "tier": s.get("product", ""),
            })

    today_return = weighted_return / total_weight if total_weight > 0 else 0

    # --- Build daily group weighted returns ---
    all_dates = set()
    stock_daily = {}
    for s in group_stocks:
        code = s["code"]
        hist = history_cache.get(code, [])
        if not hist:
            continue
        daily = {}
        for row in hist:
            if len(row) >= 3:
                date_str = row[0]
                close = float(row[2])
                daily[date_str] = close
        stock_daily[code] = daily
        all_dates.update(daily.keys())

    # Add today's close from realtime
    for s in group_stocks:
        code = s["code"]
        rt = realtime_data.get(code)
        if rt and rt["price"] > 0:
            today_str = datetime.now().strftime("%Y-%m-%d")
            if code not in stock_daily:
                stock_daily[code] = {}
            stock_daily[code][today_str] = rt["price"]
            all_dates.add(today_str)

    sorted_dates = sorted(all_dates)

    # Compute daily group return (weighted by market cap)
    daily_group_returns = []  # [(date, weighted_pct_return)]
    for idx, date in enumerate(sorted_dates):
        total_mc = 0
        total_ret = 0
        for s in group_stocks:
            code = s["code"]
            daily = stock_daily.get(code, {})
            rt = realtime_data.get(code)
            mc = rt["market_cap"] if rt and rt["market_cap"] > 0 else 0

            if date in daily and mc > 0 and idx > 0:
                prev_date = sorted_dates[idx - 1]
                prev_daily = stock_daily.get(code, {})
                if prev_date in prev_daily and prev_daily[prev_date] > 0:
                    ret = (daily[date] / prev_daily[prev_date] - 1) * 100
                    total_ret += ret * mc
                    total_mc += mc

        if total_mc > 0:
            daily_group_returns.append((date, total_ret / total_mc))

    # Compute cumulative returns (compounded): 5d, 20d
    cumulative = {}
    for n_days in [5, 20]:
        if len(daily_group_returns) >= n_days:
            compound = 1.0
            for _, ret in daily_group_returns[-n_days:]:
                compound *= (1 + ret / 100)
            cumulative[f"cum_{n_days}d"] = round((compound - 1) * 100, 2)
        else:
            cumulative[f"cum_{n_days}d"] = 0

    return {
        "today_return": round(today_return, 2),
        "cum_5d": cumulative["cum_5d"],
        "cum_20d": cumulative["cum_20d"],
        "valid_count": valid_count,
        "total_market_cap": round(total_weight, 2),
        "stocks": sorted(stock_details, key=lambda x: -x["change_pct"]),
    }


def main():
    print("=== AI 超级机柜产业链行情数据拉取 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = load_config()
    groups = config["groups"]

    # Collect all unique stocks
    all_stocks = []
    seen_codes = set()
    for g in groups:
        for s in g["stocks"]:
            if s["code"] not in seen_codes:
                all_stocks.append(s)
                seen_codes.add(s["code"])

    print(f"\n共 {len(groups)} 组，{len(all_stocks)} 只个股")

    # Fetch real-time data
    print("\n[1/2] 拉取实时行情...")
    realtime = fetch_realtime(all_stocks)
    fetched_count = len(realtime)
    print(f"  成功获取 {fetched_count}/{len(all_stocks)} 只个股实时数据")

    # Fetch historical K-lines (parallel-ish with rate limiting)
    print("\n[2/2] 拉取历史K线（30日）...")
    history_cache = {}
    for i, s in enumerate(all_stocks):
        code = s["code"]
        hist = fetch_history(code, s["exchange"], days=30)
        history_cache[code] = hist
        if (i + 1) % 10 == 0:
            print(f"  已获取 {i+1}/{len(all_stocks)}...")
        time.sleep(0.15)
    print(f"  历史K线获取完成")

    # Compute group metrics
    print("\n计算组级指标...")
    results = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "groups": [],
    }

    for g in groups:
        metrics = compute_group_metrics(g["stocks"], realtime, history_cache)
        group_result = {
            "name": g["name"],
            "desc": g["desc"],
            "color": g["color"],
            "layer": g.get("layer", "materials"),
            **metrics,
        }
        results["groups"].append(group_result)
        print(f"  {g['name']}: 今日 {metrics['today_return']:+.2f}%, 5日 {metrics['cum_5d']:+.2f}%, 20日 {metrics['cum_20d']:+.2f}%")

    # Sort groups by today_return descending
    results["groups"].sort(key=lambda x: -x["today_return"])

    # Save
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n数据已保存到 {DATA_PATH}")
    return results


if __name__ == "__main__":
    main()
