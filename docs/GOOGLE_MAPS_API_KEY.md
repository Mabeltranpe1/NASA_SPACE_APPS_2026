# Guía: crear una API key de Google Maps

Paso a paso para crear una API key de **Google Maps JavaScript API** en Google Cloud y comprobar si funciona con la plataforma.

> **Contexto:** la primera key del proyecto no funcionó porque la cuenta de facturación quedó **cerrada**: en Colombia, Google Cloud pide un **prepago** (100.000 COP) para activarla, incluso en la prueba gratuita. Por eso la plataforma usa hoy NASA GIBS + MapLibre (ver [BITACORA.md](BITACORA.md)). Esta guía sirve para probar con **otra cuenta** de Google Cloud por si esa sí tiene la facturación activa.
>
> **Regla del proyecto:** solo servicios gratuitos. **Si en algún paso Google pide un pago o un prepago, detente** y avísale al equipo antes de pagar.

---

## Paso 0. Revisar si la facturación está activa (lo más importante)

1. Entra a https://console.cloud.google.com/billing
2. Abre tu cuenta de facturación y mira el estado:

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Cuenta **activa**, sin avisos | ✅ Maps va a funcionar | Sigue al paso 1 |
| Aviso amarillo *"Tu prueba gratuita requiere un prepago"* | ❌ Pide prepago | **Detente** y avisa al equipo |
| *"Esta cuenta de facturación está cerrada"* (rojo) | ❌ Maps no va a cargar | **Detente** y avisa al equipo |
| No tienes cuenta de facturación | Hay que crearla | Créala; si al crearla pide prepago, **detente** |

Sin facturación activa, **la key se crea igual, pero el mapa no carga**. Ese fue el problema de la primera key.

---

## Paso 1. Crear o elegir un proyecto

1. Arriba, en el selector de proyectos, pulsa **Proyecto nuevo**.
2. Nombre: `nasa-analogs` (o el que prefieras).
3. Comprueba que el proyecto quede vinculado a la cuenta de facturación **activa**: *Facturación → Administrar cuentas de facturación → Mis proyectos*.

## Paso 2. Habilitar la Maps JavaScript API

1. Ve a *APIs y servicios → Biblioteca*: https://console.cloud.google.com/apis/library
2. Busca **Maps JavaScript API**.
3. Pulsa **Habilitar**.

> Si no la habilitas, no aparecerá en la lista de restricciones del paso 3.

## Paso 3. Crear la API key

1. Ve a *APIs y servicios → Credenciales*: https://console.cloud.google.com/apis/credentials
2. **Crear credenciales → Clave de API**.
3. **Nombre:** `nasa-analogs-maps`.
4. **Restricciones de API**: elige **solo** `Maps JavaScript API`. Debe decir **"1 API"**.
   - ⚠️ Si aparecen varias APIs seleccionadas (por ejemplo, 32), desmárcalas todas y deja solo esa.
   - Ignora el aviso sobre *"cuenta de servicio"*: solo aplica a Gemini y Agent Platform.
5. **Restricciones de aplicaciones**: elige **Sitios web** y agrega estos tres referrers:
   ```
   http://localhost:5173/*
   https://icy-flower-03890400f.5.azurestaticapps.net/*
   https://*.eastus2.5.azurestaticapps.net/*
   ```
   - Google **no acepta** comodines en medio del dominio (`icy-flower-03890400f-*.…` da error). El comodín solo va al inicio.
   - **No** agregues `https://*.azurestaticapps.net/*`: es demasiado amplio.
6. **Crear** y copia la key (empieza por `AIza…`).

## Paso 4. Poner un límite de cuota (evita cobros)

1. *APIs y servicios → Maps JavaScript API → Cuotas y límites del sistema*.
2. Edita **Map loads per day** → **500**.

Así, si alguien abusa de la key, el mapa deja de cargar ese día **en lugar de cobrar**.

## Paso 5. Alerta de presupuesto

1. *Facturación → Presupuestos y alertas → Crear presupuesto*.
2. Monto: **USD 1**, con alertas al 50 %, 90 % y 100 %.

> El presupuesto **solo avisa, no corta el servicio**. Lo que de verdad limita el gasto es la cuota del paso 4.
> Si este paso queda en un bucle de *"Enable billing"*, la facturación **no está activa**: vuelve al paso 0.

---

## Paso 6. Probar que la key funciona

Prueba rápida en local, sin tocar el proyecto:

1. Crea un archivo `prueba-maps.html` en tu computador con este contenido, reemplazando `TU_API_KEY`:
   ```html
   <!doctype html>
   <html>
     <body style="margin:0">
       <div id="map" style="height:100vh"></div>
       <script>
         function init() {
           new google.maps.Map(document.getElementById('map'), {
             center: { lat: 3.23, lng: -75.17 }, zoom: 10, mapTypeId: 'hybrid'
           })
         }
       </script>
       <script async src="https://maps.googleapis.com/maps/api/js?key=TU_API_KEY&callback=init"></script>
     </body>
   </html>
   ```
2. Sírvelo en el puerto 5173, que es el referrer permitido:
   ```bash
   npx serve -l 5173 .
   ```
3. Abre http://localhost:5173/prueba-maps.html

| Resultado | Significa |
|---|---|
| Se ve el mapa satelital del desierto de la Tatacoa | ✅ La key y la facturación funcionan |
| Recuadro gris *"This page can't load Google Maps correctly"* | ❌ Facturación inactiva o restricciones mal puestas. Abre la consola del navegador (F12) y busca el código de error |
| `BillingNotEnabledMapError` | Facturación no activa (paso 0) |
| `RefererNotAllowedMapError` | Falta el referrer (paso 3.5) |
| `ApiNotActivatedMapError` | Falta habilitar la API (paso 2) |
| `ApiTargetBlockedMapError` | La restricción de API no incluye Maps JavaScript API (paso 3.4) |

Después de la prueba, borra `prueba-maps.html`.

## Paso 7. Si funciona: cargar la key en GitHub

1. Carga el secret. Este comando pide la key de forma **oculta**: escríbelo tal cual, presiona Enter y **después** pega la key:
   ```bash
   read -rsp "Pega la API key de Google Maps: " KEY; echo; printf '%s' "$KEY" | gh secret set VITE_GOOGLE_MAPS_API_KEY -R Mabeltranpe1/NASA_SPACE_APPS_2026; unset KEY
   ```
   - ⚠️ **No** pegues la key dentro de las comillas: ese texto es solo el mensaje que aparece en pantalla, y la key quedaría en el historial de la terminal.
   - Debe responder `✓ Set Actions secret VITE_GOOGLE_MAPS_API_KEY`.
2. Avísale al equipo. La versión actual de la plataforma usa NASA GIBS, así que hay que **volver a activar el componente de Google Maps**. El código anterior está en el historial de git (commit `34c41bd`, archivo `web/src/App.tsx`).
3. Registra el resultado en [BITACORA.md](BITACORA.md), funcione o no.

## Seguridad

- **Nunca** pegues la key en el chat, en issues, en commits ni en archivos del repo.
- La key quedará visible en el navegador de quien use la app. Es normal en apps web: lo que la protege son las **restricciones** de los pasos 3 y 4.
- Si la key se filtra sin restricciones: *Credenciales → tu key → Regenerar clave*, y actualiza el secret.
