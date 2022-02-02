import abc


class Strategy(abc.ABC):
    """
    interface that other strategies should implement
    """

    @abc.abstractmethod
    def choose_shot(self, board, opponents_sunk, name=None):
        """
        args:
            board: board of known shots
            opponents_sunk: list(int), lengths of ships that have been sunk
            name: str
        returns:
            col: str (ex: "E")
            row: int (ex: 4)
        """
        ...


class UserStrategy(Strategy):

    def choose_shot(self, board, opponents_sunk, name=None):
        square = input("{}: Enter a square to fire on (ex: E4): ".format(name))
        col, row = square
        row = int(row)
        return col, row
