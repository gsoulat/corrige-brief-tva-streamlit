"""Tableau de bord TVA — Meridian Distribution. Corrigé (app.py du kit complété).

Lancement :  streamlit run app.py
La page se met à jour toute seule chaque fois que vous enregistrez ce fichier.

Complétez les TODO dans l'ordre des étapes du brief. Chaque TODO porte un nom
(par exemple « CHIFFRES ») que l'étape du brief vous indique.
ATTENTION : ils ne sont pas dans l'ordre du fichier (les étapes 3 et 6 sont en haut).
Cherchez-les avec Ctrl+F (Cmd+F sur Mac).
Ne passez à l'étape suivante que quand la vérification de l'étape en cours est bonne.
"""

import pandas as pd
import plotly.express as px  # noqa: F401 — servira aux étapes 2 et 4, ne pas supprimer
import streamlit as st

st.set_page_config(page_title="Référentiel TVA", layout="wide")


# Déjà écrit pour vous. @st.cache_data évite de relire le fichier à chaque clic.
@st.cache_data
def charger_donnees():
    df = pd.read_csv(
        "data/resultats_vies.csv", parse_dates=["date_saisie", "date_verification"]
    )
    df["etape_rejet"] = df["etape_rejet"].fillna("envoyé à VIES")
    return df


# Déjà écrit pour vous : sert à l'étape 4.
def taux_invalides(donnees, colonne):
    """Pour chaque valeur de `colonne` (chaque canal, chaque pays...), calcule la part
    de numéros invalides en %. Renvoie un tableau à deux colonnes : `colonne` et "taux d'erreur (%)"."""
    return (
        donnees.groupby(colonne)["statut"]
        .apply(lambda statuts: round((statuts == "invalide").mean() * 100, 1))
        .sort_values()
        .reset_index(name="taux d'erreur (%)")
    )


df = charger_donnees()

# =============================================================================
# ÉTAPE 3 — Les filtres (à faire APRÈS les étapes 1 et 2)
# =============================================================================
st.sidebar.header("Filtres")

# Exemple déjà écrit : le filtre pays. Une liste vide veut dire « tous les pays ».
pays = st.sidebar.multiselect("Pays déclaré", sorted(df["pays_declare"].unique()))

# CORRIGÉ — TODO FILTRE_CANAL (étape 3a)
canaux = st.sidebar.multiselect("Canal de saisie", sorted(df["source_saisie"].unique()))

# CORRIGÉ — TODO FILTRE_PERIODE (étape 3b)
debut, fin = st.sidebar.slider(
    "Période de saisie",
    min_value=df["date_saisie"].min().date(),
    max_value=df["date_saisie"].max().date(),
    value=(df["date_saisie"].min().date(), df["date_saisie"].max().date()),
    format="DD/MM/YYYY",
)

# `selection` contient les lignes qui passent les filtres. Toute la suite utilise
# `selection`, jamais `df` : c'est ce qui fait réagir la page aux filtres.
selection = df
if pays:
    selection = selection[selection["pays_declare"].isin(pays)]
# CORRIGÉ — TODO APPLIQUER_FILTRES (étape 3c)
if canaux:
    selection = selection[selection["source_saisie"].isin(canaux)]
selection = selection[selection["date_saisie"].dt.date.between(debut, fin)]

# =============================================================================
# ÉTAPE 6 — Rendre la page lisible par tous (à faire APRÈS l'étape 5)
# =============================================================================
st.title("Qualité du référentiel TVA")
# CORRIGÉ — TODO AIDE (étape 6a)
st.write(
    "Cette page montre où en sont les numéros de TVA de nos clients après la dernière vérification "
    "auprès du registre européen VIES. Utilisez les filtres à gauche pour regarder un pays, "
    "un canal de saisie ou une période : tous les chiffres et graphiques se mettent à jour."
)
# CORRIGÉ — TODO DATE_REGLE (étape 6b)
derniere = df["date_verification"].max()
st.info(f"Dernière vérification VIES : {derniere:%d/%m/%Y à %H:%M}. Règle : un numéro non tranché ne doit pas être facturé hors taxe tant qu'il n'a pas été revérifié.")

