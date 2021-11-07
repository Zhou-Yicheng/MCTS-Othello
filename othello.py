import numpy as np
import random
import time
import timeout_decorator

COLOR_BLACK = -1
COLOR_WHITE = 1
COLOR_NONE = 0


class AI:

    def __init__(self, chessboard_size, color, time_out):
        self.chessboard_size = chessboard_size
        self.color = color
        self.time_out = time_out
        self.candidate_list = []
        self.actions = {}
        self.root = None

    # * Entry
    def go(self, chessboard):
        deadline = time.time() + self.time_out
        n = self.chessboard_size
        board = np.zeros((n+2, n+2), int)
        for i in range(n):
            for j in range(n):
                board[i+1][j+1] = chessboard[i][j]
        self.run(board, deadline)

    def run(self, board, deadline):
        self.candidate_list.clear()
        try:
            mcts(self, board, self.color, deadline)
        except timeout_decorator.timeout_decorator.TimeoutError:
            self.candidate_list = sorted(self.actions.keys(), key=lambda k: UCT(self.actions[k], C=0))
            print(self.root.n)

    def get_candidates(self, board, color) -> list:
        n = self.chessboard_size
        candidates = []
        for i in range(n):
            for j in range(n):
                if board[i+1][j+1] == COLOR_NONE:
                    if self.check(board, color, i+1, j+1):
                        candidates.append((i+1, j+1))
        return candidates

    def check(self, board, color, x, y) -> bool:
        if AI.move(board, color, x, y, -1, 0) > 0:
            return True
        if AI.move(board, color, x, y, 1, 0) > 0:
            return True
        if AI.move(board, color, x, y, 0, -1) > 0:
            return True
        if AI.move(board, color, x, y, 0, 1) > 0:
            return True
        if AI.move(board, color, x, y, -1, -1) > 0:
            return True
        if AI.move(board, color, x, y, 1, 1) > 0:
            return True
        if AI.move(board, color, x, y, -1, 1) > 0:
            return True
        if AI.move(board, color, x, y, 1, 1) > 0:
            return True
        return False
        # sum = 0
        # sum += AI.move(board, color, x, y, -1, 0)
        # sum += AI.move(board, color, x, y, 1, 0)
        # sum += AI.move(board, color, x, y, 0, -1)
        # sum += AI.move(board, color, x, y, 0, 1)
        # sum += AI.move(board, color, x, y, -1, -1)
        # sum += AI.move(board, color, x, y, 1, 1)
        # sum += AI.move(board, color, x, y, -1, 1)
        # sum += AI.move(board, color, x, y, 1, -1)
        # return sum

    def move(board, color, x, y, i, j) -> int:
        res = 0
        while (board[x+i][y+j] == -color):
            res += 1
            x += i
            y += j
        return res if board[x+i][y+j] == color else 0

    def flip(board, color, x, y):
        board[x][y] = color
        AI.flop(board, color, x, y, -1, 0)
        AI.flop(board, color, x, y, 1, 0)
        AI.flop(board, color, x, y, 0, -1)
        AI.flop(board, color, x, y, 0, 1)
        AI.flop(board, color, x, y, -1, -1)
        AI.flop(board, color, x, y, +1, +1)
        AI.flop(board, color, x, y, -1, 1)
        AI.flop(board, color, x, y, 1, -1)

    def flop(board, color, x, y, i, j):
        tmp = []
        while (board[x+i][y+j] == -color):
            x += i
            y += j
            tmp.append((x, y))
        if (board[x+i][y+j] == color):
            for (x, y) in tmp:
                board[x][y] = color

    def is_win(board, color):
        my_score = 0
        yours = 0
        for i in range(8):
            for j in range(8):
                if board[i+1][j+1] == color:
                    my_score += 1
                elif board[i+1][j+1] == -color:
                    yours += 1
        if my_score < yours:
            return 1
        elif my_score > yours:
            return -1
        else:
            return 0


class Node:

    def __init__(self, board, color, mom):
        self.board = board
        self.color = color
        self.mom = mom
        self.kids = []
        self.n = 0
        self.w = 0


def UCT(node, C=1.4) -> int:
    return node.w / node.n + C * np.sqrt(np.log(node.mom.n) / node.n)


@timeout_decorator.timeout(4.7)
def mcts(game: AI, board, color, deadline):
    # define fun in fun, which is not fun
    def best_kid(mom) -> Node:
        return max(mom.kids, key=UCT)

    def select(root) -> Node:
        leaf = best_kid(root)
        while leaf.kids:
            leaf = best_kid(leaf)
        return leaf

    def expand(node: Node) -> Node:
        candidates = game.get_candidates(node.board, node.color)
        if not candidates:
            node.kids.append(Node(node.board.copy(), -node.color, node))

        for (x, y) in candidates:
            copy = node.board.copy()
            AI.flip(copy, node.color, x, y)
            kid = Node(copy, -node.color, node)
            node.kids.append(kid)

    def simulate(node: Node) -> int:
        return playout(node)

    def playout(node: Node) -> int:
        board = node.board.copy()
        color = node.color
        candidates = game.get_candidates(board, color)
        while candidates:
            while candidates:
                x, y = random.choice(candidates)
                AI.flip(board, color, x, y)
                color = -color
                candidates = game.get_candidates(board, color)
            color = -color
            candidates = game.get_candidates(board, color)
        return AI.is_win(board, node.mom.color)

    def backup(node, utility):
        while node:
            node.n += 1
            node.w += utility
            utility = -utility
            node = node.mom

    root = Node(board, color, None)
    candidates = game.get_candidates(board, color)
    if not candidates:
        return None
    game.root = root
    game.actions = {}
    for (x, y) in candidates:
        copy = board.copy()
        AI.flip(copy, color, x, y)
        kid = Node(copy, -color, root)
        root.kids.append(kid)
        game.actions[(x-1, y-1)] = kid
        game.candidate_list.append((x-1, y-1))
    for kid in root.kids:
        utiy = simulate(kid)
        backup(kid, utiy)

    while True:
        leaf = select(root)
        expand(leaf)
        for node in leaf.kids:
            utiy = simulate(node)
            backup(node, utiy)

    # for (k, v) in actions.items():
    #     print(k)
    #     print(UCT(v, C=0))


if __name__ == '__main__':
    ai = AI(8, -1, 0)
    board = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, -1, 1, 0, 0, 0],
        [0, 0, 0, 1, -1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ])
    start = time.time()
    ai.go(board)
    print(ai.candidate_list)
    print(time.time()-start)
