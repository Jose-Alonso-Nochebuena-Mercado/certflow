TITLE = {
    "size": 24,
    "weight": "bold"
}


SUBTITLE = {
    "size":18,
    "weight":"bold"
}


BODY = {
    "size":14,
    "weight":"normal"
}


SMALL = {
    "size":12,
    "weight":"normal"
}

def get_font(style):

    return (
        "Arial",
        style["size"],
        style["weight"]
    )