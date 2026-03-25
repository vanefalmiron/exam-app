from docx import Document

def parse_exam(file):
    doc = Document(file)
    # Filtrar párrafos vacíos
    paragraphs = [p for p in doc.paragraphs if p.text.strip()]
    questions = []

    for i, para in enumerate(paragraphs):
        text = para.text.strip()

        # Usar "Pregunta X Respuesta" como ancla
        if not (text.startswith("Pregunta ") and "Respuesta" in text):
            continue

        # El párrafo anterior es el enunciado de la pregunta
        if i == 0:
            continue
        enunciado = paragraphs[i - 1].text.strip()

        # Ignorar si el enunciado es un encabezado de unidad
        if enunciado.lower().startswith("unidad "):
            continue

        # Recoger las opciones A/B/C/D hasta la siguiente ancla
        opciones = []
        correcta = None
        j = i + 1
        while j < len(paragraphs):
            next_text = paragraphs[j].text.strip()
            # Parar si encontramos la siguiente pregunta
            if next_text.startswith("Pregunta ") and "Respuesta" in next_text:
                break
            # Es una opción si empieza por A. B. C. D.
            if next_text[:2].upper() in ["A.", "B.", "C.", "D.", "A ", "B ", "C ", "D "]:
                is_bold = any(run.bold for run in paragraphs[j].runs if run.text.strip())
                opciones.append(next_text)
                if is_bold:
                    correcta = next_text
            j += 1

        # Solo añadir si tiene opciones y respuesta correcta marcada
        if opciones and correcta:
            questions.append({
                "pregunta": enunciado,
                "opciones": opciones,
                "correcta": correcta
            })

    return questions
