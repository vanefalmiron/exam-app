# 📝 Exam Practice App — ASIR

Aplicación web interactiva para practicar exámenes tipo test a partir de un archivo Word (`.docx`). Desarrollada en Python con Streamlit y desplegada en la nube de forma gratuita.

---

## 🚀 Demo

Accede a la app en: [https://share.streamlit.io](https://share.streamlit.io)

---

## 📌 ¿Qué hace esta app?

- Lee un archivo Word `.docx` con preguntas tipo test
- Detecta automáticamente la respuesta correcta (marcada en **negrita** en el Word)
- Presenta 50 preguntas aleatorias por sesión del banco total
- Muestra feedback inmediato tras cada respuesta (✅ correcto / ❌ incorrecto)
- Lleva la cuenta de respuestas correctas e incorrectas en tiempo real
- Al finalizar, ofrece un repaso completo con todas las respuestas y un filtro de solo errores

---

## 🗂️ Estructura del proyecto

```
exam_app/
├── app.py            # Interfaz web (Streamlit)
├── parser.py         # Lector y procesador del archivo Word
├── requirements.txt  # Dependencias del proyecto
└── README.md         # Este archivo
```

---

## 📄 Formato esperado del Word

El archivo `.docx` debe seguir esta estructura por cada pregunta:

```
Enunciado de la pregunta en negrita

Pregunta 1 Respuesta

A. Opción uno
B. Opción dos
C. Opción tres (en negrita si es la correcta)
D. Opción cuatro

Respuesta correcta: C. Opción tres   ← línea opcional como refuerzo
```

**Reglas importantes:**
- El **enunciado** de la pregunta debe estar en negrita
- La **opción correcta** debe estar en negrita
- La línea `Pregunta X Respuesta` sirve como separador entre preguntas
- Opcionalmente se puede añadir una línea `Respuesta correcta: X. texto` para reforzar la detección
- Los encabezados de unidad (`Unidad X — ...`) son ignorados automáticamente

---

## ⚙️ Funcionamiento del parser

El `parser.py` procesa el Word de la siguiente manera:

1. Recorre todos los párrafos del documento
2. Analiza la negrita **run a run** (no por párrafo completo) para identificar correctamente qué opción está en negrita, incluso cuando todas las opciones están en el mismo bloque de texto
3. Separa opciones que vengan pegadas en una misma línea (`A. texto B. texto C. texto`)
4. Elimina duplicados — si una letra (A/B/C/D) aparece más de una vez, solo conserva la primera
5. Ordena las opciones siempre en orden A → B → C → D
6. Si existe una línea `Respuesta correcta:`, esa tiene prioridad sobre la negrita
7. Filtra preguntas sin respuesta correcta identificada

---

## 🧠 Lógica de la app

- Selecciona **50 preguntas aleatorias** del banco total cada sesión
- Las opciones se muestran en orden A, B, C, D (sin mezclar)
- Tras confirmar una respuesta, muestra:
  - Banner verde/rojo indicando si fue correcta o no
  - Las opciones coloreadas: verde = correcta, rojo = tu respuesta incorrecta
  - Botón para avanzar a la siguiente pregunta
- Métricas visibles en todo momento: pregunta actual, correctas, incorrectas
- Al terminar las 50 preguntas, muestra resultado final con porcentaje
- Pestaña de repaso con todas las preguntas y pestaña de solo errores
- Botón de reinicio en el sidebar para empezar de nuevo con nuevas preguntas aleatorias

---

## 🛠️ Herramientas utilizadas

| Herramienta | Versión | Uso |
|---|---|---|
| **Python** | 3.10+ | Lenguaje principal |
| **Streamlit** | latest | Framework de UI web |
| **python-docx** | latest | Lectura y parsing del archivo Word |
| **re** (stdlib) | — | Expresiones regulares para parsear texto |
| **random** (stdlib) | — | Selección aleatoria de preguntas |
| **GitHub** | — | Control de versiones y almacenamiento del código |
| **Streamlit Community Cloud** | — | Despliegue gratuito de la app en internet |

---

## 📦 Instalación local (opcional)

Si quieres ejecutarlo en tu propio ordenador:

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/exam-app.git
cd exam-app

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
streamlit run app.py
```

La app estará disponible en `http://localhost:8501`

---

## ☁️ Despliegue en Streamlit Cloud

1. Sube el código a un repositorio **público** en GitHub
2. Entra en [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub
3. Haz clic en **Create app**
4. Selecciona el repositorio, rama `main` y archivo `app.py`
5. Haz clic en **Deploy**

Cada vez que hagas `git push`, la app se actualiza automáticamente.

---

## 📋 requirements.txt

```
streamlit
python-docx
```

---

## 🔄 Cómo actualizar la app

```bash
# Tras modificar cualquier archivo
git add .
git commit -m "descripción del cambio"
git push
```

Streamlit Cloud detecta el push y redespliega en segundos.

---

## 📊 Estadísticas del banco de preguntas

| Métrica | Valor |
|---|---|
| Total preguntas detectadas | ~323 |
| Preguntas por sesión | 50 (aleatorias) |
| Opciones por pregunta | 4 (A, B, C, D) |
| Umbral de aprobado | 70% |

---

## 🤖 Desarrollo

Este proyecto fue desarrollado con asistencia de **Claude (Anthropic)**, que ayudó en:
- Diseño de la arquitectura del proyecto
- Desarrollo del parser para leer archivos Word con negrita
- Depuración de problemas de formato del documento (opciones duplicadas, negrita por run vs por párrafo, opciones mezcladas en un mismo bloque)
- Desarrollo de la interfaz con Streamlit
- Configuración del despliegue en Streamlit Cloud

---

*Proyecto creado para la preparación del examen ASIR.*
