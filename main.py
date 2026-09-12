import os

# ==========================================================
# DISABLE GPU / CUDA BEFORE TENSORFLOW IS IMPORTED
# ==========================================================

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


from flask import Flask, redirect
from flask_cors import CORS

from routes.image_routes import image_bp


# ==========================================================
# CREATE FLASK APP
# ==========================================================

app = Flask(__name__)


# ==========================================================
# ENABLE CORS
# ==========================================================

CORS(app)


# ==========================================================
# REGISTER IMAGE BLUEPRINT
# ==========================================================

app.register_blueprint(
    image_bp,
    url_prefix="/api/image"
)


# ==========================================================
# ROOT ROUTE
# Redirect / to image classifier
# ==========================================================

@app.route("/")
def index():
    return redirect("/api/image/")


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000
    )
