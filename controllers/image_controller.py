# routes/image_routes.py

import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

import uuid
import numpy as np
import tensorflow as tf

from flask import request, render_template
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps, UnidentifiedImageError


# ==========================================================
# MODEL CONFIGURATION
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "Image_classify.keras"
)


# ==========================================================
# CPU ONLY
# ==========================================================

try:
    tf.config.set_visible_devices([], "GPU")
except Exception:
    pass


# ==========================================================
# LOAD MODEL
# ==========================================================

model = load_model(
    MODEL_PATH,
    compile=False
)


# ==========================================================
# CLASS NAMES
# ==========================================================

data_cat = [
    "apple",
    "banana",
    "beetroot",
    "bell pepper",
    "cabbage",
    "capsicum",
    "carrot",
    "cauliflower",
    "chilli pepper",
    "corn",
    "cucumber",
    "eggplant",
    "garlic",
    "ginger",
    "grapes",
    "jalepeno",
    "kiwi",
    "lemon",
    "lettuce",
    "mango",
    "onion",
    "orange",
    "paprika",
    "pear",
    "peas",
    "pineapple",
    "pomegranate",
    "potato",
    "raddish",
    "soy beans",
    "spinach",
    "sweetcorn",
    "sweetpotato",
    "tomato",
    "turnip",
    "watermelon"
]


# ==========================================================
# IMAGE CONFIGURATION
# ==========================================================

img_height = 224
img_width = 224

ALLOWED_EXTS = {
    ".jpg",
    ".jpeg",
    ".png"
}

ALLOWED_FORMATS = {
    "JPEG",
    "PNG"
}

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 25_000_000
MIN_SIDE = 32

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

Image.MAX_IMAGE_PIXELS = MAX_PIXELS


# ==========================================================
# HELPERS
# ==========================================================

def _safe_extension(filename: str) -> str:

    ext = os.path.splitext(
        filename or ""
    )[1].lower()

    if (
        "\x00" in ext
        or "/" in ext
        or "\\" in ext
    ):
        return ""

    return ext


def _sniff_type(file_stream) -> str:

    head = file_stream.read(16)
    file_stream.seek(0)

    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    return ""


def _normalize(
    image: Image.Image,
    size=(224, 224)
):

    image = ImageOps.exif_transpose(image)

    if image.mode in (
        "RGBA",
        "LA",
        "P"
    ):

        background = Image.new(
            "RGB",
            image.size,
            (255, 255, 255)
        )

        image = image.convert("RGBA")

        background.paste(
            image,
            mask=image.split()[-1]
        )

        image = background

    else:
        image = image.convert("RGB")

    return image.resize(
        size,
        Image.Resampling.LANCZOS
    )


# ==========================================================
# HOME
# ==========================================================

def home():

    return render_template(
        "index.html",
        prediction=None,
        accuracy=None,
        top_k=None,
        image_url=None,
        error=None
    )


# ==========================================================
# PREDICTION
# ==========================================================

def predict_image():

    try:

        if "image" not in request.files:

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Please select an image."
            )

        uploaded_file = request.files["image"]

        if (
            not uploaded_file
            or uploaded_file.filename == ""
        ):

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Please select an image."
            )


        # --------------------------------------------------
        # EXTENSION
        # --------------------------------------------------

        ext = _safe_extension(
            uploaded_file.filename
        )

        if ext not in ALLOWED_EXTS:

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Only JPG, JPEG and PNG images are allowed."
            )


        # --------------------------------------------------
        # FILE SIZE
        # --------------------------------------------------

        uploaded_file.stream.seek(
            0,
            os.SEEK_END
        )

        file_size = uploaded_file.stream.tell()

        uploaded_file.stream.seek(0)

        if file_size == 0:

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="The uploaded file is empty."
            )

        if file_size > MAX_UPLOAD_BYTES:

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Image is too large (max 8 MB)."
            )


        # --------------------------------------------------
        # FILE TYPE
        # --------------------------------------------------

        real_type = _sniff_type(
            uploaded_file.stream
        )

        if real_type not in (
            "jpeg",
            "png"
        ):

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="File is not a valid JPG or PNG image."
            )


        # --------------------------------------------------
        # OPEN IMAGE
        # --------------------------------------------------

        try:

            probe = Image.open(
                uploaded_file.stream
            )

            probe.verify()
            probe.close()

            uploaded_file.stream.seek(0)

            image = Image.open(
                uploaded_file.stream
            )

        except (
            UnidentifiedImageError,
            Image.DecompressionBombError,
            OSError
        ):

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Could not read the image. It may be corrupted."
            )


        # --------------------------------------------------
        # FORMAT
        # --------------------------------------------------

        if image.format not in ALLOWED_FORMATS:

            image.close()

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Only JPG, JPEG and PNG images are allowed."
            )


        # --------------------------------------------------
        # DIMENSIONS
        # --------------------------------------------------

        width, height = image.size

        if (
            width < MIN_SIDE
            or height < MIN_SIDE
        ):

            image.close()

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Image is too small (min 32x32)."
            )

        if width * height > MAX_PIXELS:

            image.close()

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Image dimensions are too large."
            )


        # --------------------------------------------------
        # NORMALIZE
        # --------------------------------------------------

        image_load = _normalize(
            image,
            (img_width, img_height)
        )

        image.close()


        # --------------------------------------------------
        # SAVE IMAGE
        # --------------------------------------------------

        safe_name = (
            f"{uuid.uuid4().hex}.jpg"
        )

        image_path = os.path.join(
            UPLOAD_DIR,
            safe_name
        )

        image_load.save(
            image_path,
            format="JPEG",
            quality=90,
            optimize=True
        )


        # --------------------------------------------------
        # NUMPY ARRAY
        # --------------------------------------------------

        img_arr = np.asarray(
            image_load,
            dtype=np.float32
        )

        img_bat = np.expand_dims(
            img_arr,
            axis=0
        )


        # --------------------------------------------------
        # PREDICT
        # --------------------------------------------------

        predict = model.predict(
            img_bat,
            verbose=0
        )


        # --------------------------------------------------
        # SOFTMAX
        # --------------------------------------------------

        score = tf.nn.softmax(
            predict[0]
        ).numpy()


        # --------------------------------------------------
        # RESULT
        # --------------------------------------------------

        predicted_index = int(
            np.argmax(score)
        )

        predicted_class = data_cat[
            predicted_index
        ]

        accuracy = float(
            np.max(score) * 100
        )


        # --------------------------------------------------
        # TOP 3
        # --------------------------------------------------

        top_indices = np.argsort(
            score
        )[::-1][:3]

        top_k = [
            {
                "label": data_cat[i],
                "score": float(
                    score[i] * 100
                )
            }
            for i in top_indices
        ]


        # --------------------------------------------------
        # RESPONSE
        # --------------------------------------------------

        return render_template(
            "index.html",
            prediction=predicted_class,
            accuracy=accuracy,
            top_k=top_k,
            image_url=(
                f"/static/uploads/{safe_name}"
            ),
            error=None
        )


    except Exception:

        try:

            from flask import current_app

            current_app.logger.exception(
                "Prediction failed"
            )

        except Exception:
            pass

        return render_template(
            "index.html",
            prediction=None,
            accuracy=None,
            top_k=None,
            image_url=None,
            error="Something went wrong while processing the image."
        )