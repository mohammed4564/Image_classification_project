import os
import uuid
import imghdr
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
# LOAD MODEL
# ==========================================================

model = load_model(MODEL_PATH)


# ==========================================================
# CLASS NAMES
# ==========================================================

data_cat = [
    'apple',
    'banana',
    'beetroot',
    'bell pepper',
    'cabbage',
    'capsicum',
    'carrot',
    'cauliflower',
    'chilli pepper',
    'corn',
    'cucumber',
    'eggplant',
    'garlic',
    'ginger',
    'grapes',
    'jalepeno',
    'kiwi',
    'lemon',
    'lettuce',
    'mango',
    'onion',
    'orange',
    'paprika',
    'pear',
    'peas',
    'pineapple',
    'pomegranate',
    'potato',
    'raddish',
    'soy beans',
    'spinach',
    'sweetcorn',
    'sweetpotato',
    'tomato',
    'turnip',
    'watermelon'
]


# ==========================================================
# IMAGE SIZE
# ==========================================================

img_height = 224
img_width  = 224


# ==========================================================
# SECURITY / SAFETY CONFIG
# ==========================================================

ALLOWED_EXTS     = {".jpg", ".jpeg", ".png"}
ALLOWED_FORMATS  = {"JPEG", "PNG"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024      # 8 MB
MAX_PIXELS       = 25_000_000            # 25 MP (decompression-bomb guard)
MIN_SIDE         = 32                    # reject tiny junk

UPLOAD_DIR = os.path.join("static", "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pillow global guard — raises DecompressionBombError above this
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


# ==========================================================
# SAFETY HELPERS
# ==========================================================

def _safe_extension(filename: str) -> str:
    """Lowercase extension, or '' if it looks suspicious."""
    ext = os.path.splitext(filename or "")[1].lower()
    if "\x00" in ext or "/" in ext or "\\" in ext:
        return ""
    return ext


def _sniff_type(file_stream) -> str:
    """
    Detect the real image type from magic bytes.
    Returns 'jpeg', 'png', or '' (unknown).
    """
    head = file_stream.read(512)
    file_stream.seek(0)
    return imghdr.what(None, head) or ""


def _normalize(image: Image.Image, size=(224, 224)) -> Image.Image:
    """
    Force RGB, strip EXIF orientation, flatten alpha, resize.
    Returns a clean PIL.Image ready for the model.
    """
    # apply EXIF rotation BEFORE stripping metadata
    image = ImageOps.exif_transpose(image)

    # flatten transparency onto white
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1])
        image = background
    else:
        image = image.convert("RGB")

    return image.resize(size, Image.LANCZOS)


# ==========================================================
# HOME PAGE
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
# IMAGE PREDICTION
# ==========================================================

def predict_image():

    try:

        # --------------------------------------------------
        # 1. CHECK FILE PRESENCE
        # --------------------------------------------------

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


        if not uploaded_file or uploaded_file.filename == "":

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Please select an image."
            )


        # --------------------------------------------------
        # 2. EXTENSION WHITELIST
        # --------------------------------------------------

        ext = _safe_extension(uploaded_file.filename)

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
        # 3. SIZE CAP (before reading into memory)
        # --------------------------------------------------

        uploaded_file.stream.seek(0, os.SEEK_END)
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
        # 4. MAGIC-BYTE SNIFFING
        # --------------------------------------------------

        real_type = _sniff_type(uploaded_file.stream)

        if real_type not in ("jpeg", "png"):

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="File is not a valid JPG or PNG image."
            )


        # --------------------------------------------------
        # 5. OPEN + VERIFY (catches corrupt / truncated files)
        # --------------------------------------------------

        try:
            probe = Image.open(uploaded_file.stream)
            probe.verify()
            uploaded_file.stream.seek(0)
            image = Image.open(uploaded_file.stream)
        except (UnidentifiedImageError,
                Image.DecompressionBombError,
                OSError):
            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Could not read the image. It may be corrupted."
            )


        # --------------------------------------------------
        # 6. FORMAT WHITELIST (post-decode)
        # --------------------------------------------------

        if image.format not in ALLOWED_FORMATS:

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Only JPG, JPEG and PNG images are allowed."
            )


        # --------------------------------------------------
        # 7. DIMENSION SANITY
        # --------------------------------------------------

        w, h = image.size

        if w < MIN_SIDE or h < MIN_SIDE:

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Image is too small (min 32×32)."
            )

        if w * h > MAX_PIXELS:

            return render_template(
                "index.html",
                prediction=None,
                accuracy=None,
                top_k=None,
                image_url=None,
                error="Image dimensions are too large."
            )


        # --------------------------------------------------
        # 8. NORMALIZE (RGB, no EXIF, resized to model input)
        # --------------------------------------------------

        image_load = _normalize(image, (img_width, img_height))


        # --------------------------------------------------
        # 9. SAVE A FRESH JPEG UNDER A RANDOM NAME
        #
        # never reuse the client-supplied filename
        # .jpg only, no EXIF, no alpha, known dimensions
        # --------------------------------------------------

        safe_name  = f"{uuid.uuid4().hex}.jpg"
        image_path = os.path.join(UPLOAD_DIR, safe_name)

        image_load.save(
            image_path,
            format="JPEG",
            quality=92,
            optimize=True
        )


        # --------------------------------------------------
        # 10. IMAGE TO ARRAY
        # --------------------------------------------------

        img_arr = tf.keras.utils.img_to_array(image_load)


        # --------------------------------------------------
        # 11. ADD BATCH DIMENSION
        #
        # (224,224,3)
        #       ↓
        # (1,224,224,3)
        # --------------------------------------------------

        img_bat = tf.expand_dims(img_arr, 0)


        # --------------------------------------------------
        # 12. PREDICT
        # --------------------------------------------------

        predict = model.predict(img_bat, verbose=0)


        # --------------------------------------------------
        # 13. SOFTMAX
        # --------------------------------------------------

        score = tf.nn.softmax(predict[0])


        # --------------------------------------------------
        # 14. PREDICTED INDEX + CLASS
        # --------------------------------------------------

        predicted_index = int(np.argmax(score))
        predicted_class = data_cat[predicted_index]


        # --------------------------------------------------
        # 15. ACCURACY
        # --------------------------------------------------

        accuracy = float(np.max(score) * 100)


        # --------------------------------------------------
        # 16. TOP-K PREDICTIONS
        #
        # [
        #   {"label": "apple",  "score": 92.41},
        #   {"label": "tomato", "score":  4.83},
        #   {"label": "pear",   "score":  1.62},
        # ]
        # --------------------------------------------------

        TOP_K    = 3
        score_np = score.numpy()

        # indices sorted from highest score → lowest
        top_indices = np.argsort(score_np)[::-1][:TOP_K]

        top_k = [
            {
                "label": data_cat[i],
                "score": float(score_np[i] * 100)
            }
            for i in top_indices
        ]


        # --------------------------------------------------
        # 17. RETURN RESULT
        # --------------------------------------------------

        return render_template(
            "index.html",
            prediction=predicted_class,
            accuracy=accuracy,
            top_k=top_k,
            image_url=f"/static/uploads/{safe_name}",
            error=None
        )


    except Exception:

        # never leak internal paths / stack traces to the client
        try:
            from flask import current_app
            current_app.logger.exception("Prediction failed")
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