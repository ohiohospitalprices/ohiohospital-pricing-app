"""
Hospital Pricing Database - Simple Flask App with Embedded HTML
"""

from flask import Flask, jsonify

app = Flask(__name__)

# HTML Template - Embedded directly
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hospital Pricing Search</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary-color: #2563eb;
            --primary-dark: #1e40af;
            --gray-900: #111827;
            --gray-700: #374151;
            --gray-300: #d1d5db;
            --gray-200: #e5e7eb;
            --gray-100: #f3f4f6;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, var(--gray-100) 0%, #f0f9ff 100%);
            color: var(--gray-900);
            min-height: 100vh;
        }
        
        header {
            background: white;
            border-bottom: 1px solid var(--gray-200);
            padding: 2rem 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 2rem;
            color: var(--primary-dark);
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 0.95rem;
            color: #6b7280;
        }
        
        main {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }
        
        .search-box {
            background: white;
            padding: 2rem;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--gray-700);
        }
        
        input, select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--gray-300);
            border-radius: 0.5rem;
            font-size: 1rem;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        button {
            background: var(--primary-color);
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 0.5rem;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }
        
        button:hover {
            background: var(--primary-dark);
            box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        }
        
        button:disabled {
            background: var(--gray-300);
            cursor: not-allowed;
        }
        
        .results {
            background: white;
            padding: 2rem;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .hospital-header {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            padding: 1.5rem;
            border-radius: 0.5rem;
            border-left: 4px solid var(--primary-color);
            margin-bottom: 2rem;
        }
        
        .hospital-name {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-dark);
            margin: 0.5rem 0;
        }
        
        .hospital-price {
            font-size: 2.5rem;
            font-weight: 700;
            color: #16a34a;
            margin: 1rem 0 0 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: var(--gray-100);
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid var(--gray-300);
        }
        
        td {
            padding: 1rem;
            border-bottom: 1px solid var(--gray-200);
        }
        
        tr:hover {
            background: var(--gray-100);
        }
        
        .highlight {
            background: #dbeafe;
            font-weight: 600;
        }
        
        footer {
            background: var(--gray-900);
            color: white;
            padding: 2rem 1rem;
            margin-top: 3rem;
            text-align: center;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: none;
        }
        
        .alert.show {
            display: block;
        }
        
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 1.5rem; }
            .form-group { margin-bottom: 1rem; }
            input, select, button { font-size: 16px; }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>💊 Hospital Pricing Search</h1>
            <p class="subtitle">Compare procedure costs across hospitals</p>
        </div>
    </header>
    
    <main>
        <div class="search-box">
            <h2 style="margin-bottom: 1.5rem;">Find Procedure Pricing</h2>
            <form id="searchForm">
                <div class="form-group">
                    <label for="procedure">Procedure Name</label>
                    <input type="text" id="procedure" placeholder="e.g., Knee Replacement, MRI..." required>
                </div>
                <div class="form-group">
                    <label for="hospital">Hospital</label>
                    <select id="hospital" required>
                        <option value="">-- Select Hospital --</option>
                        <option value="1">Hospital A</option>
                        <option value="2">Hospital B</option>
                        <option value="3">Hospital C</option>
                    </select>
                </div>
                <button type="submit">Search</button>
            </form>
        </div>
        
        <div id="alert" class="alert"></div>
        
        <div id="results" class="results">
            <div id="resultsContent"></div>
        </div>
    </main>
    
    <footer>
        <p>&copy; 2026 Hospital Pricing Search | <a href="#" style="color: #93c5fd;">Privacy</a> | <a href="#" style="color: #93c5fd;">Terms</a></p>
        <p style="font-size: 0.85rem; margin-top: 1rem; color: #d1d5db;">Disclaimer: Prices are for informational purposes only. Always verify with your hospital.</p>
    </footer>
    
    <script>
        document.getElementById('searchForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const procedure = document.getElementById('procedure').value;
            const hospital = document.getElementById('hospital').value;
            
            if (!procedure || !hospital) {
                showAlert('Please fill in all fields');
                return;
            }
            
            // Mock result
            const mockData = {
                '1': { name: 'Hospital A', cost: 42500 },
                '2': { name: 'Hospital B', cost: 39800 },
                '3': { name: 'Hospital C', cost: 44200 }
            };
            
            const hosp = mockData[hospital];
            document.getElementById('resultsContent').innerHTML = `
                <div class="hospital-header">
                    <div style="font-size: 0.9rem; color: #0369a1;">Procedure: <strong>${procedure}</strong></div>
                    <div class="hospital-name">${hosp.name}</div>
                    <div class="hospital-price">$${hosp.cost.toLocaleString()}</div>
                </div>
                <h3>All Hospitals (Price Comparison)</h3>
                <table style="margin-top: 1rem;">
                    <thead>
                        <tr>
                            <th>Hospital</th>
                            <th>Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="highlight">
                            <td>Hospital A</td>
                            <td>$42,500</td>
                        </tr>
                        <tr>
                            <td>Hospital B</td>
                            <td>$39,800</td>
                        </tr>
                        <tr>
                            <td>Hospital C</td>
                            <td>$44,200</td>
                        </tr>
                    </tbody>
                </table>
            `;
            document.getElementById('results').classList.add('show');
        });
        
        function showAlert(msg) {
            const alert = document.getElementById('alert');
            alert.textContent = msg;
            alert.className = 'alert show alert-error';
            setTimeout(() => alert.classList.remove('show'), 4000);
        }
    </script>
</body>
</html>"""

@app.route('/')
def home():
    """Serve the homepage"""
    return HTML_TEMPLATE

@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
