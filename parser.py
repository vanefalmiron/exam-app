from docx import Document
import re

# Opciones REALES: "A. texto", "B. texto"... pero NO "E. UU." ni abreviaturas
# Requisitos:
#   - Empieza con letra mayúscula + punto + espacio + al menos 2 chars
#   - La letra debe ser la siguiente esperada en la secuencia (A→B→C...)
#     o ser A (inicio de bloque de opciones)
OPTION_STRICT_RE = re.compile(r'^([A-Z])\.\s+\S.+')

# Para el split interno de línea (opciones pegadas en el mismo párrafo)
OPTION_SPLIT_RE = re.compile(r'(?<!\A)(?=[A-Z]\.\s)')

def _is_option(text, expected_letters):
    """
    Devuelve True solo si el texto parece una opción de respuesta legítima:
    - Cumple el patrón estricto (Letra. texto con contenido)
    - La letra es la siguiente esperada O es 'A' (reinicio)
    - El texto tiene al menos 5 caracteres (evita "E. U" como opción)
    """
    m = OPTION_STRICT_RE.match(text)
    if not m:
        return False
    letra = m.group(1)
    if len(text) < 5:
        return False
    # Si no hay opciones todavía, solo aceptamos A
    if not expected_letters and letra != 'A':
        return False
    # La siguiente letra esperada es la inmediatamente posterior a la última
    if expected_letters:
        next_expected = chr(ord(max(expected_letters)) + 1)
        # Aceptar si es la siguiente en secuencia O si es A (reinicio tras nueva pregunta)
        if letra not in (next_expected, 'A'):
            return False
    return True


def parse_exam(file):
    doc = Document(file)
    MARKER_RE = re.compile(r'(Pregunta\s+\d+\s+Respuesta)')

    tokens = []  # (texto, is_bold)

    for para in doc.paragraphs:
        if not para.text.strip():
            continue

        run_chunks = []
        for run in para.runs:
            if run.text:
                run_chunks.append((run.text, bool(run.bold)))

        merged = []
        for text, bold in run_chunks:
            if merged and merged[-1][1] == bold:
                merged[-1] = (merged[-1][0] + text, bold)
            else:
                merged.append([text, bold])

        for chunk_text, chunk_bold in merged:
            parts = MARKER_RE.split(chunk_text)
            for part in parts:
                for line in part.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Split solo cuando hay patrón claro de opciones contiguas
                    subparts = OPTION_SPLIT_RE.split(line)
                    for sp in subparts:
                        sp = sp.strip()
                        if sp:
                            tokens.append((sp, chunk_bold))

    questions = []
    current_q = None

    for text, is_bold in tokens:
        is_marker   = bool(re.match(r'^Pregunta\s+\d+\s+Respuesta$', text))
        is_unit     = text.lower().startswith("unidad ")
        is_correcta = text.lower().startswith("respuesta correcta")

        if is_unit or is_marker:
            continue

        # Línea explícita "Respuesta correcta: X. texto"
        if is_correcta and current_q:
            m = re.search(r'[Rr]espuesta correcta[:\s]+(.+)', text)
            if m:
                correcta_texto = m.group(1).strip()
                for op in current_q["opciones"]:
                    if op.strip() == correcta_texto or op.strip().endswith(correcta_texto):
                        current_q["correctas"].add(op)
                        break
                if not current_q["correctas"]:
                    current_q["correctas"].add(correcta_texto)
            continue

        # Comprobamos si es opción con el nuevo validador estricto
        letras_actuales = current_q["_letras"] if current_q else set()
        starts_option = _is_option(text, letras_actuales)

        # Nueva pregunta: negrita y no es opción
        if is_bold and not starts_option:
            if current_q and current_q["opciones"]:
                questions.append(current_q)
            current_q = {"pregunta": text, "opciones": [], "correctas": set(), "_letras": set()}

        # Opción válida
        elif current_q is not None and starts_option:
            letra = text[0].upper()
            if letra in current_q["_letras"]:
                continue
            current_q["_letras"].add(letra)
            current_q["opciones"].append(text)
            if is_bold and not current_q["correctas"]:
                # Solo marcar como correcta la primera en negrita
                # (para no confundir enunciados en negrita con respuestas)
                pass
            if is_bold:
                current_q["correctas"].add(text)

    if current_q and current_q["opciones"]:
        questions.append(current_q)

    def sort_key(op):
        m = re.match(r'^([A-Z])[.\s]', op)
        return m.group(1) if m else op

    result = []
    for q in questions:
        q["opciones"] = sorted(q["opciones"], key=sort_key)
        del q["_letras"]
        q["correctas"] = sorted(q["correctas"], key=sort_key)
        q["correcta"] = q["correctas"][0] if q["correctas"] else None
        q["multi"] = len(q["correctas"]) > 1
        if q["correctas"]:
            result.append(q)

    return result
