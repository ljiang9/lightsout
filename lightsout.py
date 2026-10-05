#!/usr/bin/env python3
"""Lights Out 关灯游戏: 按下一格会翻转它自己和上下左右邻居, 目标是把所有灯熄灭。

- 纯标准库, 单文件实现。
- 开局由全灭状态随机按若干下打乱得到, 因此必然可解(逆操作即解法)。
- --solve 用 GF(2) 高斯消元求出一组解并自动执行。
"""
import argparse
import random
import secrets
import sys

ON, OFF = 1, 0


def new_board(size):
    return [[OFF] * size for _ in range(size)]


def toggle(board, size, r, c):
    """翻转 (r, c) 及其正交邻居。返回实际被翻转的格数。"""
    n = 0
    for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        if 0 <= rr < size and 0 <= cc < size:
            board[rr][cc] ^= 1
            n += 1
    return n


def scramble(size, steps, rng):
    """从全灭开始随机按 steps 下, 返回 (board, 打乱序列)。打乱局面必然可解。"""
    board = new_board(size)
    seq = []
    for _ in range(steps):
        r, c = rng.randrange(size), rng.randrange(size)
        toggle(board, size, r, c)
        seq.append((r, c))
    return board, seq


def is_solved(board):
    return all(cell == OFF for row in board for cell in row)


def solve_gf2(board, size):
    """在 GF(2) 上解按灯方程组。返回长度 size*size 的 0/1 列表(1=按),
    无解返回 None。打乱局面必然有解。"""
    n = size * size
    mat = []
    for r in range(size):
        for c in range(size):
            row = [0] * (n + 1)
            for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < size and 0 <= cc < size:
                    row[rr * size + cc] = 1
            row[n] = board[r][c]
            mat.append(row)
    pivots, prow = [], 0
    for col in range(n):  # Gauss-Jordan 消元
        piv = next((i for i in range(prow, n) if mat[i][col]), None)
        if piv is None:
            continue
        mat[prow], mat[piv] = mat[piv], mat[prow]
        for i in range(n):
            if i != prow and mat[i][col]:
                mat[i] = [a ^ b for a, b in zip(mat[i], mat[prow])]
        pivots.append(col)
        prow += 1
    for i in range(prow, n):  # 相容性检查
        if mat[i][n] and not any(mat[i][:n]):
            return None
    x = [0] * n
    for i, col in enumerate(pivots):
        x[col] = mat[i][n]
    return x


def apply_solution(board, size, sol):
    moves = [(i // size, i % size) for i, v in enumerate(sol) if v]
    for r, c in moves:
        toggle(board, size, r, c)
    return moves


def render(board, size):
    head = "   " + " ".join(chr(ord("A") + c) for c in range(size))
    lines = [head]
    for r in range(size):
        lines.append(f"{r + 1:>2} " + " ".join("●" if board[r][c] else "·" for c in range(size)))
    return "\n".join(lines)


def parse_coord(text, size):
    """接受 'B3' 或 '2 3'(行 列, 1 起始)。非法返回 None。"""
    t = text.strip().upper()
    if len(t) >= 2 and t[0].isalpha() and t[1:].isdigit():
        c, r = ord(t[0]) - ord("A"), int(t[1:]) - 1
        if 0 <= r < size and 0 <= c < size:
            return r, c
        return None
    parts = t.split()
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        r, c = int(parts[0]) - 1, int(parts[1]) - 1
        if 0 <= r < size and 0 <= c < size:
            return r, c
    return None


def play_interactive(size, steps, seed):
    rng = random.Random(seed) if seed is not None else random.Random(secrets.randbits(64))
    board, _ = scramble(size, steps, rng)
    moves = 0
    print(f"关灯游戏 {size}x{size} | 输入如 B3 或 '2 3' 翻转, solve 自动解, q 退出")
    while True:
        print(render(board, size))
        if is_solved(board):
            print(f"🎉 全灭了! 共用了 {moves} 步。")
            return 0
        try:
            cmd = input("> ").strip()
        except EOFError:
            print()
            return 0
        if cmd.lower() in ("q", "quit", "退出"):
            print("已退出。")
            return 0
        if cmd.lower() == "solve":
            sol = solve_gf2(board, size)
            if sol is None:
                print("此局面无解(理论上打乱局面不会发生)。")
                return 1
            mv = apply_solution(board, size, sol)
            moves += len(mv)
            print("解法:", " ".join(f"{chr(ord('A') + c)}{r + 1}" for r, c in mv) or "(已全灭)")
            continue
        pos = parse_coord(cmd, size)
        if pos is None:
            print("坐标无效, 例如 B3 或 '2 3'。")
            continue
        toggle(board, size, *pos)
        moves += 1


def cmd_solve(size, steps, seed):
    rng = random.Random(seed) if seed is not None else random.Random(secrets.randbits(64))
    board, _ = scramble(size, steps, rng)
    print("初始局面:")
    print(render(board, size))
    sol = solve_gf2(board, size)
    if sol is None:
        print("error: 此局面无解")
        return 1
    mv = apply_solution(board, size, sol)
    print("解法 (%d 步):" % len(mv), " ".join(f"{chr(ord('A') + c)}{r + 1}" for r, c in mv) or "(已全灭)")
    print(render(board, size))
    print("验证:", "全部熄灭 ✅" if is_solved(board) else "仍有亮灯 ❌")
    return 0 if is_solved(board) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="关灯游戏 Lights Out: 把所有灯按灭。")
    ap.add_argument("--size", type=int, default=5, help="棋盘边长, 默认 5")
    ap.add_argument("--steps", type=int, default=12, help="打乱步数, 默认 12")
    ap.add_argument("--seed", type=int, default=None, help="随机种子, 便于复现")
    ap.add_argument("--solve", action="store_true", help="直接求解并验证, 不进入交互")
    args = ap.parse_args(argv)
    if not 2 <= args.size <= 9:
        print("error: --size 需在 2~9 之间", file=sys.stderr)
        return 2
    if args.steps < 0:
        print("error: --steps 不能为负", file=sys.stderr)
        return 2
    if args.solve:
        return cmd_solve(args.size, args.steps, args.seed)
    if not sys.stdin.isatty():
        print("error: 交互模式需要终端; 管道场景请用 --solve", file=sys.stderr)
        return 2
    return play_interactive(args.size, args.steps, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
