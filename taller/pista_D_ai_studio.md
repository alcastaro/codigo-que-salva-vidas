# 📱 Pista D (extra) — La alerta: de datos técnicos a un mensaje que salva vidas

**Código que Salva Vidas · DevFest Santo Domingo 2026 · Taller · Nivel principiante**
**Sin código. Funciona desde el teléfono.** Solo necesitas una cuenta de Google.

Un pronóstico perfecto no sirve de nada si la gente no lo entiende. En esta pista usas **Google AI Studio**
para construir el último eslabón de la cadena: el que convierte números en una instrucción clara.

| Paso | Qué haces | Tiempo |
|---|---|---|
| 1 | Darle a Gemini el rol de redactor de alertas | 3 min |
| 2 | Pasarle datos reales del huracán Melissa | 3 min |
| 3 | Obligarlo a responder en el formato estándar de alertas (CAP) | 4 min |
| 4 | Comparar con **Gemma**, el modelo abierto que corre sin internet | 3 min |
| 5 | Crear tu propia app de alertas con **Build** | 7 min |

---

## Antes de empezar (1 minuto)

1. Abre **[aistudio.google.com](https://aistudio.google.com)** en el navegador del teléfono o de la laptop.
2. Inicia sesión con tu cuenta de Google y, si es la primera vez, acepta los términos de uso.
3. Ten esta guía abierta en otra pestaña: vas a copiar y pegar los bloques de texto gris. En el teléfono, mantén pulsado el bloque y elige **Copiar**; en la laptop, usa el icono de copiar que aparece arriba a la derecha de cada bloque.

En esta pista **no necesitas API key**: AI Studio usa tu sesión de Google directamente.

> AI Studio cambia de diseño con frecuencia. Si un botón no está exactamente donde dice la guía, búscalo por su nombre; en el teléfono, muchas opciones están detrás del icono de ajustes ⚙️ o del menú ☰.

## Paso 1 · El rol

1. En AI Studio, crea un **chat nuevo** (botón **+** o **New chat**).
2. Abre **System instructions** (instrucciones del sistema).
3. Pega esto:

```text
Eres el redactor de alertas de una oficina de protección civil del Caribe.
Recibes datos técnicos y escribes UNA alerta para la población, en español sencillo.
Reglas:
- Se tiene que entender en 3 segundos: primero QUÉ pasa, luego DÓNDE, luego QUÉ HACER.
- Máximo 280 caracteres en el mensaje. Sin tecnicismos (nada de nudos, hPa ni probabilidades con decimales).
- No inventes datos que no estén en la entrada. Si la certeza es baja, dilo.
```

> **Por qué importa:** las instrucciones del sistema son las reglas fijas del modelo. El usuario cambia
> los datos, pero las reglas no se negocian. Es la diferencia entre un chatbot y una herramienta.

## Paso 2 · Los datos

Pega esto en el chat. Son los números que calcula la Pista A con el pronóstico de **Google DeepMind Weather Lab**
emitido el 25 de octubre de 2025, tres días antes de que Melissa tocara tierra:

```json
{
  "evento": "Huracán Melissa",
  "pronostico_emitido": "2025-10-25 00:00 UTC",
  "lugar": "Black River, Jamaica",
  "probabilidad_paso_a_menos_de_100_km": 0.86,
  "viento_esperado": "Categoría 4, con 28% de probabilidad de categoría 5",
  "llegada_mas_probable": "28 de octubre, 12:00 UTC"
}
```

**🧠 Para pensar:** ¿la alerta dice qué hacer? ¿Usa alguna palabra técnica que tu abuela no entendería?
Ajusta las instrucciones del sistema y vuelve a probar.

## Paso 3 · El formato estándar (CAP)

Las autoridades no publican alertas en texto libre. Usan el **Protocolo Común de Alertas (CAP)**, el estándar
con el que Google recibe las alertas oficiales para mostrarlas en Búsqueda, Maps y Android.

1. En el panel derecho, activa **Structured output** y pulsa **Edit**.
2. Pega este esquema:

```json
{
  "type": "object",
  "properties": {
    "titulo":    { "type": "string" },
    "mensaje":   { "type": "string" },
    "que_hacer": { "type": "array", "items": { "type": "string" } },
    "severidad": { "type": "string", "enum": ["Extreme", "Severe", "Moderate", "Minor", "Unknown"] },
    "urgencia":  { "type": "string", "enum": ["Immediate", "Expected", "Future", "Past", "Unknown"] },
    "certeza":   { "type": "string", "enum": ["Observed", "Likely", "Possible", "Unlikely", "Unknown"] }
  },
  "required": ["titulo", "mensaje", "que_hacer", "severidad", "urgencia", "certeza"]
}
```

3. Vuelve a enviar los datos. Ahora la respuesta es un **JSON** que cualquier sistema puede leer y reenviar
   por SMS, por WhatsApp o a una sirena.

## Paso 4 · Gemma: la misma tarea, sin internet

Cambia el modelo arriba a la derecha a uno de la familia **Gemma**. Gemma es la familia de modelos **abiertos** de Google:
sus versiones pequeñas corren en un teléfono o en una Raspberry Pi, sin conexión.

Así funciona **Acuífero·Vigía**, ganador del premio *Global Resilience* del **Gemma 4 Good Challenge** (Kaggle + Google DeepMind):
un sistema de alerta de inundaciones en Sudamérica que funciona aunque se caiga internet.

**🧠 Para pensar:** ¿la alerta de Gemma es peor? ¿Lo bastante buena para una zona sin señal?

## Paso 5 · Tu app con Build

1. En el menú de la izquierda, entra en **Build**.
2. Pega este encargo:

```text
Crea una app web en español llamada "Traductor de alertas".
- Un cuadro de texto donde pego un boletín técnico de meteorología o hidrología (en inglés o español).
- Un selector de idioma de salida: español, inglés, creole haitiano.
- Un botón "Traducir para la gente" que llama a Gemini y devuelve una alerta con: título,
  mensaje de máximo 280 caracteres, lista de qué hacer, y tres etiquetas de colores con severidad,
  urgencia y certeza (Protocolo Común de Alertas, CAP).
- La alerta se muestra como una notificación de teléfono, con tipografía grande y alto contraste.
- Un botón para copiar el mensaje y otro para compartirlo por WhatsApp.
- Un aviso fijo al pie: "Herramienta de práctica. Para alertas reales, consulta a tu servicio meteorológico nacional."
```

3. Prueba la app con un boletín real. Por ejemplo, copia un párrafo de un aviso del Centro Nacional de Huracanes
   ([nhc.noaa.gov](https://www.nhc.noaa.gov)) o de la ONAMET.
4. **Reto:** pídele a Build que añada un mapa, un modo oscuro o un botón para escuchar la alerta en voz alta.

---

**Ética, en una línea:** esto es una práctica. Una alerta real la emite una autoridad, la revisa una persona y se
prueba con la comunidad antes de usarse. La IA ayuda a redactar, pero no reemplaza esa cadena.
