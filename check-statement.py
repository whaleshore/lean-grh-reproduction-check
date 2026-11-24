"""
检查形式化的到底是哪条定理。

做法：不解析 Lean，只做三件事——
  1. 把 src/Statements.lean 的定义原样打出来（人能看）
  2. 检查 Main.lean 里用到的核心定义是不是来自 Mathlib（不在本地重定义）
  3. 检查本地有没有自己定义一个叫 RiemannHypothesis / RiemannZeta 的东西

为什么第 3 条要紧：如果本地把 RiemannHypothesis 定义成一个容易证的命题，
那「证明了 RiemannHypothesis」就没什么意义。用 Mathlib 的定义才算数。

2026-11-24 立。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "lean-full", "lean")
SRC = os.path.join(ROOT, "src")


def lp(p):
    p = os.path.abspath(p)
    return p if len(p) < 240 else "\\\\?\\" + p


def read(p):
    return open(lp(p), encoding="utf-8", errors="replace").read()


def main():
    print("=" * 60)
    print("1. src/Statements.lean 全文")
    print("=" * 60)
    st = os.path.join(SRC, "Statements.lean")
    if os.path.exists(lp(st)):
        print(read(st))
    else:
        print("  文件不存在")

    print("=" * 60)
    print("2. src/Main.lean 全文")
    print("=" * 60)
    mn = os.path.join(SRC, "Main.lean")
    if os.path.exists(lp(mn)):
        print(read(mn))
    else:
        print("  文件不存在")

    print("=" * 60)
    print("3. 本地有没有重定义 RiemannHypothesis / riemannZeta")
    print("=" * 60)
    # 只找 def / theorem / structure 级别的定义，不找引用
    bad = []
    pat = re.compile(
        r"^\s*(?:@\[[^\]]*\]\s*)?(def|theorem|abbrev|structure|class)\s+"
        r"(RiemannHypothesis|riemannZeta|RiemannZeta)\b",
        re.MULTILINE,
    )
    for dirpath, _, fns in os.walk(lp(SRC)):
        for fn in fns:
            if not fn.endswith(".lean"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                t = read(p)
            except Exception:
                continue
            for m in pat.finditer(t):
                ln = t[: m.start()].count("\n") + 1
                bad.append((m.group(1), m.group(2), p, ln))

    if not bad:
        print("  没有本地重定义。RiemannHypothesis 应该来自 Mathlib。")
    else:
        print(f"  发现 {len(bad)} 处本地定义：")
        for kind, name, p, ln in bad:
            print(f"    {kind} {name}")
            print(f"        {p.replace(lp(SRC), '')}:{ln}")

    print()
    print("=" * 60)
    print("4. Main.lean 的 import 和它依赖的核心名字")
    print("=" * 60)
    if os.path.exists(lp(mn)):
        t = read(mn)
        for line in t.split("\n"):
            if line.startswith("import"):
                print("  " + line.strip())
        print()
        for name in re.findall(r":=\s*([A-Za-z0-9_.']+)", t):
            print(f"  := {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
