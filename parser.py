from docx import Document
import re

def parse_exam(file):
    doc = Document(file)
    MARKER_RE = re.compile(r'(Pregunta\s+\d+\s+Respuesta)')

    # Convertir el documento en tokens (texto, is_bold)
    tokens = []
    for para in doc.paragraphs:
        raw = para.text
        if not raw.strip():
            continue
        is_bold = any(r.bold for r in para.runs if r.text.strip())

        parts = MARKER_RE.split(raw)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            for line in part.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Separar opciones pegadas en la misma línea ("A. xxx B. yyy")
                subparts = re.split(r'(?<!\A)(?=[A-D]\. )', line)
                for sp in subparts:
                    sp = sp.strip()
                    if sp:
                        tokens.append((sp, is_bold))

    # Parsear tokens
    questions = []
    current_q = None

    for text, is_bold in tokens:
        starts_option  = bool(re.match(r'^[A-D][.\s]', text))
        is_marker      = bool(re.match(r'^Pregunta\s+\d+\s+Respuesta$', text))
        is_unit        = text.lower().startswith("unidad ")
        is_correcta    = text.lower().startswith("respuesta correcta")

        if is_unit or is_marker:
            continue

        # Línea explícita "Respuesta correcta: X. texto"
        if is_correcta and current_q:
            m = re.search(r'[Rr]espuesta correcta[:\s]+(.+)', text)
            if m:
                correcta_texto = m.group(1).strip()
                for op in current_q["opciones"]:
                    if op.strip() == correcta_texto or op.strip().endswith(correcta_texto):
                        current_q["correcta"] = op
                        break
                if not current_q["correcta"]:
                    current_q["correcta"] = correcta_texto
            continue

        # Nueva pregunta: negrita y no es opción
        if is_bold and not starts_option:
            if current_q and current_q["opciones"]:
                questions.append(current_q)
            current_q = {"pregunta": text, "opciones": [], "correcta": None, "_letras": set()}

        # Opción A/B/C/D
        elif current_q is not None and starts_option:
            letra = text[0].upper()
            # Ignorar si ya tenemos esa letra (evita duplicados)
            if letra in current_q["_letras"]:
                continue
            current_q["_letras"].add(letra)
            current_q["opciones"].append(text)
            if is_bold and not current_q["correcta"]:
                current_q["correcta"] = text

    if current_q and current_q["opciones"]:
        questions.append(current_q)

    # Ordenar A → B → C → D y limpiar campo interno
    def sort_key(op):
        m = re.match(r'^([A-D])[.\s]', op)
        return m.group(1) if m else op

    for q in questions:
        q["opciones"] = sorted(q["opciones"], key=sort_key)
        del q["_letras"]

    # Solo preguntas con respuesta correcta identificada
    questions = [q for q in questions if q["correcta"]]

    return questions
