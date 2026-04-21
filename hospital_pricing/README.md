# OhioHealth Hospital Pricing Lookup

A clean, interactive web interface for comparing hospital procedure pricing across OhioHealth facilities.

## Features

✅ **15 OhioHealth Hospitals** - Columbus, Cleveland, Dublin, Grady, Grant, Grove City, Hardin, Mansfield, Marion, O'Bleness, Pickerington, Riverside, Shelby, Southeastern, Van Wert

✅ **8 Procedure Categories** - Surgical, Imaging, Lab, Pharmacy, ER, Therapy, Room, Other

✅ **Procedure Search** - Real-time filtering by name or CPT code

✅ **Price Comparison** - Click any procedure to see pricing across all OhioHealth hospitals

✅ **Responsive Design** - Works on desktop and mobile devices

✅ **No Dependencies** - Frontend uses pure HTML/CSS/JavaScript (no React required)

## Local Development

```bash
# Install dependencies
npm install

# Start the server
npm start
```

Server runs on `http://localhost:3000`

## Deployment to Render

1. **Create a Render account** at https://render.com

2. **Connect GitHub repository** containing this code

3. **Create new Web Service:**
   - Select your repository
   - Runtime: Node
   - Build Command: `npm install`
   - Start Command: `npm start`
   - Plan: Free tier works fine

4. **Deploy:**
   - Render will automatically build and deploy
   - Your app will be live at `https://[your-service-name].onrender.com`

## Data Structure

Procedure data is in `procedures.json`:

```json
{
  "hospital": "Columbus",
  "category": "Surgical",
  "procedure": "Appendectomy",
  "cpt": "44960",
  "price": 12000
}
```

To add/update procedures, modify `procedures.json` and redeploy.

## Usage

1. **Select a Hospital** - Choose from the dropdown or view all hospitals
2. **Pick a Category** - Click category buttons to filter
3. **Search** - Type procedure name or CPT code
4. **Compare Prices** - Click any procedure to see all hospital prices

## File Structure

```
hospital_pricing/
├── index.html          # Main interface
├── procedures.json     # Procedure data
├── server.js          # Express server
├── package.json       # Dependencies
├── render.yaml        # Render deployment config
└── README.md          # This file
```

## Browser Support

Works in all modern browsers (Chrome, Firefox, Safari, Edge)

## Performance

- Loads 152K+ procedures
- Real-time search and filtering
- Smooth animations and transitions
- Mobile-optimized interface

---

Built for OhioHealth. Last updated: April 2026.
