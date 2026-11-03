import itertools
import json
from http.server import BaseHTTPRequestHandler
import numpy as np

def find_absolute_best_combination(history_100, total_balls=45, pick_count=6):
    """
    history_100: Mảng 100 kỳ quay gần nhất (kỳ mới nhất ở index 0)
    total_balls: 45 (Mega 6/45) hoặc 55 (Power 6/55)
    """
    history = np.array(history_100[:100])
    m_draws = len(history)

    # 1. Chuyển đổi ma trận nhị phân (100 x total_balls)
    binary_matrix = np.zeros((m_draws, total_balls), dtype=int)
    for i, draw in enumerate(history):
        valid = [n - 1 for n in draw if 1 <= n <= total_balls]
        binary_matrix[i, valid] = 1

    # 2. Tính khoảng cách kỳ vắng mặt (Gaps) & Z-score chuẩn xác
    gaps = np.zeros(total_balls, dtype=float)
    for idx in range(total_balls):
        pos = np.where(binary_matrix[:, idx] == 1)[0]
        gaps[idx] = pos[0] if len(pos) > 0 else m_draws

    mean_gap = np.mean(gaps)
    std_gap = np.std(gaps) if np.std(gaps) > 0 else 1.0
    z_scores = (gaps - mean_gap) / std_gap

    # 3. Tính ma trận đồng xuất hiện chuẩn C = X^T * X
    co_matrix = np.dot(binary_matrix.T, binary_matrix)
    np.fill_diagonal(co_matrix, 0)

    # 4. Thu hẹp không gian tìm kiếm: Chọn top 14 hạt nhân có Z-score cao nhất
    top_pool = np.argsort(z_scores)[::-1][:14]

    target_sum_min = 115 if total_balls == 45 else 140
    target_sum_max = 145 if total_balls == 45 else 180

    best_combo = None
    best_score = -float('inf')

    # 5. Duyệt toàn bộ không gian tổ hợp C(14, 6) = 3,003 cách (xử lý dưới 5ms)
    for combo_indices in itertools.combinations(top_pool, pick_count):
        actual_nums = [idx + 1 for idx in combo_indices]
        total_sum = sum(actual_nums)

        # Kiểm tra điều kiện tổng
        if not (target_sum_min <= total_sum <= target_sum_max):
            continue

        # Kiểm tra điều kiện chẵn/lẻ
        even_cnt = sum(1 for n in actual_nums if n % 2 == 0)
        if even_cnt not in (2, 3, 4):
            continue

        # Tính điểm hàm mục tiêu
        z_component = sum(z_scores[i] for i in combo_indices)
        pair_component = sum(
            co_matrix[i, j] 
            for i, j in itertools.combinations(combo_indices, 2)
        )
        total_score = z_component * 1.0 + pair_component * 0.5

        if total_score > best_score:
            best_score = total_score
            best_combo = sorted(actual_nums)

    if best_combo is None:
        best_combo = sorted([idx + 1 for idx in top_pool[:pick_count]])

    return {
        "best_numbers": best_combo,
        "score": round(best_score, 3),
        "sum": sum(best_combo),
        "even_odd": f"{sum(1 for n in best_combo if n % 2 == 0)}:{sum(1 for n in best_combo if n % 2 != 0)}"
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length).decode('utf-8'))
        
        history = body.get('history', [])
        game_type = body.get('type', 'mega')
        total_balls = 55 if game_type == 'power' else 45

        result = find_absolute_best_combination(history, total_balls=total_balls)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, "data": result}).encode('utf-8'))