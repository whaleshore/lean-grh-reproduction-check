"""
查 Lean 源码里的 'sorry' / 'admit' / 'axiom'。

为什么用 Python 而不是 findstr/grep：
  - Windows 的 findstr 遇到 >260 字符路径会跳过，而且不报错
  - 需要精确的词边界判断（'sorry' 可能是注释里出现）

判据（第一版）：
  sorry 出现一次就是可疑——除非在注释里
  区分：行内是否有 -- 或 /- 注释标记在它前面
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "lean-full", "lean", "src")

SORRY_RE = re.compile(r"(?<![A-Za-z_])sorry(?![A-Za-z_])")
ADMIT_RE = re.compile(r"(?<![A-Za-z_])admit(?![A-Za-z_])")
AXIOM_RE = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?axiom\s+([A-Za-z0-9_'.]+)", re.MULTILINE)


def strip_comments(line):
    """粗略去掉行内注释。不处理跨行的 /- -/。"""
    i = line.find("--")
    if i >= 0:
        line = line[:i]
    return line


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
    print(f"扫描 {len(files)} 个 .lean 文件")

    sorry_hits = []   # (file, lineno, line)
    admit_hits = []
    axiom_hits = []   # (file, lineno, name)
    total_lines = 0
    unreadable = []   # 读不了的文件——必须计数，否则「0 命中」是假的

    for i, f in enumerate(files):
        try:
            # 必须用长路径前缀，否则 >260 字符的路径读不了。
            # 2026-11-24 第一次跑漏了这一行，结果「0 个 sorry」不可信。
            with open(long_path(f), "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except Exception as e:
            unreadable.append((f, str(e)[:120]))
            continue
        total_lines += len(lines)
        text = "".join(lines)

        # axiom 是全文件级别的声明
        for m in AXIOM_RE.finditer(text):
            ln = text[: m.start()].count("\n") + 1
            axiom_hits.append((f, ln, m.group(1)))

        # sorry / admit 逐行查，去掉注释
        for ln, line in enumerate(lines, 1):
            code = strip_comments(line)
            if SORRY_RE.search(code):
                sorry_hits.append((f, ln, line.strip()[:150]))
            if ADMIT_RE.search(code):
                admit_hits.append((f, ln, line.strip()[:150]))

        if (i + 1) % 30000 == 0:
            print(f"  {i+1}/{len(files)}，{time.time()-t0:.0f} 秒")

    print(f"\n{'='*50}")
    print(f"总行数      {total_lines:,}")
    print(f"文件数      {len(files):,}")
    print(f"读不了      {len(unreadable):,}   ← 这个数不为 0，下面的「0 命中」就不可信")
    print(f"sorry 命中  {len(sorry_hits)}")
    print(f"admit 命中  {len(admit_hits)}")
    print(f"axiom 命中  {len(axiom_hits)}")
    print(f"用时        {time.time()-t0:.0f} 秒")

    if unreadable:
        print(f"\n--- 读不了的文件（最多列 10 个）---")
        for f, e in unreadable[:10]:
            print(f"  {e}")
            print(f"      {f[:120]}")

    if sorry_hits:
        print(f"\n--- sorry 前 20 条 ---")
        for f, ln, txt in sorry_hits[:20]:
            rel = f.replace(long_path(ROOT), "")[:100]
            print(f"  {rel}:{ln}")
            print(f"      {txt}")
    if admit_hits:
        print(f"\n--- admit 前 10 条 ---")
        for f, ln, txt in admit_hits[:10]:
            rel = f.replace(long_path(ROOT), "")[:100]
            print(f"  {rel}:{ln}  {txt}")
    if axiom_hits:
        print(f"\n--- axiom（全部，最多 40 条）---")
        for f, ln, name in axiom_hits[:40]:
            rel = f.replace(long_path(ROOT), "")[:100]
            print(f"  {name}")
            print(f"      {rel}:{ln}")

    # 落盘一份完整结果
    out = os.path.join(os.path.dirname(ROOT), "..", "results-1-sorry-axiom.txt")
    out = os.path.abspath(out)
    with open(long_path(out), "w", encoding="utf-8") as fh:
        fh.write(f"扫描 {len(files):,} 文件 / {total_lines:,} 行\n")
        fh.write(f"读不了 {len(unreadable):,}\n")
        fh.write(f"sorry {len(sorry_hits)} / admit {len(admit_hits)} / axiom {len(axiom_hits)}\n\n")
        if unreadable:
            fh.write("=== 读不了的文件 ===\n")
            for f, e in unreadable:
                fh.write(f"{f}\n  {e}\n")
            fh.write("\n")
        fh.write("=== sorry ===\n")
        for f, ln, txt in sorry_hits:
            fh.write(f"{f}:{ln}\n  {txt}\n")
        fh.write("\n=== admit ===\n")
        for f, ln, txt in admit_hits:
            fh.write(f"{f}:{ln}\n  {txt}\n")
        fh.write("\n=== axiom ===\n")
        for f, ln, name in axiom_hits:
            fh.write(f"{f}:{ln}  {name}\n")
    print(f"\n完整结果 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
