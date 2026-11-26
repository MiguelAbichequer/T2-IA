"""Variante sem_perigo (gerada por testes_extra/experimentos.py)."""
from . import othello_eval as _E
from . import tournament_agent as _T

TIME_BUDGET = 0.5
_E.W.update({'danger': (0.0, 0.0)})


def make_move(state):
    _T.TIME_BUDGET = TIME_BUDGET
    return _T.make_move(state)
