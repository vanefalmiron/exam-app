import streamlit as st
import random
from parser import parse_exam

st.set_page_config(page_title="Examen", page_icon="📝")
st.title("📝 Práctica de examen")

# --- Subida del archivo ---
uploaded = st.file_uploader("Sube tu archivo Word (.docx)", type="docx")

if uploaded:
    questions = parse_exam(uploaded)

    if not questions:
        st.error("No se encontraron preguntas. Revisa el formato del Word.")
        st.stop()

    # Inicializar sesión
    if "questions" not in st.session_state or st.sidebar.button("🔄 Reiniciar examen"):
        shuffled = questions.copy()
        random.shuffle(shuffled)
        st.session_state.questions = shuffled
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.answers = {}

    q_list = st.session_state.questions
    idx = st.session_state.index
    total = len(q_list)

    # --- Progreso ---
    st.progress(idx / total)
    st.caption(f"Pregunta {idx + 1} de {total}")

    if idx < total:
        q = q_list[idx]
        st.subheader(q["pregunta"])

        opciones = q["opciones"].copy()
        random.seed(q["pregunta"])  # seed fija para no mezclar en cada render
        random.shuffle(opciones)

        eleccion = st.radio("Elige una opción:", opciones, key=f"q_{idx}", index=None)

        if st.button("Confirmar respuesta", disabled=eleccion is None):
            correcta = q["correcta"]
            st.session_state.answers[idx] = eleccion

            if eleccion == correcta:
                st.session_state.score += 1
                st.success("✅ ¡Correcto!")
            else:
                st.error(f"❌ Incorrecto. La respuesta era: **{correcta}**")

            st.session_state.index += 1
            st.rerun()

    else:
        # --- Resultados finales ---
        score = st.session_state.score
        pct = round(score / total * 100)
        st.balloons()
        st.header(f"Resultado: {score}/{total} — {pct}%")

        if pct >= 70:
            st.success("¡Aprobado! 🎉")
        else:
            st.warning("Sigue practicando 💪")

        # Repaso de errores
        st.divider()
        st.subheader("📋 Repaso de respuestas")
        for i, q in enumerate(q_list):
            with st.expander(q["pregunta"]):
                st.write(f"✅ Correcta: **{q['correcta']}**")
                tu_resp = st.session_state.answers.get(i, "—")
                if tu_resp == q["correcta"]:
                    st.write(f"Tu respuesta: ✅ {tu_resp}")
                else:
                    st.write(f"Tu respuesta: ❌ {tu_resp}")
