import os

# Disable GPU/CUDA before TensorFlow is imported anywhere
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


from flask import Flask

from routes.image_routes import image_bp


# ==========================================================
# CREATE FLASK APP
# ==========================================================

app = Flask(__name__)


# ==========================================================
# REGISTER BLUEPRINT
# ==========================================================

app.register_blueprint(
    image_bp
)


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        debug=False,
        host="0.0.0.0",
        port=port
    )