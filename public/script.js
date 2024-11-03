function toggleForms() {
    document.getElementById('login-form').style.display = 
        document.getElementById('login-form').style.display === 'none' ? 'block' : 'none';
    document.getElementById('signup-form').style.display = 
        document.getElementById('signup-form').style.display === 'none' ? 'block' : 'none';
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    if (result.success) {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('upload-section').style.display = 'block';
    } else {
        alert(result.message);
    }
});

document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('signupUsername').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;

    const response = await fetch('/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });

    const result = await response.json();
    alert(result.success ? 'Sign up successful. Please log in.' : result.error);
});

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData();
    const imageFile = document.getElementById('imageInput').files[0];
    formData.append('image', imageFile);

    document.getElementById('loadingIndicator').style.display = 'block'; // Show loading indicator

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    
    document.getElementById('loadingIndicator').style.display = 'none'; // Hide loading indicator

    // Show the message received from the server
    alert(result.message);

    // Check if the processing was successful and show the solver output
    if (result.success) {
        document.getElementById('solverOutput').innerText = result.solverOutput;
    } else {
        document.getElementById('solverOutput').innerText = 'Error: ' + result.message;
    }
});



