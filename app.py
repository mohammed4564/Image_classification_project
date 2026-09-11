import tensorflow as tf  # type: ignore
from tensorflow import keras  # type: ignore
from tensorflow.keras.models import load_model  # type: ignore
import streamlit as st  # type: ignore
import numpy as np
from PIL import Image


# ---------------------------------------
# Page Title
# ---------------------------------------

st.header("Image Classification Model")


# ---------------------------------------
# Load Model
# ---------------------------------------

model = load_model(r"model\Image_classify.keras")


# ---------------------------------------
# Class Names
# ---------------------------------------

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


# ---------------------------------------
# Image Size
# ---------------------------------------

img_height = 224
img_width = 224


# ---------------------------------------
# Check Model
# ---------------------------------------

st.write("Model Input Shape:", model.input_shape)
st.write("Model Output Shape:", model.output_shape)


# ---------------------------------------
# Upload Image
# ---------------------------------------

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png"]
)


# ---------------------------------------
# Prediction
# ---------------------------------------

if uploaded_file is not None:

    # -----------------------------------
    # Open uploaded image
    # Convert RGBA / grayscale to RGB
    # -----------------------------------

    image = Image.open(uploaded_file).convert("RGB")


    # -----------------------------------
    # Display Image
    # -----------------------------------

    st.image(
        image,
        caption="Uploaded Image",
        width=300
    )


    # -----------------------------------
    # Resize Image
    # -----------------------------------

    image_load = image.resize(
        (img_width, img_height)
    )


    # -----------------------------------
    # Convert Image to Array
    # -----------------------------------

    img_arr = tf.keras.utils.img_to_array(
        image_load
    )


    # -----------------------------------
    # Add Batch Dimension
    # -----------------------------------

    img_bat = tf.expand_dims(
        img_arr,
        0
    )


    # -----------------------------------
    # Show Input Shape
    # -----------------------------------

    st.write(
        "Input Image Shape:",
        img_bat.shape
    )


    # -----------------------------------
    # Prediction
    # -----------------------------------

    predict = model.predict(img_bat)


    # -----------------------------------
    # Convert Prediction to Probability
    # -----------------------------------

    score = tf.nn.softmax(
        predict[0]
    )


    # -----------------------------------
    # Get Predicted Class
    # -----------------------------------

    predicted_index = np.argmax(score)

    predicted_class = data_cat[
        predicted_index
    ]


    # -----------------------------------
    # Get Accuracy
    # -----------------------------------

    accuracy = np.max(score) * 100


    # -----------------------------------
    # Display Result
    # -----------------------------------

    st.subheader("Prediction Result")


    st.write(
        "Veg/Fruit in image is:",
        predicted_class
    )


    st.write(
        "With accuracy of:",
        f"{accuracy:.2f}%"
    )