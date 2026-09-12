from flask import Blueprint

from controllers.image_controller import (
    home,
    predict_image
)


# ==========================================================
# BLUEPRINT
# ==========================================================

image_bp = Blueprint(
    "image_bp",
    __name__
)


# ==========================================================
# HOME
# ==========================================================

@image_bp.route(
    "/",
    methods=["GET"]
)
def home_route():
    return home()


# ==========================================================
# PREDICT IMAGE
# ==========================================================

@image_bp.route(
    "/predict",
    methods=["POST"]
)
def predict_image_route():
    return predict_image()
