# FasalSathi / HarvestIQ

This repository contains the complete runnable source for the FasalSathi crop-disease, market-information, weather, and speech-assistance application.

It includes the application source, TorchScript inference model files, and the Vosk speech model required for local runtime operation.

Training datasets, generated databases, frontend build output, Python caches, and `node_modules` are intentionally excluded because they can be regenerated or are not required in the source repository.

---

## Requirements

* Java JDK 17 or later
* Maven 3.9 or later
* Node.js 20 or later (includes npm)

The Maven project is configured to compile against Java 17.

---

## Run the Full Web Application

On Windows, from the repository root, run:

```bat
run-app.bat
```

This is the only user-facing launcher.

The launcher:

1. Checks Java, Maven, Node.js, and npm.
2. Installs frontend dependencies when required.
3. Builds the React frontend.
4. Starts the Spring Boot backend.
5. Waits for the backend health endpoint.
6. Opens the main application in the browser.

For the packaged/local application, use:

```text
http://localhost:8080
```

Do not open individual `index.html` files directly.

---

## Development Mode

For frontend development with Vite:

```bash
cd frontend/desktop-tutorial/frontend
npm install
npm run dev
```

The development frontend runs at:

```text
http://localhost:5173
```

The Spring Boot backend runs at:

```text
http://localhost:8080
```

Vite proxies `/api/*` requests to the backend.

Example:

```text
Frontend:
http://localhost:5173/api/v1/crops

Backend:
http://localhost:8080/api/v1/crops
```

---

## API Keys

The application can start without external API keys.

To enable live weather and mandi-price data, configure:

```text
OPENWEATHER_API_KEY
DATA_GOV_API_KEY
```

as environment variables before launching the application.

Do not commit API keys to the repository.

---

## Project Structure

```text
FasalSathi/
│
├── run-app.bat
├── setup-and-run.bat
├── train_model.py
│
├── vosk-model-small-en-us-0.15/
│
└── frontend/
    └── desktop-tutorial/
        │
        ├── pom.xml
        │
        ├── models/
        │   ├── crop_model.pt
        │   └── classes.txt
        │
        ├── frontend/
        │   ├── package.json
        │   ├── package-lock.json
        │   ├── vite.config.js
        │   └── src/
        │
        └── src/
            └── main/
                ├── java/
                └── resources/
```

---

## Machine Learning Models

TorchScript model files are stored under:

```text
frontend/desktop-tutorial/models/
```

The model class mapping is stored in:

```text
frontend/desktop-tutorial/models/classes.txt
```

The Java inference service must use the same class ordering as `classes.txt`.

The model file and class mapping must remain synchronized.

---

## Speech Recognition

The Vosk English model is stored at:

```text
vosk-model-small-en-us-0.15/
```

The backend resolves the model relative to the repository/project runtime location.

---

## Training

Training datasets are intentionally excluded from the repository.

To retrain the crop disease model, provide the required datasets and run:

```bash
python train_model.py
```

The default training output is:

```text
models/crop_model.pt
models/classes.txt
```

When training from a different working directory, use an explicit `--output-dir` so that the generated files are placed in the application's model directory.

---

## Main API Endpoints

All application APIs use the `/api/v1` prefix.

```text
GET  /api/v1/health
GET  /api/v1/districts
GET  /api/v1/crops
POST /api/v1/diagnose
GET  /api/v1/weather
GET  /api/v1/mandi-prices
GET  /api/v1/kvk
POST /api/v1/speech/transcribe
GET  /api/v1/translations
```

---

## Important Runtime URLs

### Packaged / Main Application

```text
http://localhost:8080
```

### Development Frontend

```text
http://localhost:5173
```

### Backend API

```text
http://localhost:8080/api/v1/
```

---

## Notes

* `run-app.bat` is the only user-facing launcher.
* `setup-and-run.bat` is an internal setup/startup script.
* The canonical application source is under `frontend/desktop-tutorial/`.
* There is no second supported backend.
* Do not open React `index.html` directly from the filesystem.
* Frontend API requests should use relative `/api/...` paths during Vite development.
* Generated build output and `node_modules` should not be committed.
* Keep ML model files and `classes.txt` synchronized.

---

## Troubleshooting

### Java not found

Check:

```bash
java -version
```

Java 17 or newer is required.

### Maven not found

Check:

```bash
mvn -version
```

Maven 3.9 or newer is recommended.

### Node.js not found

Check:

```bash
node --version
npm --version
```

Node.js 20 or newer is required.

### Port 8080 already in use

Stop the process currently using port 8080 or change the Spring Boot server port and update the frontend proxy accordingly.

### Frontend build failure

From:

```text
frontend/desktop-tutorial/frontend/
```

run:

```bash
npm install
npm run build
```

### Backend startup failure

From:

```text
frontend/desktop-tutorial/
```

run:

```bash
mvn spring-boot:run
```

and inspect the console output.

### Diagnosis failure

Verify:

```text
frontend/desktop-tutorial/models/crop_model.pt
frontend/desktop-tutorial/models/classes.txt
```

exist and that the Java inference service can load the TorchScript model.

---

## Current Architecture

```text
Browser
   │
   ├── Packaged application
   │       │
   │       ▼
   │   http://localhost:8080
   │
   └── Development
           │
           ▼
       Vite :5173
           │
           │ /api/*
           ▼
       Spring Boot :8080
           │
           ├── Crop disease inference
           ├── H2 database
           ├── Weather/market services
           └── Vosk speech recognition
```
