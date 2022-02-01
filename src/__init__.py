import string


# defines board size
BOARD_SIZE = 10

# define ship sizes
SHIP_LENS = [5, 4, 3, 3, 2]

# rows are A,B,C...
COLS = [x.upper() for x in string.ascii_lowercase[:BOARD_SIZE]]
# cols are 1,2,3...
ROWS = list(range(1, BOARD_SIZE+1))
