# HARV React Frontend

Modern React + TypeScript frontend for the HARV attendance verification system.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 3
- **Routing**: React Router v6
- **State**: Zustand
- **HTTP**: Axios
- **Testing**: Playwright

## Development

### Local Development (Vite Dev Server)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173 with API proxy to http://localhost:8000

### Production Build

```bash
npm run build
npm run preview
```

## Docker Production

The Dockerfile uses a multi-stage build:
1. **Build stage**: Node.js compiles React app
2. **Production stage**: NGINX serves static files and proxies `/api/*` to backend

```bash
docker build -t harv-frontend .
docker run -p 8080:80 harv-frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # App entry point
│   ├── App.tsx               # Router configuration
│   ├── api.ts                # Axios API client
│   ├── store/
│   │   └── appState.ts       # Zustand global state
│   ├── components/           # Reusable components
│   │   ├── StatusBanner.tsx
│   │   ├── GPSButton.tsx
│   │   ├── ManualCoordsForm.tsx
│   │   ├── ProfessorCalibrationForm.tsx
│   │   ├── VerifyButtons.tsx
│   │   ├── ImageVerifyCard.tsx
│   │   └── JsonViewer.tsx
│   └── pages/                # Route pages
│       ├── Landing.tsx
│       ├── Professor.tsx
│       ├── Student.tsx
│       └── Status.tsx
├── e2e/                      # Playwright tests
├── nginx.conf                # Production NGINX config
├── Dockerfile                # Multi-stage production build
└── vite.config.ts            # Vite configuration

```

## Features

### Professor Mode (`/professor`)
- Calibrate classroom location (lat/lon)
- Set acceptable radius (epsilon_m)
- View current calibration status

### Student Mode (`/student`)
- **GPS Verification**: Browser geolocation with permission handling
- **IP Verification**: Fallback IP-based location
- **Manual Coords**: Backup entry if GPS blocked
- **Image Verification**: Photo upload with challenge word

### Status Page (`/status`)
- API health check
- Geolocation provider status
- Current calibration details

## API Integration

All API calls route through `/api/*` which NGINX proxies to `http://serve:8000/`.

Endpoints used:
- `GET /healthz` - API health
- `GET /geo/status` - Geolocation config
- `POST /geo/calibrate` - Set classroom location
- `POST /geo/verify` - Verify student location
- `POST /verify` - Image verification

## Testing

### E2E Tests (Playwright)

```bash
npm run test:e2e          # Run tests
npm run test:e2e:ui       # Interactive UI mode
```

Tests cover:
- Navigation flows
- Form interactions
- GPS mocking
- API integration

## Environment Variables

Create `.env` file (optional for local dev):

```env
VITE_API_BASE=/api
VITE_CHALLENGE_WORD=orchid
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

Requires geolocation API support for GPS features.

## Migration Notes

This React frontend replaces the previous Streamlit dashboard while maintaining full feature parity:
- ✅ Professor calibration
- ✅ Student GPS verification  
- ✅ Student IP verification
- ✅ Manual coordinate entry
- ✅ Image upload with challenge
- ✅ Status monitoring

## Troubleshooting

### TypeScript Errors
All "Cannot find module" errors resolve after `npm install`.

### API Connection Issues
- Verify backend is running on port 8000
- Check NGINX proxy configuration
- Review browser console for CORS errors

### GPS Permission Denied
- Use HTTPS in production (required for geolocation)
- Check browser settings
- Fall back to IP verification
