import os, tempfile, pathlib, math, re
import streamlit as st
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, TextClip
from moviepy.audio.fx.all import audio_loop

st.set_page_config(page_title="MontageAI Studio", page_icon="🎬", layout="wide")

MODELS = {
"Breaking / Actualité":"Rythme rapide, gros titres et changements fréquents.",
"Analyse football":"Stats, joueurs, tableaux et rythme analytique.",
"Storytelling":"Narration fluide, zooms et rythme cinématique.",
"Débat / Opinion":"Phrases fortes, emphase et transitions rapides.",
"Histoire / Documentaire":"Rythme posé et transitions cinématiques.",
"Classement / Top":"Numéros, cartes et changements rapides.",
"News / Transfert":"Style alerte, informations courtes et visuels rapides."
}

def vertical(c,w=1080,h=1920):
    r=max(w/c.w,h/c.h); c=c.resize(r)
    return c.crop(x1=(c.w-w)/2,y1=(c.h-h)/2,x2=(c.w+w)/2,y2=(c.h+h)/2)

def visual(path,d):
    ext=pathlib.Path(path).suffix.lower()
    if ext in [".mp4",".mov",".mkv",".webm"]:
        c=VideoFileClip(path).without_audio()
        if c.duration >= d: c=c.subclip(0,d)
        else: c=concatenate_videoclips([c]*math.ceil(d/c.duration)).subclip(0,d)
    else: c=ImageClip(path).set_duration(d)
    return vertical(c).set_duration(d)

def render(files,audio_path,title,out):
    audio=AudioFileClip(audio_path)
    total=audio.duration
    slot=total/len(files)
    base=concatenate_videoclips([visual(p,slot) for p in files],method="compose")
    layers=[base]
    if title:
        try:
            t=TextClip(title,fontsize=62,color="white",font="DejaVu-Sans-Bold",
                       method="caption",size=(920,None),align="center")
            layers.append(t.set_duration(min(4,total)).set_position(("center",1450)))
        except Exception: pass
    final=CompositeVideoClip(layers,size=(1080,1920)).set_audio(audio)
    final.write_videofile(out,fps=30,codec="libx264",audio_codec="aac",preset="medium",logger=None)
    final.close(); audio.close()

st.markdown("""<style>
.block-container{max-width:1180px;padding-top:2rem}
.hero{padding:28px;border-radius:24px;background:linear-gradient(135deg,#111827,#202938);color:white;margin-bottom:20px}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🎬 MontageAI Studio</h1><p>Assistant de montage vidéo vertical — prototype amélioré.</p></div>',unsafe_allow_html=True)

tab1,tab2,tab3,tab4=st.tabs(["🚀 Créer","🎙️ Voix IA","🔎 Sources","ℹ️ État"])

with tab1:
    c1,c2=st.columns(2)
    with c1:
        script=st.text_area("Script / sujet",height=150,placeholder="Colle ton script…")
        files=st.file_uploader("📁 Visuels",type=["png","jpg","jpeg","webp","mp4","mov","mkv","webm"],accept_multiple_files=True)
        source=st.radio("Source",["Mes fichiers","Recherche IA","Mix automatique"],horizontal=True)
        link=st.text_input("🔗 Lien de référence",placeholder="Colle une URL de contenu public que tu as le droit d'utiliser…")
        st.caption("L'application n'essaie pas de contourner les restrictions ou protections des plateformes.")
        audio=st.file_uploader("🎙️ Voix off existante",type=["mp3","wav","m4a"])
    with c2:
        auto=st.checkbox("🤖 Recommander le modèle",True)
        manual=st.selectbox("Modèle",list(MODELS))
        personality=st.selectbox("Personnalité",["Énergique","Sérieuse","Dramatique","Calme","Humoristique","Breaking News"])
        title=st.text_input("Titre à l'écran")
        subtitle=st.checkbox("Sous-titres automatiques",True)
        if auto:
            s=(script or "").lower()
            if any(x in s for x in ["transfert","mercato","here we go","signé"]): model="News / Transfert"
            elif any(x in s for x in ["top","classement","meilleur","numéro"]): model="Classement / Top"
            elif any(x in s for x in ["stat","xg","possession","tirs"]): model="Analyse football"
            elif any(x in s for x in ["histoire","pourquoi","depuis","avant"]): model="Histoire / Documentaire"
            else: model="Storytelling"
        else: model=manual
        st.success("Modèle choisi : "+model)

    if st.button("🎬 Générer l'aperçu",type="primary",use_container_width=True):
        if not files or not audio:
            st.error("Pour ce prototype, ajoute au moins un visuel et une voix off.")
        else:
            work=tempfile.mkdtemp(prefix="montageai_"); paths=[]
            for f in files:
                p=os.path.join(work,f.name)
                with open(p,"wb") as o:o.write(f.getbuffer())
                paths.append(p)
            ap=os.path.join(work,audio.name)
            with open(ap,"wb") as o:o.write(audio.getbuffer())
            out=os.path.join(work,"preview.mp4")
            with st.spinner("Création de l'aperçu…"):
                render(paths,ap,title,out)
            st.session_state.preview=out
            st.session_state.model=model
            st.session_state.source=source
            st.session_state.subtitle=subtitle
    if st.session_state.get("preview"):
        st.divider(); st.subheader("👁️ Aperçu avant export")
        st.video(st.session_state.preview)
        st.success("Aperçu généré. Tu peux le vérifier avant export.")

with tab2:
    st.subheader("Voix off IA")
    st.info("Le branchement TTS est prévu par API sécurisée. Aucun fournisseur ni clé n'est inclus dans le projet.")
    tts_text=st.text_area("Texte à transformer en voix",height=130)
    voice=st.selectbox("Style",["Énergique","Sérieux","Dramatique","Calme","Breaking News"])
    st.caption("Pour produire réellement l'audio, ajoute une clé d'un service TTS compatible dans les secrets du déploiement. Les clés ne doivent jamais être placées dans le code.")

with tab3:
    st.subheader("Analyse de sources")
    st.write("URL reçue :", link if 'link' in locals() and link else "Aucune")
    st.write("Mode :", source if 'source' in locals() else "Mes fichiers")
    st.info("La version distribuée prépare l'interface. L'extraction automatique d'une plateforme doit utiliser ses API/permissions officielles ou une source dont tu as les droits.")

with tab4:
    st.subheader("Ce qui est réellement intégré")
    st.markdown("""
- ✅ Interface web
- ✅ 7 modèles
- ✅ Sélection automatique du modèle
- ✅ Import multiple de visuels
- ✅ Import de voix
- ✅ Montage vertical 1080×1920
- ✅ Aperçu vidéo
- ✅ Choix de personnalité
- 🧩 Sous-titres : interface prête, moteur de transcription à connecter
- 🧩 TTS : interface prête, fournisseur/API à connecter
- 🧩 Recherche de visuels : interface prête, fournisseur/API à connecter
- 🧩 Analyse de liens : interface prête, dépend des API/permissions de la plateforme
""")
