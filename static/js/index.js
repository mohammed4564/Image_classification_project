document.addEventListener("DOMContentLoaded", function () {

    // ==========================================================
    // ELEMENTS
    // ==========================================================

    const uploadForm = document.getElementById("uploadForm");

    const uploadModeBtn = document.getElementById("uploadModeBtn");
    const cameraModeBtn = document.getElementById("cameraModeBtn");

    const uploadSection = document.getElementById("uploadSection");
    const cameraSection = document.getElementById("cameraSection");

    const imageInput = document.getElementById("imageInput");

    const dropzone = document.getElementById("dropzone");

    const previewBox = document.getElementById("previewBox");
    const previewImg = document.getElementById("previewImg");
    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");

    const submitBtn = document.getElementById("submitBtn");
    const resetBtn = document.getElementById("resetBtn");

    const clientError = document.getElementById("clientError");
    const clientErrorText = document.getElementById("clientErrorText");

    // Camera
    const cameraVideo = document.getElementById("cameraVideo");
    const cameraCanvas = document.getElementById("cameraCanvas");

    const captureBtn = document.getElementById("captureBtn");
    const stopCameraBtn = document.getElementById("stopCameraBtn");

    const cameraError = document.getElementById("cameraError");
    const cameraErrorText = document.getElementById("cameraErrorText");

    const capturedSection = document.getElementById("capturedSection");
    const capturedImage = document.getElementById("capturedImage");

    const retakeBtn = document.getElementById("retakeBtn");
    const usePhotoBtn = document.getElementById("usePhotoBtn");

    // Theme
    const themeToggle = document.getElementById("themeToggle");


    // ==========================================================
    // CAMERA STATE
    // ==========================================================

    let cameraStream = null;
    let capturedFile = null;


    // ==========================================================
    // SHOW / HIDE ERRORS
    // ==========================================================

    function showError(message) {
        clientErrorText.textContent = message;
        clientError.style.display = "flex";
    }

    function hideError() {
        clientError.style.display = "none";
    }

    function showCameraError(message) {
        cameraErrorText.textContent = message;
        cameraError.style.display = "flex";
    }

    function hideCameraError() {
        cameraError.style.display = "none";
    }


    // ==========================================================
    // FORMAT FILE SIZE
    // ==========================================================

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    }


    // ==========================================================
    // DISPLAY FILE PREVIEW
    // ==========================================================

    function displayFile(file) {

        if (!file) return;

        const allowedTypes = ["image/jpeg", "image/png"];

        if (!allowedTypes.includes(file.type)) {
            showError("Please select a JPG, JPEG, or PNG image.");
            imageInput.value = "";
            return;
        }

        const maxSize = 8 * 1024 * 1024;

        if (file.size > maxSize) {
            showError("Image size must be less than 8 MB.");
            imageInput.value = "";
            return;
        }

        hideError();

        const reader = new FileReader();

        reader.onload = function (event) {
            previewImg.src = event.target.result;
            previewBox.style.display = "flex";
        };

        reader.readAsDataURL(file);

        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
    }


    // ==========================================================
    // FILE INPUT
    // ==========================================================

    imageInput.addEventListener("change", function () {
        if (this.files && this.files.length > 0) {
            displayFile(this.files[0]);
        }
    });


    // ==========================================================
    // DRAG & DROP
    // ==========================================================

    dropzone.addEventListener("dragover", function (event) {
        event.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", function () {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", function (event) {

        event.preventDefault();
        dropzone.classList.remove("dragover");

        const files = event.dataTransfer.files;
        if (!files || files.length === 0) return;

        const file = files[0];

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        imageInput.files = dataTransfer.files;

        displayFile(file);
    });


    // ==========================================================
    // OPEN CAMERA
    // ==========================================================

    cameraModeBtn.addEventListener("click", async function () {

        hideError();
        hideCameraError();

        uploadSection.style.display = "none";
        cameraSection.style.display = "block";

        uploadModeBtn.classList.remove("active");
        cameraModeBtn.classList.add("active");

        try {
            await startCamera();
        } catch (error) {
            console.error("Camera error:", error);
            showCameraError(
                "Unable to access your camera. Please allow camera permission in your browser."
            );
        }
    });


    // ==========================================================
    // START CAMERA
    // ==========================================================

    async function startCamera() {

        stopCamera();
        hideCameraError();

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Camera API is not supported by this browser.");
        }

        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: "environment" },
                width:  { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        });

        cameraVideo.srcObject = cameraStream;
        await cameraVideo.play();
    }


    // ==========================================================
    // STOP CAMERA
    // ==========================================================

    function stopCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(function (track) {
                track.stop();
            });
            cameraStream = null;
        }
        cameraVideo.srcObject = null;
    }


    // ==========================================================
    // CLOSE CAMERA
    // ==========================================================

    stopCameraBtn.addEventListener("click", function () {

        stopCamera();

        cameraSection.style.display = "none";
        uploadSection.style.display = "block";

        uploadModeBtn.classList.add("active");
        cameraModeBtn.classList.remove("active");
    });


    // ==========================================================
    // CAPTURE PHOTO
    // ==========================================================

    captureBtn.addEventListener("click", function () {

        if (!cameraStream) {
            showCameraError("Camera is not active.");
            return;
        }

        const width = cameraVideo.videoWidth;
        const height = cameraVideo.videoHeight;

        if (!width || !height) {
            showCameraError("Camera is not ready yet. Please try again.");
            return;
        }

        cameraCanvas.width = width;
        cameraCanvas.height = height;

        const context = cameraCanvas.getContext("2d");
        context.drawImage(cameraVideo, 0, 0, width, height);

        const imageData = cameraCanvas.toDataURL("image/jpeg", 0.92);

        capturedImage.src = imageData;
        capturedSection.style.display = "block";

        stopCamera();
    });


    // ==========================================================
    // RETAKE PHOTO
    // ==========================================================

    retakeBtn.addEventListener("click", async function () {

        capturedSection.style.display = "none";
        capturedFile = null;

        try {
            await startCamera();
        } catch (error) {
            console.error(error);
            showCameraError("Unable to restart camera.");
        }
    });


    // ==========================================================
    // USE CAPTURED PHOTO
    // ==========================================================

    usePhotoBtn.addEventListener("click", function () {

        cameraCanvas.toBlob(function (blob) {

            if (!blob) {
                showError("Unable to create image from camera.");
                return;
            }

            capturedFile = new File(
                [blob],
                "camera-photo.jpg",
                { type: "image/jpeg" }
            );

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(capturedFile);
            imageInput.files = dataTransfer.files;

            displayFile(capturedFile);

            capturedSection.style.display = "none";
            cameraSection.style.display = "none";
            uploadSection.style.display = "block";

            uploadModeBtn.classList.add("active");
            cameraModeBtn.classList.remove("active");

            hideCameraError();

        }, "image/jpeg", 0.92);
    });


    // ==========================================================
    // UPLOAD MODE
    // ==========================================================

    uploadModeBtn.addEventListener("click", function () {

        stopCamera();

        cameraSection.style.display = "none";
        uploadSection.style.display = "block";

        uploadModeBtn.classList.add("active");
        cameraModeBtn.classList.remove("active");

        hideCameraError();
    });


    // ==========================================================
    // FORM SUBMIT
    // ==========================================================

    uploadForm.addEventListener("submit", function (event) {

        if (!imageInput.files || imageInput.files.length === 0) {
            event.preventDefault();
            showError("Please upload an image or take a photo first.");
            return;
        }

        const file = imageInput.files[0];
        const maxSize = 8 * 1024 * 1024;

        if (file.size > maxSize) {
            event.preventDefault();
            showError("Image size must be less than 8 MB.");
            return;
        }

        stopCamera();

        submitBtn.disabled = true;
        submitBtn.classList.add("loading");

        const btnText = submitBtn.querySelector(".btn-text");
        if (btnText) btnText.textContent = "Predicting...";
    });


    // ==========================================================
    // RESET
    // ==========================================================

    resetBtn.addEventListener("click", function () {

        stopCamera();

        uploadForm.reset();

        previewImg.src = "";
        previewBox.style.display = "none";

        capturedImage.src = "";
        capturedSection.style.display = "none";
        cameraSection.style.display = "none";
        uploadSection.style.display = "block";

        capturedFile = null;

        hideError();
        hideCameraError();

        uploadModeBtn.classList.add("active");
        cameraModeBtn.classList.remove("active");

        submitBtn.disabled = false;
        submitBtn.classList.remove("loading");

        const btnText = submitBtn.querySelector(".btn-text");
        if (btnText) btnText.textContent = "Predict Image";
    });


    // ==========================================================
    // THEME TOGGLE
    // ==========================================================

    if (themeToggle) {

        document.documentElement.classList.remove("dark-preload");

        const savedTheme = localStorage.getItem("theme");
        if (savedTheme === "dark") {
            document.body.classList.add("dark");
        }

        themeToggle.addEventListener("click", function () {
            document.body.classList.toggle("dark");
            localStorage.setItem(
                "theme",
                document.body.classList.contains("dark") ? "dark" : "light"
            );
        });
    }


    // ==========================================================
    // CLEANUP CAMERA ON UNLOAD
    // ==========================================================

    window.addEventListener("beforeunload", function () {
        stopCamera();
    });

});