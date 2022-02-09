import string
import time

# defines board size
BOARD_SIZE = 10

# define ship sizes
SHIP_LENS = {
    "carrier": 5, 
    "battleship": 4, 
    "submarine": 3,
    "destroyer": 3, 
    "patrol boat": 2
}

# rows are A,B,C...
COLS = [x.upper() for x in string.ascii_lowercase[:BOARD_SIZE]]
# cols are 1,2,3...
ROWS = list(range(BOARD_SIZE))


def benchmark(name, show=False, _active={}, _total={}):
    if show:
        grand_total = 0
        for name in list(_total.keys()):
            t = _total.pop(name)
            grand_total += t
            print(name, t)
        print()
        print("total", grand_total)
        return
    t = time.perf_counter()
    if name in _active:
        elapsed = t - _active.pop(name)
        if name in _total:
            _total[name] += elapsed
        else:
            _total[name] = elapsed
    else:
        _active[name] = t
    

