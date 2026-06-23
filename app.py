import streamlit as st
import random
from parser import parse_exam

st.set_page_config(page_title="Examen ASIR", page_icon="📝", layout="centered")
st.title("📝 Práctica de examen")

LIMITE = 50

uploaded = st.file_uploader("Sube tu archivo Word (.docx)", type="docx")

def es_correcta(eleccion, q):
    """Comprueba si la elección del usuario es correcta (soporta multi y single)."""
    if q.get("multi"):
        return sorted(eleccion) == sorted(q["correctas"])
    else:
        return eleccion == q["correcta"]

def _init_exam(questions):
    shuffled = random.sample(questions, min(LIMITE, len(questions)))
    st.session_state.questions = shuffled
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.incorrectas = 0
    st.session_state.answers = {}
    st.session_state.show_result = False
    st.session_state.feedback_idx = None
    st.session_state.repaso_mode = False
    st.session_state.repaso_list = []
    st.session_state.repaso_index = 0
    st.session_state.repaso_answers = {}
    st.session_state.repaso_feedback_idx = None
    st.session_state.repaso_done = False

if uploaded:
    questions = parse_exam(uploaded)

    if not questions:
        st.error("No se encontraron preguntas. Revisa el formato del Word.")
        st.stop()

    if "questions" not in st.session_state:
        _init_exam(questions)

    if st.sidebar.button("🔄 Reiniciar examen"):
        _init_exam(questions)
        st.rerun()

    q_list = st.session_state.questions
    total = len(q_list)
    idx = st.session_state.index

    st.sidebar.markdown(f"**Total preguntas en el banco:** {len(questions)}")
    st.sidebar.markdown(f"**Preguntas en este examen:** {total}")

    # ─────────────────────────────────────────────
    # MODO REPASO DE INCORRECTAS
    # ─────────────────────────────────────────────
    if st.session_state.repaso_mode:
        repaso_list = st.session_state.repaso_list
        r_total = len(repaso_list)
        r_idx = st.session_state.repaso_index

        st.info(f"🔁 Modo repaso — {r_total} preguntas incorrectas")

        if st.session_state.repaso_done:
            # Resultados del repaso
            aciertos_repaso = sum(
                1 for i, q in enumerate(repaso_list)
                if es_correcta(st.session_state.repaso_answers.get(i, [] if q.get("multi") else ""), q)
            )
            pct = round(aciertos_repaso / r_total * 100)
            if pct >= 70:
                st.success(f"## ✅ Repaso completado — {aciertos_repaso}/{r_total} ({pct}%)")
            else:
                st.warning(f"## 🔁 Repaso completado — {aciertos_repaso}/{r_total} ({pct}%)")

            col1, col2 = st.columns(2)
            if col1.button("🔄 Repetir repaso"):
                st.session_state.repaso_index = 0
                st.session_state.repaso_answers = {}
                st.session_state.repaso_feedback_idx = None
                st.session_state.repaso_done = False
                st.rerun()
            if col2.button("🏠 Volver al inicio"):
                _init_exam(questions)
                st.rerun()

        elif r_idx < r_total:
            q = repaso_list[r_idx]
            opciones = q["opciones"]
            is_multi = q.get("multi", False)

            st.progress(r_idx / r_total)
            col1, col2 = st.columns(2)
            col1.metric("Pregunta", f"{r_idx + 1} / {r_total}")
            col2.metric("Tipo", "✌️ Múltiple" if is_multi else "☝️ Una respuesta")

            st.subheader(q["pregunta"])
            if is_multi:
                st.caption(f"⚠️ Selecciona las {len(q['correctas'])} respuestas correctas")

            # MODO FEEDBACK REPASO
            if st.session_state.repaso_feedback_idx == r_idx:
                eleccion = st.session_state.repaso_answers[r_idx]
                correctas = q["correctas"]
                acierto = es_correcta(eleccion, q)

                if acierto:
                    st.success("✅ ¡Correcto!")
                else:
                    st.error("❌ Incorrecto")

                for op in opciones:
                    es_c = op in correctas
                    es_e = op in eleccion if isinstance(eleccion, list) else op == eleccion
                    if es_c and es_e:
                        st.success(f"✅ {op}")
                    elif es_c:
                        st.success(f"✅ {op} ← Respuesta correcta")
                    elif es_e:
                        st.error(f"❌ {op}  ← Tu respuesta")
                    else:
                        st.write(f"　{op}")

                if st.button("➡️ Siguiente", key="repaso_next"):
                    st.session_state.repaso_feedback_idx = None
                    st.session_state.repaso_index += 1
                    if st.session_state.repaso_index >= r_total:
                        st.session_state.repaso_done = True
                    st.rerun()

            # MODO NORMAL REPASO
            else:
                if is_multi:
                    seleccion = []
                    for op in opciones:
                        if st.checkbox(op, key=f"repaso_check_{r_idx}_{op}"):
                            seleccion.append(op)
                    confirmar_disabled = len(seleccion) != len(q["correctas"])
                    if confirmar_disabled and seleccion:
                        st.caption(f"Selecciona exactamente {len(q['correctas'])} opciones (llevas {len(seleccion)})")
                    eleccion_actual = seleccion
                else:
                    eleccion_actual = st.radio("Elige una opción:", opciones, key=f"repaso_q_{r_idx}", index=None)
                    confirmar_disabled = eleccion_actual is None

                if st.button("✅ Confirmar", disabled=confirmar_disabled, key="repaso_confirmar"):
                    st.session_state.repaso_answers[r_idx] = eleccion_actual
                    st.session_state.repaso_feedback_idx = r_idx
                    st.rerun()

    # ─────────────────────────────────────────────
    # EXAMEN NORMAL
    # ─────────────────────────────────────────────
    elif idx < total and not st.session_state.show_result:
        q = q_list[idx]
        opciones = q["opciones"]
        is_multi = q.get("multi", False)

        st.progress(idx / total)
        col1, col2, col3 = st.columns(3)
        col1.metric("Pregunta", f"{min(idx + 1, total)} / {total}")
        col2.metric("✅ Correctas", st.session_state.score)
        col3.metric("❌ Incorrectas", st.session_state.incorrectas)

        st.subheader(q["pregunta"])
        if is_multi:
            st.caption(f"⚠️ Selecciona las {len(q['correctas'])} respuestas correctas")

        # MODO FEEDBACK
        if st.session_state.feedback_idx == idx:
            eleccion = st.session_state.answers[idx]
            correctas = q["correctas"]
            acierto = es_correcta(eleccion, q)

            if acierto:
                st.success("✅ ¡Correcto!")
            else:
                st.error("❌ Incorrecto")

            for op in opciones:
                es_c = op in correctas
                es_e = op in eleccion if isinstance(eleccion, list) else op == eleccion
                if es_c and es_e:
                    st.success(f"✅ {op}")
                elif es_c:
                    st.success(f"✅ {op} ← Respuesta correcta")
                elif es_e:
                    st.error(f"❌ {op}  ← Tu respuesta")
                else:
                    st.write(f"　{op}")

            if st.button("➡️ Siguiente pregunta"):
                st.session_state.feedback_idx = None
                st.session_state.index += 1
                if st.session_state.index >= total:
                    st.session_state.show_result = True
                st.rerun()

        # MODO NORMAL
        else:
            if is_multi:
                seleccion = []
                for op in opciones:
                    if st.checkbox(op, key=f"check_{idx}_{op}"):
                        seleccion.append(op)
                confirmar_disabled = len(seleccion) != len(q["correctas"])
                if confirmar_disabled and seleccion:
                    st.caption(f"Selecciona exactamente {len(q['correctas'])} opciones (llevas {len(seleccion)})")
                eleccion_actual = seleccion
            else:
                eleccion_actual = st.radio("Elige una opción:", opciones, key=f"q_{idx}", index=None)
                confirmar_disabled = eleccion_actual is None

            if st.button("✅ Confirmar respuesta", disabled=confirmar_disabled):
                st.session_state.answers[idx] = eleccion_actual
                st.session_state.feedback_idx = idx

                if es_correcta(eleccion_actual, q):
                    st.session_state.score += 1
                else:
                    st.session_state.incorrectas += 1

                st.rerun()

    # ─────────────────────────────────────────────
    # RESULTADOS FINALES
    # ─────────────────────────────────────────────
    elif st.session_state.show_result or idx >= total:
        score = st.session_state.score
        incorrectas_count = st.session_state.incorrectas
        pct = round(score / total * 100)

        if pct >= 70:
            st.balloons()
            st.success(f"## ✅ Aprobado — {score}/{total} ({pct}%)")
        else:
            st.error(f"## ❌ Suspenso — {score}/{total} ({pct}%)")
            st.info("Revisa las preguntas incorrectas abajo y vuelve a intentarlo 💪")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", total)
        col2.metric("✅ Correctas", score)
        col3.metric("❌ Incorrectas", incorrectas_count)

        # Botón repaso
        errores = [(i, q) for i, q in enumerate(q_list)
                   if not es_correcta(st.session_state.answers.get(i, [] if q.get("multi") else ""), q)]

        if errores:
            st.divider()
            if st.button(f"🔁 Repasar {len(errores)} preguntas incorrectas", type="primary"):
                st.session_state.repaso_mode = True
                st.session_state.repaso_list = [q for _, q in errores]
                st.session_state.repaso_index = 0
                st.session_state.repaso_answers = {}
                st.session_state.repaso_feedback_idx = None
                st.session_state.repaso_done = False
                st.rerun()

        # Tabs de repaso en pantalla
        st.divider()
        tab1, tab2 = st.tabs(["📋 Todas las respuestas", "❌ Solo errores"])

        with tab1:
            for i, q in enumerate(q_list):
                tu_resp = st.session_state.answers.get(i, [] if q.get("multi") else "—")
                acierto = es_correcta(tu_resp, q)
                icono = "✅" if acierto else "❌"
                with st.expander(f"{icono} {q['pregunta'][:80]}"):
                    if q.get("multi"):
                        st.caption("Pregunta de respuesta múltiple")
                    for op in q["opciones"]:
                        es_c = op in q["correctas"]
                        es_e = op in tu_resp if isinstance(tu_resp, list) else op == tu_resp
                        if es_c and es_e:
                            st.markdown(f"✅ **{op}** ← Correcto")
                        elif es_c:
                            st.markdown(f"✅ **{op}** ← Respuesta correcta")
                        elif es_e:
                            st.markdown(f"❌ ~~{op}~~ ← Tu respuesta")
                        else:
                            st.markdown(f"　{op}")

        with tab2:
            if not errores:
                st.success("¡Sin errores! 🎉")
            else:
                st.caption(f"{len(errores)} preguntas incorrectas")
                for i, q in errores:
                    tu_resp = st.session_state.answers.get(i, [] if q.get("multi") else "—")
                    with st.expander(f"❌ {q['pregunta'][:80]}"):
                        if q.get("multi"):
                            st.caption("Pregunta de respuesta múltiple")
                        for op in q["opciones"]:
                            es_c = op in q["correctas"]
                            es_e = op in tu_resp if isinstance(tu_resp, list) else op == tu_resp
                            if es_c and es_e:
                                st.markdown(f"✅ **{op}** ← Correcto")
                            elif es_c:
                                st.markdown(f"✅ **{op}** ← Respuesta correcta")
                            elif es_e:
                                st.markdown(f"❌ ~~{op}~~ ← Tu respuesta")
                            else:
                                st.markdown(f"　{op}")
