# Alertas de coches por Telegram

Este proyecto revisa portales de coches usados y envía un mensaje de Telegram cuando detecta anuncios nuevos que cumplan tus filtros.

Fuentes incluidas:

- Autohero
- Clicars
- OcasionPlus
- Flexicar

## Preparación local

1. Crea o activa tu entorno virtual.
2. Instala dependencias:

```powershell
pip install -r requirements.txt
```

3. Crea un archivo `.env` copiando `.env.example`.
4. Rellena tu token y chat ID de Telegram.
5. Ajusta los filtros versionados en `config.py`.
6. Ejecuta el script:

```powershell
python alerta.py
```

Si faltan las credenciales de Telegram, el script no fallará: imprimirá por consola las coincidencias encontradas.

## Credenciales y configuración

- `TELEGRAM_BOT_TOKEN`: token del bot creado con BotFather.
- `TELEGRAM_CHAT_ID`: identificador del chat o usuario que recibirá las alertas.

Las credenciales de Telegram se leen desde `.env`.

La configuración funcional se versiona en `config.py`:

- `max_price`: precio máximo aceptado.
- `max_monthly_payment`: cuota máxima aceptada.
- `exclude_keywords`: palabras a excluir.
- `send_only_new`: evita alertas repetidas usando `alert_state.json`.
- `max_alert_items`: máximo de enlaces incluidos por ejecución.
- `max_message_chars`: límite por bloque de mensaje antes de dividirlo.
- `request_timeout`: timeout de las peticiones HTTP y del envío a Telegram.

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
	- `TELEGRAM_BOT_TOKEN`
	- `TELEGRAM_CHAT_ID`
3. Ajusta en `config.py` los filtros como `max_price`, `max_monthly_payment`, `exclude_keywords` o `max_alert_items` si lo necesitas.
4. En `Settings > Actions > General`, activa permisos `Read and write permissions` para que el workflow pueda actualizar `alert_state.json`.
5. El workflow se ejecutará cada hora y también se puede lanzar manualmente desde la pestaña `Actions`.
6. Cuando encuentre anuncios nuevos y los marque como vistos, hará commit automático del archivo `alert_state.json` para no repetir alertas en la siguiente ejecución.

## Telegram

1. Abre Telegram y busca `@BotFather`.
2. Crea un bot con `/newbot` y copia el token.
3. Envía cualquier mensaje a tu bot para abrir el chat.
4. Obtén tu `chat_id` con la URL `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`.
5. Copia `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` a tu `.env`.

## Notas

- Las webs pueden cambiar su HTML. Si dejan de salir resultados, revisa selectores y textos.
- En PythonAnywhere conviene dejar `SEND_ONLY_NEW=true` para no repetir avisos.
- Los mensajes de Telegram se envían agrupados por fuente y con solo la URL limpia para reducir tamaño.
- En GitHub Actions, `alert_state.json` debe estar versionado para conservar el histórico entre ejecuciones.