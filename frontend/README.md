# frontend (waytoweb4-agent)

React + Vite frontend that talks to the FastAPI backend on `/api/*`.

## Run

```bash
# from the project root:
python -m pip install -e agent[dev]
python -m pip install -e backend[dev]

# install npm deps once
cd frontend && npm install && cd ..

# one-shot launcher starts BOTH backend (8000) and frontend (5173)
python scripts/run_demo.py
```

Then open <http://localhost:5173/>.

## Stack

- React 18 + plain JavaScript (no TypeScript)
- Vite for the dev server + `/api` proxy
- Tailwind via CDN
- Font Awesome 4.7 via CDN

## Layout

The demo workspace contains:

- **Header**: title + Kiln mode pill + Passport mode pill + Reset
- **Chat (left)**: scrollable dialog; type intent, click Send
- **Spec (top right)**: locked fields + "Lock Spec & Mint" button
- **Passport (mid right)**: id / status / tx hashes / per-mandate human gate + Engine controls
- **RedLine (bottom right)**: drawdown gauge + verdict + buttons + recent events
- **Human gate**: local camera preview, frozen mandate, explicit consent, no image upload
- **Inference evidence**: per-flow tokens, latency, 180W estimate, usage source and control timeline

## API

All `/api/*` calls go through Vite's proxy to `http://127.0.0.1:8000`.
No CORS gymnastics in the frontend.

## File map

```
frontend/
├── index.html              Tailwind CDN + Font Awesome CDN
├── package.json
├── vite.config.js          server.port=5173 + /api proxy
└── src/
    ├── main.jsx            mount <App />
    ├── App.jsx             layout + state
    ├── api.js              fetch wrapper
    ├── usePoll.js          polling hook
    ├── colors.js           status -> color map
    ├── styles.css          scrollbar + pulse animation
    └── components/
        ├── Header.jsx
        ├── ChatPanel.jsx
        ├── SpecCard.jsx
        ├── PassportCard.jsx
        ├── HumanGate.jsx
        ├── InferenceEvidencePanel.jsx
        ├── DrawdownGauge.jsx
        ├── VerdictBadge.jsx
        ├── RedLinePanel.jsx
        └── EventLog.jsx
```
