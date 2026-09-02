# IT Service Desk - Kubernetes deployment

This deployment is based on the complete project source provided by the user.

## Images

- `prabhushriyaans/it_service_desk_flask_app:latest`
- `prabhushriyaans/it_service_desk_mysql:8.4`
- `prabhushriyaans/it_service_desk_ollama:latest`

## Important project-specific fixes

- Flask listens on port 5000, not 3000.
- Flask uses `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`.
- The application database is `IT_S`, matching `.env` and `init.sql`.
- Kubernetes MySQL is reached as `mysql-service:3306`; do not use localhost or host port 3307/3308 from Flask.
- MySQL uses the same application DB user/password from the local `.env`.
- `init.sql` is mounted into `/docker-entrypoint-initdb.d/init.sql`.
- Flask uploads are stored in a PVC.
- Ollama models are stored in a PVC at `/root/.ollama`.
- Local HTTP uses `JWT_COOKIE_SECURE=0`; switch to `1` only when Flask is served over HTTPS.

## Deploy

1. Keep this folder next to the project root so that the project `.env` is at `../.env` relative to this bundle.
2. Ensure Docker Desktop Kubernetes is running and the `docker-desktop` context is active.
3. From this folder run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy.ps1
```

The script reads the application values from the project `.env` and prompts for the MySQL root password. It creates a Kubernetes Secret locally and never writes the secret into the YAML files.

## Verify

```powershell
kubectl get pods -n it-service-desk
kubectl get svc -n it-service-desk
kubectl get pvc -n it-service-desk
```

Open: `http://localhost:30007`

## MySQL initialization note

`init.sql` runs only when MySQL initializes a fresh data directory. If `mysql-pvc` already contains an old database from a previous failed deployment, the initialization script will not be re-run. Only when you are certain the old Kubernetes database contains no data you need, delete the namespace/PVC and deploy again.

## Ollama model note

The Ollama image does not prove that a model is installed. Models are stored in the `ollama-pvc`. After Ollama is running, install a model, for example:

```powershell
kubectl exec -n it-service-desk deploy/ollama-deployment -- ollama pull llama3.2
```

Use the model name required by your application. The current Flask source does not contain an Ollama API call, so Ollama is deployed as a ready internal service rather than being assumed to be integrated.
