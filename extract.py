"""
解 Lean 压缩包，绕过 Windows 260 字符路径限制。

为什么要自己写：Windows 的 tar.exe 遇到超长路径会静默跳过
（报 "Archive entry has empty or unreadable filename"），
17.4 万个文件里丢了 7.4 万个。2026-11-24 踩。

Python 的 tarfile 没这个限制，能用 \\\\?\\ 前缀写超长路径。
"""
import os
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
ARCHIVE = os.path.join(ROOT, "lean.tar.gz")
DEST = os.path.join(ROOT, "lean-full")

# 先清掉上次解了一半的
# （不清 lean/ 那个，因为那是 tar.exe 的产物，留着做对比）


def long_path(p):
    """Windows 长路径前缀。必须用反斜杠，且是绝对路径。"""
    p = os.path.abspath(p)
    if len(p) < 240:
        return p
    if p.startswith("\\\\?\\"):
        return p
    return "\\\\?\\" + p


def main():
    if not os.path.exists(ARCHIVE):
        print(f"找不到 {ARCHIVE}")
        return 2

    os.makedirs(DEST, exist_ok=True)
    t0 = time.time()
    n_ok = 0
    n_err = 0
    n_dir = 0
    max_len = 0
    err_samples = []

    print(f"解到 {DEST}")
    with tarfile.open(ARCHIVE, "r:gz") as tf:
        for i, member in enumerate(tf):
            # 只解 lean/ 下面
            if not member.name.startswith("lean/"):
                continue

            target = os.path.join(DEST, member.name.replace("/", os.sep))
            max_len = max(max_len, len(target))

            try:
                if member.isdir():
                    os.makedirs(long_path(target), exist_ok=True)
                    n_dir += 1
                    continue
                if not member.isfile():
                    continue

                os.makedirs(long_path(os.path.dirname(target)), exist_ok=True)
                src = tf.extractfile(member)
                if src is None:
                    n_err += 1
                    continue
                with open(long_path(target), "wb") as out:
                    while True:
                        chunk = src.read(1 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
                n_ok += 1
            except Exception as e:
                n_err += 1
                if len(err_samples) < 5:
                    err_samples.append(f"{member.name[:80]} -> {e}")

            if n_ok % 20000 == 0 and n_ok > 0:
                print(f"  {n_ok} 个，{time.time()-t0:.0f} 秒")

    print(f"\n完成：{n_ok} 文件 / {n_dir} 目录 / {n_err} 失败，{time.time()-t0:.0f} 秒")
    print(f"最长路径 {max_len} 字符")
    for s in err_samples:
        print("  失败样例:", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
