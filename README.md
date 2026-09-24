# Webcam local

Aplicación simple para Windows que transmite una webcam en una página local y permite cambiar entre cámaras.

## Arranque

En PowerShell, desde esta carpeta:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Abre <http://127.0.0.1:5000> :D