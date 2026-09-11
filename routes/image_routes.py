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

image_bp.route(
    "/",
    methods=["GET"]
)(home)


# ==========================================================
# PREDICT IMAGE
# ==========================================================

image_bp.route(
    "/predict",
    methods=["POST"]
)(predict_image)