from docx import Document


def parse_exam(file):
    doc = Document(file)
    questions = []
    current_q = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        is_bold = any(run.bold for run in para.runs if run.text.strip())

        # Detectar pregunta (empieza con número)
        if para.text and para.text[0].isdigit():
            if current_q and current_q["correcta"]:
                questions.append(current_q)
            current_q = {"pregunta": text, "opciones": [], "correcta": None}

        # Detectar opción (empieza con A, B, C o D)
        elif current_q and text and text[0].upper() in "ABCD":
            current_q["opciones"].append(text)
            if is_bold:
                current_q["correcta"] = text

    if current_q and current_q["correcta"]:
        questions.append(current_q)

    return questions
