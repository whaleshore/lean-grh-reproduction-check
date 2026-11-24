"""
查「伪装成证明」的三类东西：
  sorryAx         sorry 底层的公理，手工调用等于绕过
  native_decide   调编译器而不是内核验证，可以「证明」任何东西
  set_option ...  能关掉某些检查的选项

2026-11-24 立。前提：check-sorry.py 已经证明可靠（11/11 测试通过），
但那条正则故意排除了 sorryAx。这个脚本补上那个缺口。
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "lean-full", "lean", "src")

PATTERNS = {
    "sorryAx": re.compile(r"(?<![A-Za-z_])sorryAx(?![A-Za-z_])"),
    "native_decide": re.compile(r"(?<![A-Za-z_])native_decide(?![A-Za-z_])"),
    "set_option": re.compile(r"set_option\s+([A-Za-z0-9_.]+)\s+", re.MULTILINE),
    "implemented_by": re.compile(r"(?<![A-Za-z_])implemented_by(?![A-Za-z_])"),
    "extern": re.compile(r"(?<![A-Za-z_])extern(?![A-Za-z_])"),
    "opaque": re.compile(r"(?<![A-Za-z_])opaque(?![A-Za-z_])"),
    "unsafe": re.compile(r"(?<![A-Za-z_])unsafe(?![A-Za-z_])"),
}


def long_path(p):
    p = os.path.abspath(p)
    if len(p) < 240:
        return p
    if p.startswith("\\\\?\\"):
        return p
    return "\\\\?\\" + p


def main():
    t0 = time.time()
    files = []
    for dirpath, _, filenames in os.walk(long_path(ROOT)):
        for fn in filenames:
            if fn.endswith(".lean"):
                files.append(os.path.join(dirpath, fn))
    print(f"扫描 {len(files)} 个文件")

    hits = {k: [] for k in PATTERNS}
    unreadable = 0
    options_seen = {}

    for i, f in enumerate(files):
        try:
            with open(long_path(f), "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except Exception:
            unreadable += 1
            continue

        for name, rx in PATTERNS.items():
            for m in rx.finditer(text):
                if name == "set_option":
                    opt = m.group(1)
                    options_seen[opt] = options_seen.get(opt, 0) + 1
                    hits[name].append((f, opt))
                else:
                    ln = text[: m.start()].count("\n") + 1
                    hits[name].append((f, ln))

        if (i + 1) % 50000 == 0:
            print(f"  {i+1}/{len(files)}，{time.time()-t0:.0f} 秒")

    print(f"\n{'='*55}")
    print(f"文件 {len(files):,}  读不了 {unreadable}")
    for name in PATTERNS:
        if name == "set_option":
            continue
        print(f"{name:20s} {len(hits[name]):,}")

    print(f"\nset_option 一共 {len(hits['set_option']):,} 处，涉及的选项：")
    for opt, n in sorted(options_seen.items(), key=lambda x: -x[1]):
        print(f"  {n:>7,}  {opt}")

    # 落盘
    out = os.path.abspath(
        os.path.join(os.path.dirname(ROOT), "..", "results-2-sorryax-native.txt")
    )
    with open(long_path(out), "w", encoding="utf-8") as fh:
        fh.write(f"文件 {len(files):,} / 读不了 {unreadable}\n\n")
        for name, items in hits.items():
            fh.write(f"=== {name}: {len(items)} ===\n")
            for it in items[:200]:
                fh.write(f"{it}\n")
            fh.write("\n")
        fh.write("=== set_option 统计 ===\n")
        for opt, n in sorted(options_seen.items(), key=lambda x: -x[1]):
            fh.write(f"{n:>7,}  {opt}\n")
    print(f"\n完整结果 → {out}")

    # 只打印可疑的（大部分是合法的）
    for name in ["sorryAx", "native_decide"]:
        if hits[name]:
            print(f"\n--- {name} 前 10 条 ---")
            for f, ln in hits[name][:10]:
                print(f"  {f.replace(long_path(ROOT), '')[:110]}:{ln}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
