# Alertas de coches por WhatsApp

Este proyecto revisa tres portales de coches usados y envía un WhatsApp cuando detecta anuncios nuevos que cumplan tus filtros.

Fuentes incluidas:

- Autohero
- Clicars
- OcasionPlus

## Preparación local

1. Crea o activa tu entorno virtual.
2. Instala dependencias:

```powershell
pip install -r requirements.txt
```

3. Crea un archivo `.env` copiando `.env.example`.
4. Rellena tus credenciales de Twilio y ajusta los filtros.
5. Ejecuta el script:

```powershell
python alerta.py
```

Si faltan las credenciales de Twilio, el script no fallará: imprimirá por consola las coincidencias encontradas.

## Variables importantes

- `TWILIO_ACCOUNT_SID`: SID de tu cuenta Twilio.
- `TWILIO_AUTH_TOKEN`: token de autenticación.
- `TWILIO_WHATSAPP_NUMBER`: número del sandbox o número aprobado por Twilio.
- `DESTINO_WHATSAPP_NUMBER`: tu número en formato `whatsapp:+34...`.
- `MAX_PRICE`: precio máximo aceptado.
- `MAX_MONTHLY_PAYMENT`: cuota máxima aceptada.
- `EXCLUDE_KEYWORDS`: palabras a excluir separadas por comas.
- `SEND_ONLY_NEW`: evita alertas repetidas usando `alert_state.json`.
- `MAX_ALERT_ITEMS`: máximo de enlaces incluidos por ejecución.
- `MAX_MESSAGE_CHARS`: límite por bloque de mensaje antes de dividirlo.

## PythonAnywhere

1. Sube `alerta.py`, `requirements.txt` y tu `.env` al directorio del proyecto.
2. Crea un virtualenv en PythonAnywhere.
3. Instala dependencias dentro del virtualenv:

```bash
pip install -r requirements.txt
```

4. Ejecuta una prueba manual desde una consola Bash:

```bash
python alerta.py
```

5. Crea una tarea programada para lanzar el script con la frecuencia que quieras.

## WhatsApp con Twilio

1. Crea una cuenta en Twilio.
2. Activa el sandbox de WhatsApp.
3. Vincula tu móvil enviando el código del sandbox al número que indique Twilio.
4. Copia `ACCOUNT SID`, `AUTH TOKEN` y el número del sandbox a tu `.env`.
5. Usa como destino tu número real en formato `whatsapp:+34...`.

## Notas

- Las webs pueden cambiar su HTML. Si dejan de salir resultados, revisa selectores y textos.
- En PythonAnywhere conviene dejar `SEND_ONLY_NEW=true` para no repetir avisos.
- Los mensajes de WhatsApp se envían agrupados por fuente y con solo la URL limpia para reducir tamaño.