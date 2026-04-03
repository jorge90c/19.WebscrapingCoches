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
4. Rellena tus credenciales de Twilio.
5. Ajusta los filtros versionados en `config.py`.
6. Ejecuta el script:

```powershell
python alerta.py
```

Si faltan las credenciales de Twilio, el script no fallará: imprimirá por consola las coincidencias encontradas.

## Credenciales y configuración

- `TWILIO_ACCOUNT_SID`: SID de tu cuenta Twilio.
- `TWILIO_AUTH_TOKEN`: token de autenticación.
- `TWILIO_WHATSAPP_NUMBER`: número del sandbox o número aprobado por Twilio.
- `DESTINO_WHATSAPP_NUMBER`: tu número en formato `whatsapp:+34...`.

Las credenciales de Twilio se leen desde `.env`.

La configuración funcional se versiona en `config.py`:

- `max_price`: precio máximo aceptado.
- `max_monthly_payment`: cuota máxima aceptada.
- `exclude_keywords`: palabras a excluir.
- `send_only_new`: evita alertas repetidas usando `alert_state.json`.
- `max_alert_items`: máximo de enlaces incluidos por ejecución.
- `max_message_chars`: límite por bloque de mensaje antes de dividirlo.
- `request_timeout`: timeout de las peticiones HTTP.

## PythonAnywhere

1. Sube `alerta.py`, `config.py`, `requirements.txt` y tu `.env` al directorio del proyecto.
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

## GitHub Actions

1. Sube el proyecto a un repositorio de GitHub.
2. En `Settings > Secrets and variables > Actions > Secrets`, crea estos secretos:
	- `TWILIO_ACCOUNT_SID`
	- `TWILIO_AUTH_TOKEN`
	- `TWILIO_WHATSAPP_NUMBER`
	- `DESTINO_WHATSAPP_NUMBER`
3. Ajusta en `config.py` los filtros como `max_price`, `max_monthly_payment`, `exclude_keywords` o `max_alert_items` si lo necesitas.
4. En `Settings > Actions > General`, activa permisos `Read and write permissions` para que el workflow pueda actualizar `alert_state.json`.
5. El workflow se ejecutará cada hora y también se puede lanzar manualmente desde la pestaña `Actions`.
6. Cuando encuentre anuncios nuevos y los marque como vistos, hará commit automático del archivo `alert_state.json` para no repetir alertas en la siguiente ejecución.

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
- En GitHub Actions, `alert_state.json` debe estar versionado para conservar el histórico entre ejecuciones.