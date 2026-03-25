from docx import Document
import re

def parse_exam(file):
    doc = Document(file)

    # Aplanar el documento en líneas individuales, dividiendo párrafos
    # que mezclan varias opciones o tienen saltos de línea internos
    lines = []  # lista de (texto, is_bold)

    for para in doc.paragraphs:
        raw = para.text.strip()
        if not raw:
            continue

        is_bold = any(r.bold for r in para.runs if r.text.strip())

        # Dividir por saltos de línea internos
        parts = raw.split('\n')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Subdividir si hay varias opciones en la misma línea: "A. texto B. texto"
            subparts = re.split(r'(?<!\A)(?=[A-D]\. )', part)
            for sp in subparts:
                sp = sp.strip()
                if sp:
                    lines.append((sp, is_bold))

    # Parsear las líneas
    questions = []
    current_q = None

    for text, is_bold in lines:
        starts_with_option = bool(re.match(r'^[A-Da-d][.\s]', text))
        is_skip = text.startswith("Pregunta ") and "Respuesta" in text
        is_unit = text.lower().startswith("unidad ")

        if is_unit:
            continue

        if is_skip:
            if current_q and current_q["correcta"]:
                questions.append(current_q)
            current_q = None
            continue

        if is_bold and not starts_with_option:
            if current_q and current_q["correcta"]:
                questions.append(current_q)
            current_q = {"pregunta": text, "opciones": [], "correcta": None}

        elif current_q is not None and starts_with_option:
            current_q["opciones"].append(text)
            if is_bold:
                current_q["correcta"] = text

    if current_q and current_q["correcta"]:
        questions.append(current_q)

    return questions
