const express = require('express');
const bodyParser = require('body-parser');
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const path = require('path');
const multer = require('multer');
const fs = require('fs');
const { exec } = require('child_process'); // For running the Python script
require('dotenv').config();
const app = express();

const port = 4000;

// PostgreSQL connection
const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT
});

// Middleware
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

// Set up multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const dir = path.join(__dirname, 'imgs');
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir);
        }
        cb(null, dir);
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

const upload = multer({ storage: storage });

// Sign up route
app.post('/signup', async (req, res) => {
    const { username, email, password } = req.body;
    try {
        const hashedPassword = await bcrypt.hash(password, 10);
        await pool.query(
            'INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING *',
            [username, email, hashedPassword]
        );
        res.json({ success: true });
    } catch (err) {
        res.json({ success: false, error: err.message });
    }
});

// Login route
app.post('/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
        if (result.rows.length > 0) {
            const user = result.rows[0];
            const match = await bcrypt.compare(password, user.password);
            if (match) {
                res.json({ success: true, message: 'Login successful. You can now upload an image.' });
            } else {
                res.json({ success: false, message: 'Invalid password.' });
            }
        } else {
            res.json({ success: false, message: 'User not found.' });
        }
    } catch (err) {
        res.json({ success: false, error: err.message });
    }
});

app.post('/upload', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ success: false, message: 'No file uploaded.' });
    }

    const imagePath = req.file.path;
    const solverPath = path.join(__dirname, 'public', 'solver.py'); // Adjust the path as necessary

    // Run the Python Sudoku solver script and wait for it to finish
    exec(`python "${path.join(__dirname, 'public', 'solver.py')}" "${imagePath}"`, { timeout: 60000 * 2 }, (error, stdout, stderr) => {
        console.log(`stdout: ${stdout}`);
        console.log(`stderr: ${stderr}`);
    
        if (error) {
            console.error(`Error executing Python script: ${error.message}`);
            return res.status(500).json({ success: false, message: 'Error solving Sudoku.' });
        }
    
        res.json({
            success: true,
            message: 'Image processed successfully.',
            solverOutput: stdout.trim()
        });
    });
});






// Welcome page route
app.get('/welcome', (req, res) => {
    res.send(`
        <h1>Welcome, User! You can now upload an image.</h1>
        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" name="image" id="imageInput" accept="image/*" required>
            <button type="submit">Upload Image</button>
        </form>
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const formData = new FormData();
                const imageFile = document.getElementById('imageInput').files[0];
                formData.append('image', imageFile);

                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                alert(result.message);
                if (result.success) {
                    document.body.insertAdjacentHTML('beforeend', '<pre>' + result.solverOutput + '</pre>');
                }
            });
        </script>
    `);
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
