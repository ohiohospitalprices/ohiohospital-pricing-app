const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Ensure homepage route is properly configured for Render deployment
// CMS Standards & Resources update deployed: 2026-04-22

app.use(cors());
app.use(express.static(path.join(__dirname, '.')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Explicit endpoint for procedures data
app.get('/procedures.json', (req, res) => {
    try {
        const proceduresPath = path.join(__dirname, 'procedures.json');
        const data = fs.readFileSync(proceduresPath, 'utf8');
        res.setHeader('Content-Type', 'application/json');
        res.send(data);
    } catch (error) {
        console.error('Error serving procedures.json:', error);
        res.status(404).json({ error: 'Procedures data not found' });
    }
});

app.listen(PORT, () => {
    console.log(`OhioHealth Pricing Server running on port ${PORT}`);
});
