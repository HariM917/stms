// STMS Web App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('STMS Web App initialized');
    
    // Display filename when file is selected
    const fileInput = document.getElementById('file');
    const fileLabel = document.querySelector('label[for="file"]');
    
    if (fileInput && fileLabel) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                fileLabel.textContent = this.files[0].name;
            } else {
                fileLabel.textContent = 'Choose a file';
            }
        });
    }
});
