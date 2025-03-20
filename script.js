document.getElementById('imageUpload').addEventListener('change', function () {
    const file = this.files[0];
    if (file) {
        document.getElementById('uploadStatus').textContent = 'Image Uploaded';
        document.getElementById('uploadStatus').classList.add('show');
    } else {
        document.getElementById('uploadStatus').textContent = '';
        document.getElementById('uploadStatus').classList.remove('show');
    }
});

document.getElementById('processButton').addEventListener('click', function () {
    const file = document.getElementById('imageUpload').files[0];

    if (!file) {
        alert("⚠️ Please select an image!");
        return;
    }

    // Show preview in input image box
    const reader = new FileReader();
    reader.onload = function (e) {
        document.getElementById("inputImage").src = e.target.result;
    };
    reader.readAsDataURL(file);

    // Scroll to result section immediately
    document.getElementById("result").scrollIntoView({ behavior: "smooth" });

    const formData = new FormData();
    formData.append("file", file);

    // Show loader & hide output image + download button
    document.getElementById("loader").style.display = "block";
    document.getElementById("outputImage").style.display = "none";
    document.getElementById("downloadLink").style.display = "none";

    // Reset upload status
    document.getElementById('uploadStatus').textContent = '';
    document.getElementById('uploadStatus').classList.remove('show');

    fetch("https://bgremove-9dab4bc42a85.herokuapp.com/remove-bg/", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("loader").style.display = "none";
        document.getElementById("outputImage").style.display = "block";

        if (data.output_image_url) {
            document.getElementById("outputImage").src = data.output_image_url;
            document.getElementById("downloadLink").style.display = "inline-block";

            // Force Download
            document.getElementById("downloadLink").onclick = function (e) {
                e.preventDefault();
                fetch(data.output_image_url)
                    .then(response => response.blob())
                    .then(blob => {
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = "processed_image.png";
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    });
            };
        }
    });
});