from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai import Game, find_winner, N, HUMAN, AI

app = FastAPI(title="Gomoku AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class MoveRequest(BaseModel):
    board: List[int] = Field(..., description="225 значень: 0 - порожньо, 1 - людина, 2 - ШІ")
    depth: int = Field(3, ge=1, le=5)
    alpha_beta: bool = True


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/move")
def move(req: MoveRequest):
    if len(req.board) != N * N or any(v not in (0, HUMAN, AI) for v in req.board):
        raise HTTPException(400, "Некоректна дошка")

    who, line = find_winner(req.board)
    if who:
        return {"status": "human_won" if who == HUMAN else "ai_won", "winning_line": line}
    if all(req.board):
        return {"status": "draw"}

    game = Game(req.board)
    result = game.best_move(req.depth, req.alpha_beta)
    r, c = result["move"]
    board = list(req.board)
    board[r * N + c] = AI

    who, line = find_winner(board)
    status = "ai_won" if who == AI else "draw" if all(board) else "ongoing"
    return {"status": status, "winning_line": line, **result}
