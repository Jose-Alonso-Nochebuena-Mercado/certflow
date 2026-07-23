from app.ui.theme.colors import (
    SURFACE,
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    BORDER,
    HEADER_ACTION_BG,
    HEADER_ACTION_BORDER,
    HEADER_ACTION_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY
)

from app.ui.theme.dimensions import (
    ICON_BUTTON_SIZE,
    ICON_BUTTON_RADIUS
)


CARD_STYLE = {

    "fg_color": SURFACE,

    "corner_radius": 15

}


PRIMARY_BUTTON = {

    "fg_color": PRIMARY,

    "hover_color": PRIMARY_LIGHT

}


SECONDARY_BUTTON = {

    "fg_color": PRIMARY_SOFT,

    "hover_color": "#DCE8F7",

    "text_color": PRIMARY,

    "border_width": 1,

    "border_color": BORDER

}


SOFT_CARD_STYLE = {

    "fg_color": SURFACE,

    "corner_radius": 20,

    "border_width": 1,

    "border_color": BORDER

}


HEADER_ACTION_GROUP = {

    "fg_color": HEADER_ACTION_BG,

    "corner_radius": 22,

    "border_width": 1,

    "border_color": HEADER_ACTION_BORDER

}


ICON_BUTTON_LIGHT = {

    "width": ICON_BUTTON_SIZE,

    "height": ICON_BUTTON_SIZE,

    "corner_radius": ICON_BUTTON_RADIUS,

    "fg_color": HEADER_ACTION_BG,

    "hover_color": HEADER_ACTION_HOVER,

    "text_color": PRIMARY,

    "border_width": 0,

    "border_color": HEADER_ACTION_BORDER

}


SOFT_BADGE_STYLE = {

    "corner_radius": 12,

    "padx": 10,

    "pady": 4

}


TITLE_STYLE = {

    "text_color": TEXT_PRIMARY,

    "font": (
        "Arial",
        28,
        "bold"
    )

}


BODY_STYLE = {

    "text_color": TEXT_SECONDARY,

    "font":(
        "Arial",
        14
    )

}