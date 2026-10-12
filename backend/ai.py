import time

N = 15
HUMAN, AI = 1, 2
DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]
WIN = 10 ** 7
WIDTH = 10
W = [0, 1, 10, 100, 1000, 10 ** 6]


def window_score(a, h):
    if h == 0 and a > 0:
        return W[a] * 5
    if a == 0 and h > 0:
        return -W[h] * 6
    return 0


def in_board(r, c):
    return 0 <= r < N and 0 <= c < N


def find_winner(board):
    for r in range(N):
        for c in range(N):
            p = board[r * N + c]
            if not p:
                continue
            for dr, dc in DIRS:
                line = [(r, c)]
                y, x = r + dr, c + dc
                while in_board(y, x) and board[y * N + x] == p:
                    line.append((y, x))
                    y += dr
                    x += dc
                if len(line) >= 5:
                    return p, line
    return 0, None


class Game:
    def __init__(self, board):
        self.b = list(board)
        self.near = [0] * (N * N)    
        for i, v in enumerate(self.b):
            if v:
                self._bump(i // N, i % N, 1)
        self.score = self._full_eval()
        self.nodes = 0
        self.cuts = 0

    def _bump(self, r, c, d):
        for y in range(max(0, r - 2), min(N, r + 3)):
            for x in range(max(0, c - 2), min(N, c + 3)):
                self.near[y * N + x] += d

    def _full_eval(self):
        s = 0
        for dr, dc in DIRS:
            for r in range(N):
                for c in range(N):
                    if in_board(r + 4 * dr, c + 4 * dc):
                        s += self._win(r, c, dr, dc)
        return s

    def _win(self, r, c, dr, dc):
        a = h = 0
        for k in range(5):
            v = self.b[(r + k * dr) * N + c + k * dc]
            if v == AI:
                a += 1
            elif v == HUMAN:
                h += 1
        return window_score(a, h)

    def _local(self, r, c):
        s = 0
        for dr, dc in DIRS:
            for k in range(5):
                sr, sc = r - k * dr, c - k * dc
                if in_board(sr, sc) and in_board(sr + 4 * dr, sc + 4 * dc):
                    s += self._win(sr, sc, dr, dc)
        return s

    def place(self, r, c, p):
        before = self._local(r, c)
        self.b[r * N + c] = p
        self._bump(r, c, 1)
        self.score += self._local(r, c) - before

    def unplace(self, r, c):
        before = self._local(r, c)
        self.b[r * N + c] = 0
        self._bump(r, c, -1)
        self.score += self._local(r, c) - before

    def is_win(self, r, c):
        p = self.b[r * N + c]
        for dr, dc in DIRS:
            n = 1
            for s in (1, -1):
                y, x = r + dr * s, c + dc * s
                while in_board(y, x) and self.b[y * N + x] == p:
                    n += 1
                    y += dr * s
                    x += dc * s
            if n >= 5:
                return True
        return False

    def cell_score(self, r, c, p):
        s = 0
        for dr, dc in DIRS:
            n, e = 1, 0
            for sg in (1, -1):
                y, x = r + dr * sg, c + dc * sg
                while in_board(y, x) and self.b[y * N + x] == p:
                    n += 1
                    y += dr * sg
                    x += dc * sg
                if in_board(y, x) and self.b[y * N + x] == 0:
                    e += 1
            if n >= 5:
                s += 10 ** 6
            elif e:
                if n == 4:
                    s += 50000 if e == 2 else 5000
                elif n == 3:
                    s += 1000 if e == 2 else 100
                elif n == 2:
                    s += 100 if e == 2 else 10
                else:
                    s += 1
        return s

    def candidates(self):
        lst = []
        for i in range(N * N):
            if self.b[i] == 0 and self.near[i] > 0:
                r, c = divmod(i, N)
                lst.append((self.cell_score(r, c, AI) + 0.9 * self.cell_score(r, c, HUMAN), i))
        lst.sort(reverse=True)
        return [i for _, i in lst[:WIDTH]]

    def search(self, depth, alpha, beta, maxing, use_ab):
        self.nodes += 1
        if depth == 0:
            return self.score
        cs = self.candidates()
        if not cs:
            return 0
        best = -float("inf") if maxing else float("inf")
        p = AI if maxing else HUMAN
        for i in cs:
            r, c = divmod(i, N)
            self.place(r, c, p)
            if self.is_win(r, c):
                v = (1 if maxing else -1) * (WIN + depth)
            else:
                v = self.search(depth - 1, alpha, beta, not maxing, use_ab)
            self.unplace(r, c)
            if maxing:
                best = max(best, v)
                alpha = max(alpha, best)
            else:
                best = min(best, v)
                beta = min(beta, best)
            if use_ab and beta <= alpha:
                self.cuts += 1
                break
        return best

    def best_move(self, depth, use_ab=True):
        t0 = time.perf_counter()
        if not any(self.b):
            return {"move": [N // 2, N // 2], "value": 0, "nodes": 0, "cuts": 0,
                    "time_ms": 0, "root_moves": []}
        alpha, beta = -float("inf"), float("inf")
        best, best_i, root = -float("inf"), None, []
        for i in self.candidates():
            r, c = divmod(i, N)
            self.place(r, c, AI)
            if self.is_win(r, c):
                v = WIN + depth
            else:
                v = self.search(depth - 1, alpha, beta, False, use_ab)
            self.unplace(r, c)
            root.append({"move": [r, c], "value": v})
            if v > best:
                best, best_i = v, i
            alpha = max(alpha, best)
        root.sort(key=lambda m: -m["value"])
        return {"move": list(divmod(best_i, N)), "value": best, "nodes": self.nodes,
                "cuts": self.cuts, "time_ms": round((time.perf_counter() - t0) * 1000),
                "root_moves": root[:6]}
