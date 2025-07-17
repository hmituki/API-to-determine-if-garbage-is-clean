document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    var formData = new FormData();
    var imageInput = document.getElementById('imageInput');
    formData.append('image', imageInput.files[0]);
    
    fetch('/detect', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('status').textContent = 'Status: ' + data.status;
        document.getElementById('resultImage').src = data.result_image;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