# =============================================================================
# ÉTAPE 1 — Les quatre chiffres clés
# =============================================================================
total = len(selection)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Numéros", total)
# CORRIGÉ — TODO CHIFFRES (étape 1)
valides = (selection["statut"] == "valide").sum()
col2.metric("Valides", valides, f"{valides / total:.1%} du total", delta_color="off")
invalides = (selection["statut"] == "invalide").sum()
col3.metric("Invalides", invalides, f"{invalides / total:.1%} du total", delta_color="off")
non_tranches = (selection["statut"] == "non_tranche").sum()
col4.metric("Non tranchés", non_tranches, f"{non_tranches / total:.1%} du total", delta_color="off")

# =============================================================================
# ÉTAPE 2 — L'entonnoir
# =============================================================================
st.subheader("Combien de numéros ont pu être envoyés à VIES ?")
# CORRIGÉ — TODO ENTONNOIR (étape 2)
absents = (selection["etape_rejet"] == "absent").sum()
doublons = (selection["etape_rejet"] == "doublon").sum()
structure = (selection["etape_rejet"] == "structure").sum()
entonnoir = pd.DataFrame({
    "étape": ["Référentiel", "Sans les absents", "Sans les doublons", "Envoyés à VIES"],
    "numéros": [total,
                total - absents,
                total - absents - doublons,
                total - absents - doublons - structure],
})
fig = px.funnel(entonnoir, x="numéros", y="étape",
                title="Du référentiel aux numéros envoyés à VIES")
fig.update_traces(texttemplate="%{value:d}")
st.plotly_chart(fig)
st.caption(f"Sur {total} numéros, {entonnoir['numéros'].iloc[-1]} ont été envoyés à VIES. Les autres ont été écartés avant l'envoi.")

# =============================================================================
# ÉTAPE 4 — D'où viennent les erreurs ?
# =============================================================================
st.subheader("D'où viennent les erreurs ?")
# CORRIGÉ — TODO GRAPHIQUES (étape 4)
taux = taux_invalides(selection, "source_saisie")
fig = px.bar(taux, x="taux d'erreur (%)", y="source_saisie", orientation="h",
             text="taux d'erreur (%)", title="Part de numéros invalides par canal de saisie")
st.plotly_chart(fig)

taux_pays = taux_invalides(selection, "pays_declare")
fig = px.bar(taux_pays, x="taux d'erreur (%)", y="pays_declare", orientation="h",
             text="taux d'erreur (%)", title="Part de numéros invalides par pays déclaré")
st.plotly_chart(fig)
st.caption(
    "Le canal « reprise_erp » a nettement plus de numéros invalides que les autres (environ 59 % contre 43 %). "
    "Ces numéros viennent de l'ancien logiciel de gestion : ce sont souvent des clients anciens, "
    "qui ont cessé leur activité ou changé de numéro depuis."
)

# =============================================================================
# ÉTAPE 5 — Les numéros à traiter
# =============================================================================
st.subheader("Numéros à traiter")
# CORRIGÉ — TODO A_TRAITER (étape 5)
# 1. Garder les lignes dont le statut n'est pas "valide" (!= veut dire « différent de »)
a_traiter = selection[selection["statut"] != "valide"].copy()

# 2. Ajouter une colonne "action" : .map remplace chaque statut par le texte associé
a_traiter["action"] = a_traiter["statut"].map({
    "invalide": "Demander un nouveau numéro au client",
    "non_tranche": "Revérifier sur VIES avant la prochaine facture",
})

# 3. Afficher le nombre et le tableau, avec les colonnes utiles pour la comptabilité
colonnes = ["raison_sociale", "numero_saisi", "pays_declare", "statut", "motif", "action"]
st.write(f"{len(a_traiter)} numéros demandent une action.")
st.dataframe(a_traiter[colonnes], hide_index=True)

# 4. Le bouton de téléchargement
st.download_button(
    "Télécharger la liste",
    a_traiter[colonnes].to_csv(index=False, sep=";").encode("utf-8-sig"),
    file_name="numeros_a_traiter.csv",
)

# Déjà écrit : les données brutes, cachées par défaut.
with st.expander("Voir toutes les données"):
    st.dataframe(selection, hide_index=True)
