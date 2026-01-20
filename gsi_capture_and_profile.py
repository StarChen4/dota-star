#!/usr/bin/env python3
import json
import time
import os
import hashlib
from collections import defaultdict, Counter
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Tuple, Optional

HOST = "127.0.0.1"
PORT = 53000

# cfg 里 auth.token；不校验就设为 None
EXPECTED_TOKEN = None  # e.g. "CHANGE_ME_TO_A_LONG_RANDOM_TOKEN"

# 采样与输出控制
REPORT_EVERY_SECONDS = 5          # 每隔多少秒输出一次统计摘要
MAX_STORE_SECONDS = 60            # 只对最近这段时间统计“稳定性”（滑动窗口）
STORE_RAW = True                  # 是否保存原始 jsonl
OUT_DIR = "gsi_out"               # 输出目录

# 终端输出控制
PRINT_TOP_FIELDS = 30             # 每次摘要打印出现率最高的多少个字段路径
PRINT_CHANGED_FIELDS = 20         # 每次摘要打印“最近新增字段”最多多少个


def now_ms() -> int:
    return int(time.time() * 1000)


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sha1_short(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()[:10]


def flatten_paths(obj: Any, prefix: str = "", paths: Optional[List[Tuple[str, str]]] = None) -> List[Tuple[str, str]]:
    """
    将 JSON 展开为字段路径列表，并附带简单类型标签：
      - dict: 继续递归
      - list: 记为 'list'，并对前几项做抽样递归（避免爆炸）
      - scalar: str/int/float/bool/null
    返回: [(path, type_tag), ...]
    """
    if paths is None:
        paths = []

    def type_tag(x: Any) -> str:
        if x is None:
            return "null"
        if isinstance(x, bool):
            return "bool"
        if isinstance(x, int) and not isinstance(x, bool):
            return "int"
        if isinstance(x, float):
            return "float"
        if isinstance(x, str):
            return "str"
        if isinstance(x, dict):
            return "dict"
        if isinstance(x, list):
            return "list"
        return type(x).__name__

    if isinstance(obj, dict):
        # 记录当前 dict 本身也可作为一个 schema 节点（可选）
        if prefix:
            paths.append((prefix, "dict"))
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            flatten_paths(v, p, paths)

    elif isinstance(obj, list):
        paths.append((prefix, "list"))
        # 抽样递归前 3 个元素，避免 list 很大
        for i, v in enumerate(obj[:3]):
            p = f"{prefix}[*]"
            flatten_paths(v, p, paths)

    else:
        paths.append((prefix, type_tag(obj)))

    return paths


class SlidingWindowStats:
    """
    对最近 MAX_STORE_SECONDS 内的帧做稳定性统计：
      - field_presence[path] = 出现次数
      - field_types[path] = Counter(type_tag)
      - total_frames = 帧数
      - first_seen_ms[path], last_seen_ms[path]
    """
    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self.frames: List[Tuple[int, List[Tuple[str, str]]]] = []  # (t_ms, [(path,type)...])
        self.field_presence = Counter()
        self.field_types: Dict[str, Counter] = defaultdict(Counter)
        self.first_seen_ms: Dict[str, int] = {}
        self.last_seen_ms: Dict[str, int] = {}
        self.total_frames = 0

        # 用于报告“最近新增字段”
        self.known_fields = set()
        self.recent_new_fields: List[Tuple[str, int]] = []

    def add_frame(self, t_ms: int, paths: List[Tuple[str, str]]):
        # 清理过期帧
        self._evict_old(t_ms)

        # 统计本帧字段（去重，避免一个 path 因 list 抽样重复计数）
        unique = {}
        for p, ty in paths:
            if not p:
                continue
            unique[p] = ty

        self.frames.append((t_ms, list(unique.items())))
        self.total_frames += 1

        for p, ty in unique.items():
            self.field_presence[p] += 1
            self.field_types[p][ty] += 1
            if p not in self.first_seen_ms:
                self.first_seen_ms[p] = t_ms
            self.last_seen_ms[p] = t_ms

            if p not in self.known_fields:
                self.known_fields.add(p)
                self.recent_new_fields.append((p, t_ms))

    def _evict_old(self, t_ms: int):
        cutoff = t_ms - self.window_seconds * 1000
        while self.frames and self.frames[0][0] < cutoff:
            old_t, old_items = self.frames.pop(0)
            self.total_frames -= 1
            for p, ty in old_items:
                self.field_presence[p] -= 1
                if self.field_presence[p] <= 0:
                    del self.field_presence[p]
                    if p in self.field_types:
                        del self.field_types[p]
                    if p in self.first_seen_ms:
                        del self.first_seen_ms[p]
                    if p in self.last_seen_ms:
                        del self.last_seen_ms[p]

        # recent_new_fields 只保留窗口内
        self.recent_new_fields = [(p, ts) for (p, ts) in self.recent_new_fields if ts >= cutoff]

    def classify_stability(self, p: str) -> Tuple[str, float]:
        """
        稳定性分级（窗口内出现率）：
          - stable: >= 0.95
          - mostly: 0.60 ~ 0.95
          - sporadic: 0.10 ~ 0.60
          - rare: < 0.10
        """
        if self.total_frames <= 0:
            return ("unknown", 0.0)
        rate = self.field_presence.get(p, 0) / self.total_frames
        if rate >= 0.95:
            return ("stable", rate)
        if rate >= 0.60:
            return ("mostly", rate)
        if rate >= 0.10:
            return ("sporadic", rate)
        return ("rare", rate)

    def report(self) -> Dict[str, Any]:
        # 按出现率排序
        fields_sorted = sorted(self.field_presence.items(), key=lambda x: (-x[1], x[0]))
        top = fields_sorted[:PRINT_TOP_FIELDS]

        stability_buckets = defaultdict(list)
        for p, cnt in fields_sorted:
            label, rate = self.classify_stability(p)
            types = dict(self.field_types.get(p, {}))
            stability_buckets[label].append({
                "path": p,
                "presence_rate": round(rate, 4),
                "types": types,
                "first_seen_ms": self.first_seen_ms.get(p),
                "last_seen_ms": self.last_seen_ms.get(p),
            })

        # 最近新增字段（最多 PRINT_CHANGED_FIELDS）
        recent_new = sorted(self.recent_new_fields, key=lambda x: -x[1])[:PRINT_CHANGED_FIELDS]
        recent_new_simple = [{"path": p, "seen_ms": ts} for p, ts in recent_new]

        return {
            "window_seconds": self.window_seconds,
            "total_frames_in_window": self.total_frames,
            "top_fields": [
                {
                    "path": p,
                    "presence_rate": round(self.field_presence[p] / self.total_frames, 4) if self.total_frames else 0.0,
                    "types": dict(self.field_types.get(p, {})),
                }
                for p, _ in top
            ],
            "stability": stability_buckets,
            "recent_new_fields": recent_new_simple,
        }


STATS = SlidingWindowStats(MAX_STORE_SECONDS)
LAST_REPORT_MS = 0
RAW_FILE = None


class GSIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global LAST_REPORT_MS, RAW_FILE

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        t_ms = now_ms()

        # 尝试解析 JSON
        body_text = raw.decode("utf-8", errors="replace")
        try:
            data = json.loads(body_text)
        except Exception:
            data = None

        # token 校验（如果配置）
        if EXPECTED_TOKEN:
            token = None
            if isinstance(data, dict):
                token = (data.get("auth") or {}).get("token")
            if token != EXPECTED_TOKEN:
                # 仍然返回 200，避免 Dota 反复重试，但我们丢弃统计
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK\n")
                return

        # 保存原始 JSONL（推荐）
        if STORE_RAW and isinstance(data, dict):
            if RAW_FILE is None:
                safe_mkdir(os.path.join(OUT_DIR, "captures"))
                fname = f"gsi_{time.strftime('%Y%m%d_%H%M%S')}_{sha1_short(str(PORT))}.jsonl"
                RAW_FILE = open(os.path.join(OUT_DIR, "captures", fname), "a", encoding="utf-8")
            record = {"t_ms": t_ms, "headers": dict(self.headers), "body": data}
            RAW_FILE.write(json.dumps(record, ensure_ascii=False) + "\n")
            RAW_FILE.flush()

        # 更新 schema/stability 统计
        if isinstance(data, dict):
            paths = flatten_paths(data)
            STATS.add_frame(t_ms, paths)

        # 周期性输出报告（只输出摘要，不刷屏）
        if t_ms - LAST_REPORT_MS >= REPORT_EVERY_SECONDS * 1000:
            LAST_REPORT_MS = t_ms
            rep = STATS.report()
            safe_mkdir(os.path.join(OUT_DIR, "reports"))
            rep_path = os.path.join(OUT_DIR, "reports", "latest_report.json")
            with open(rep_path, "w", encoding="utf-8") as f:
                json.dump(rep, f, ensure_ascii=False, indent=2)

            print("\n" + "=" * 80)
            print(f"[GSI PROFILER] window={rep['window_seconds']}s, frames={rep['total_frames_in_window']}")
            print(f"Report written: {rep_path}")

            print("\nTop fields by presence rate:")
            for item in rep["top_fields"]:
                p = item["path"]
                r = item["presence_rate"]
                ty = item["types"]
                print(f"  {r:>6}  {p}   types={ty}")

            if rep["recent_new_fields"]:
                print("\nRecently new fields (within window):")
                for item in rep["recent_new_fields"]:
                    print(f"  {item['path']}")

        # 回复 200 OK
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK\n")

    def log_message(self, format, *args):
        return


def main():
    safe_mkdir(OUT_DIR)
    print(f"Listening on http://{HOST}:{PORT}/")
    print(f"Saving raw JSONL: {STORE_RAW} -> {os.path.join(OUT_DIR, 'captures')}")
    print(f"Reporting every {REPORT_EVERY_SECONDS}s, window={MAX_STORE_SECONDS}s")
    print("Press Ctrl+C to stop.\n")
    HTTPServer((HOST, PORT), GSIHandler).serve_forever()


if __name__ == "__main__":
    main()
