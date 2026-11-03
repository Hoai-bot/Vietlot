import json
import os
import urllib.request

DATA_DIR = "data"
MAX_DRAWS = 100

# Endpoint tổng hợp giả định trả về kết quả xổ số chuẩn JSON
# Cổng proxy API tổng hợp hỗ trợ đồng thời cả 3 loại hình
API_ENDPOINTS = {
    "mega": "https://api-lottery-proxy.example/v1/vietlott/mega645/latest?limit=100",
    "power": "https://api-lottery-proxy.example/v1/vietlott/power655/latest?limit=100",
    "keno": "https://api-lottery-proxy.example/v1/vietlott/keno/latest?limit=100"
}

HEADERS = {
    "User-Agent": "Vietlott-Predictor-Bot/1.0",
    "Accept": "application/json"
}

def fetch_gateway(url):
    """Gọi API cổng tổng hợp và lấy dữ liệu JSON"""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"Lỗi kết nối cổng API: {e}")
        return None

def process_game(game_key, filename, game_name):
    url = API_ENDPOINTS[game_key]
    payload = fetch_gateway(url)
    if not payload or "data" not in payload:
        print(f"Không thể lấy dữ liệu cho {game_name}")
        return

    raw_draws = payload["data"]  # Danh sách các kỳ quay từ API
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)

    processed_draws = []
    for i, item in enumerate(raw_draws[:MAX_DRAWS]):
        jackpot = item.get("jackpot_amount", 0)
        # Tính mức tăng trưởng so với kỳ trước
        prev_jp = raw_draws[i + 1].get("jackpot_amount", jackpot) if i + 1 < len(raw_draws) else jackpot
        growth = max(0, jackpot - prev_jp)

        processed_draws.append({
            "draw_id": str(item.get("id")),
            "date": item.get("date"),
            "jackpot": jackpot,
            "growth": growth,
            "numbers": sorted(item.get("numbers", []))
        })

    curr_jp = processed_draws[0]["jackpot"] if processed_draws else 0
    recent_growth = processed_draws[0]["growth"] if processed_draws else 0
    status = "EXPLOSIVE" if curr_jp >= 50_000_000_000 else ("HOT" if curr_jp >= 30_000_000_000 else "NORMAL")

    output_data = {
        "game": game_name,
        "last_updated": processed_draws[0]["date"] if processed_draws else "",
        "summary": {
            "current_jackpot": curr_jp,
            "display": f"{curr_jp / 1e9:.1f} tỷ VNĐ",
            "recent_growth": f"+{recent_growth / 1e9:.1f} tỷ VNĐ" if recent_growth > 0 else "0 VNĐ",
            "status": status
        },
        "draws": processed_draws
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"-> Đã đồng bộ thành công: {filename} ({output_data['summary']['display']})")

def main():
    process_game("mega", "mega.json", "Mega 6/45")
    process_game("power", "power.json", "Power 6/55")
    process_game("keno", "keno.json", "Keno")

if __name__ == "__main__":
    main()