
def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
