from docx import Document
import re

def parse_exam(file):
    doc = Document(file)
    MARKER_RE = re.compile(r'(Pregunta\s+\d+\s+Respuesta)')
    OPTION_RE = re.compile(r'^[A-Z][.\s]')

    tokens = []

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
                    subparts = re.split(r'(?<!\A)(?=[A-Z]\. )', line)
                    for sp in subparts:
                        sp = sp.strip()
                        if sp:
                            tokens.append((sp, chunk_bold))

    questions = []
    current_q = None

    for text, is_bold in tokens:
        starts_option = bool(OPTION_RE.match(text))
        is_marker     = bool(re.match(r'^Pregunta\s+\d+\s+Respuesta$', text))
        is_unit       = text.lower().startswith("unidad ")
        is_correcta   = text.lower().startswith("respuesta correcta")

        if is_unit or is_marker:
            continue

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

        if is_bold and not starts_option:
            if current_q and current_q["opciones"]:
                questions.append(current_q)
            current_q = {"pregunta": text, "opciones": [], "correctas": set(), "_letras": set()}

        elif current_q is not None and starts_option:
            letra = text[0].upper()
            if letra in current_q["_letras"]:
                continue
            current_q["_letras"].add(letra)
            current_q["opciones"].append(text)
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
