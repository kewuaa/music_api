import time


def get_time_stamp(bit: int = 10) -> int:
    """ get the time stamp.

    :param bit: bit of the time stamp, optional
    :return: time stamp
    """

    t = time.time()
    return int(t * 10 ** (bit - 10))
