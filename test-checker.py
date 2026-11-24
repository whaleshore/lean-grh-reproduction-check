"""
验检查器：造几段已知答案的 Lean 代码，看 check-sorry.py 的正则抓不抓得到。

为什么必须做：如果检查器本身漏检，「0 个 sorry」这个结果就是假的。
2026-11-24 立。
"""
import re
import sys

# 与 check-sorry.py 一模一样的三条正则
SORRY_RE = re.compile(r"(?<![A-Za-z_])sorry(?![A-Za-z_])")
ADMIT_RE = re.compile(r"(?<![A-Za-z_])admit(?![A-Za-z_])")
AXIOM_RE = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?axiom\s+([A-Za-z0-9_'.]+)", re.MULTILINE)


def strip_comments(line):
    i = line.find("--")
    if i >= 0:
        line = line[:i]
    return line


CASES = [
    # (名字, 代码, 期望 sorry 命中数, 期望 axiom 命中数)
    ("裸 sorry", "theorem foo : 1 = 2 := by sorry", 1, 0),
    ("在表达式里", "def x := (sorry : Nat)", 1, 0),
    ("by 之后", "theorem bar : P := by\n  sorry", 1, 0),
    ("行尾注释里", "theorem baz : P := by trivial -- sorry", 0, 0),
    ("变量名含 sorry", "def sorryFree : Nat := 1", 0, 0),
    ("名字带下划线", "def my_sorry_thing : Nat := 1", 0, 0),
    ("sorryAx", "def foo := sorryAx Nat", 0, 0),
    ("axiom 裸声明", "axiom myAssumption : RiemannHypothesis", 0, 1),
    ("带属性的 axiom", "@[simp] axiom foo : P", 0, 1),
    ("admit", "theorem x : P := by admit", 0, 0),
    ("多个 sorry", "theorem a : P := by sorry\ntheorem b : Q := by sorry", 2, 0),
]


def main():
    print(f"测试 {len(CASES)} 个用例\n")
    fail = 0
    for name, code, want_sorry, want_axiom in CASES:
        lines = code.split("\n")
        text = code

        got_sorry = 0
        for line in lines:
            if SORRY_RE.search(strip_comments(line)):
                got_sorry += 1

        got_axiom = len(AXIOM_RE.findall(text))
        got_admit = sum(1 for line in lines if ADMIT_RE.search(strip_comments(line)))

        ok = got_sorry == want_sorry and got_axiom == want_axiom
        mark = "过" if ok else "不过"
        if not ok:
            fail += 1
        print(f"[{mark}] {name}")
        print(f"      代码: {code.replace(chr(10), ' / ')}")
        print(f"      sorry 期望 {want_sorry} 实际 {got_sorry}   axiom 期望 {want_axiom} 实际 {got_axiom}")
        if "admit" in name:
            print(f"      admit 实际 {got_admit}（期望 1，但 check-sorry.py 只计数不判定）")
        print()

    print(f"{'='*50}")
    print(f"{len(CASES) - fail} 过 / {fail} 不过")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
