#!/usr/bin/env python3
"""Alles Themenspezifische der taeglichen Studienauswahl — und sonst nichts.

Diese Datei ist die EINZIGE unter scripts/, die sich von Portal zu Portal
inhaltlich unterscheidet. `update_studies.py` bleibt in allen Portalen
wortgleich und importiert von hier. Wer die Auswahl aendern will, aendert
Text in dieser Datei — keinen Code.

Erzeugt von neues-portal.py aus dem Themenprofil `themen/healthliteracy.json`.
Weiterentwickelt wird danach hier, nicht im Profil.
"""
from __future__ import annotations

import os

# --------------------------------------------------------------- Kennungen
# NCBI bittet bei automatisierten Zugriffen um eine Tool-Kennung.
NCBI_TOOL = "healthliteracy-portal"

# ----------------------------------------------------------- Die Suchabfrage
# Zwei Bloecke, die BEIDE zutreffen muessen. Ohne den zweiten spuelt die Abfrage
# Arbeiten herein, die das Thema nur streifen; ohne den ersten kommt beliebige
# Versorgungsliteratur.
#
# Zur Feldwahl: [MeSH Terms] fasst breit, [Majr] verlangt das Haupt-Schlagwort,
# [Title/Abstract] fasst am breitesten, [Title] am engsten. Faustregel aus den
# Schwesterportalen: Steht ein Begriff in fremden Abstracts als blosses Werkzeug
# oder Beiwerk, ist [Title/Abstract] untauglich — dann [Majr]/[Title]. Im
# KI-Portal sank die Trefferzahl dadurch von 605.000 auf 321.000, und erst die
# kleinere Menge handelte tatsaechlich vom Thema.
#
# Vor dem Livegang die Trefferzahl in PubMed nachsehen und hier notieren, damit
# spaetere Aenderungen messbar bleiben.
_THEMA = (
    '(("Health Literacy"[Majr] OR "Patient Education as Topic"[Majr] '
    'OR "Health Communication"[Majr] OR "Consumer Health Information"[Majr] '
    'OR "Decision Making, Shared"[Majr] OR "Patient Participation"[Majr]) '
    'OR ("health literacy"[Title] OR "eHealth literacy"[Title] '
    'OR "digital health literacy"[Title] OR "patient education"[Title] '
    'OR "shared decision making"[Title] OR "health numeracy"[Title] '
    'OR "patient information"[Title] OR "informed choice"[Title] '
    'OR "risk communication"[Title]))'
)
_KONTEXT = (
    '("Delivery of Health Care"[MeSH Terms] OR "Health Services"[MeSH Terms] '
    'OR "Quality of Health Care"[MeSH Terms] OR "Patient Care"[MeSH Terms] '
    'OR "Health Policy"[MeSH Terms] OR "Public Health"[MeSH Terms] '
    'OR "health care"[Title/Abstract] OR "health services"[Title/Abstract] '
    'OR "patient outcome*"[Title/Abstract] OR "clinical practice"[Title/Abstract] '
    'OR implementation[Title/Abstract] OR patients[Title/Abstract])'
)
# "Humans"[MeSH] haelt Tier-, Labor- und reine Modellarbeiten heraus.
TERM = os.environ.get(
    "SEARCH_TERM",
    f'(({_THEMA} AND {_KONTEXT}) AND "Humans"[MeSH Terms])',
)
# Zweite Abfrage, damit Arbeiten mit Deutschland- und Europabezug den
# Kandidatenpool sicher erreichen. Ueber MeSH und Autorenadresse, nicht ueber
# Journalnamen - deutschsprachige Journale liefern kaum Treffer.
TERM_DE = os.environ.get(
    "SEARCH_TERM_DE",
    f"{TERM} AND (Germany[MeSH Terms] OR Germany[Affiliation] "
    "OR Europe[MeSH Terms] OR Europe[Affiliation])",
)

# Groesse des Kandidatenpools. Europa steht vorn und stellt die Mehrheit -
# ein Sprachmodell gewichtet, was es zuerst liest. Wer das umdreht, bekommt
# eine Auswahl ohne Bezug zu hiesigen Verhaeltnissen; im Klima-Portal ist
# genau das passiert.
POOL_EUROPA = 30
POOL_ALLGEMEIN = 25
# Welche Abfrage vorn steht. True ist der Regelfall und die Lehre aus dem
# Klima-Portal: Steht die allgemeine Abfrage vorn, kommt eine Auswahl ohne
# Bezug zu hiesigen Verhaeltnissen heraus. Das Versorgungsforschungs-Portal
# arbeitet historisch andersherum (40 allgemein + 15 deutsch) - dort steht
# hier False, damit der Anschluss an die Vorlage nichts an seiner taeglichen
# Auswahl geaendert hat. Umstellen ist eine redaktionelle Entscheidung.
EUROPA_ZUERST = True

# Wie viele Studien taeglich erscheinen. SOLL wird im Prompt verlangt und beim
# Kappen verwendet; ueber MAX wird gekappt, unter MIN bricht der Lauf ab.
# **Nicht ins JSON-Schema schreiben** - die Anthropic-API lehnt minItems > 1
# und maxItems ab (am 17.08.2026 zweimal mit HTTP 400 belegt).
ANZAHL_SOLL = 6
ANZAHL_MAX = 7
ANZAHL_MIN = 5
# True: zu viele Studien werden auf ANZAHL_SOLL gekuerzt (die Auswahl ist nach
# Relevanz geordnet, die vorderen sind brauchbar). False: zu viele lassen den
# Lauf scheitern - so hielt es das Versorgungsforschungs-Portal von Anfang an.
KAPPEN = True

# ------------------------------------------------------------------- Prompts
SYSTEM = (
    "Du bist Fachredakteur fuer Gesundheitskompetenz und Patienten-"
    "kommunikation. Aus einer Liste von PubMed-Abstracts waehlst du die "
    "relevantesten aktuellen Studien aus und fasst sie praezise auf Deutsch "
    "zusammen. Deine Leserschaft arbeitet im deutschen Gesundheitswesen: "
    "Kliniken, Praxen, Kostentraeger, Selbstverwaltung, Praevention, "
    "Patientenvertretung und Gesundheitspolitik. Sie will wissen, ob "
    "Menschen eine Information verstehen und danach handeln koennen - nicht, "
    "welches Messinstrument die beste Guetekennzahl erreicht hat."
)

USER_TEMPLATE = """Unten stehen aktuelle PubMed-Abstracts (nach Datum sortiert).

Waehle GENAU 6 Studien aus, die (a) die Gesundheitskompetenz, die Verstaendlichkeit von Gesundheitsinformation oder die Beteiligung von Patientinnen und Patienten untersuchen UND (b) im
Abstract ein BENENNBARES ERGEBNIS berichten. Bei quantitativen Arbeiten heisst
das: konkrete Zahlen (Prozentwerte, Effektstaerken, Odds/Hazard Ratios, Zeit-
oder Kostenwirkungen, Fallzahlen, p-Werte) - und die gehoeren dann auch in die
Zusammenfassung. Qualitative Studien (Interviews, Fokusgruppen) und
Expertenpapiere sind ausdruecklich zugelassen; bei ihnen tritt an die Stelle
der Zahl die klar benannte Kernaussage - welche Faktoren, welche Bedingungen,
welche Empfehlung. Was NICHT genuegt, ist ein Abstract, der nur ankuendigt,
was untersucht wurde, ohne zu sagen, was dabei herauskam.
Ueberspringe Studien ohne Abstract oder ohne benennbares Ergebnis. Achte auf
thematische Vielfalt und mische quantitative und qualitative Arbeiten.

THEMATISCHE RANGFOLGE - in dieser Reihenfolge bevorzugen:
  1. Verstehen und Handeln: Massnahmen, die nachweislich das Verstaendnis,
     die Entscheidung oder das Gesundheitsverhalten veraendert haben -
     Entscheidungshilfen, verstaendliche Materialien, Rueckfragemethode,
     Beratungsformate, Schulungen.
  2. Versorgung und Ergebnis: Wirkung auf Inanspruchnahme, Adhaerenz,
     Krankenhauseinweisungen, Notaufnahmebesuche, Kosten oder
     patientenberichtete Ergebnisse.
  3. Ungleichheit: Wer wird nicht erreicht - nach Bildung, Einkommen,
     Sprache, Alter, Behinderung - und was hilft dagegen.
  4. Organisation und System: gesundheitskompetente Einrichtungen,
     Qualitaet von Gesundheitsinformation, Patientenrechte, Beteiligung an
     Leitlinien und Entscheidungen des Systems.
  5. Bevoelkerungsdaten und Messung, sofern sie einen Handlungsbedarf
     erkennbar machen und nicht nur einen Fragebogen validieren.

NICHT in die Auswahl gehoeren:
reine Instrumentenentwicklung und Fragebogenvalidierung ohne Anwendung in der
Versorgung, Lesbarkeitsanalysen einzelner Webseiten oder Broschueren ohne
Wirkungsmessung, Querschnittsbefragungen ohne Bezugsgroesse ("X Prozent der
Befragten haben geringe Gesundheitskompetenz"), Arbeiten, die ein digitales
Werkzeug entwickeln oder technisch bewerten - die gehoeren in den KI-Hub -,
sowie Uebersichten, die nichts Eigenes berichten.

HARTE REGELN ZUR ZUSAMMENSETZUNG (sie gehen der thematischen Rangfolge vor):
  1. MINDESTENS DREI der sechs Studien muessen aus Europa stammen oder ein
     europaeisches Gesundheitssystem betreffen. Liegen weniger als drei solche
     Arbeiten vor, nimm die verbleibenden Plaetze aus dem Rest - aber schoepfe
     die europaeischen zuerst aus.
  2. HOECHSTENS EINE der sechs darf eine digitale Anwendung im Mittelpunkt
     haben (App, Portal, Chatbot, Sprachmodell). Dieses Segment waechst am
     schnellsten und wird bereits vom Schwesterportal ki.m-vf.de abgedeckt;
     ohne diese Grenze bestuende die Auswahl bald zur Haelfte aus
     Technikstudien und der Hub verloere seinen eigenen Zuschnitt. Zugelassen
     ist sie nur, wenn die Frage nach Verstaendlichkeit oder Beteiligung im
     Vordergrund steht, nicht die Technik.
  3. HOECHSTENS EINE darf ausschliesslich messen, wie es um die
     Gesundheitskompetenz einer Bevoelkerungsgruppe steht, ohne eine Massnahme
     oder eine Folge zu untersuchen.

ZWEITES AUSWAHLKRITERIUM - Übertragbarkeit auf Deutschland:
Bei sonst gleicher Qualität hat die übertragbare Studie IMMER Vorrang vor der
aktuelleren.

  Hoch:    Deutschland und deutschsprachiger Raum, vergleichbare Sozial-
           versicherungssysteme.
  Mittel:  Übriges Europa, Kanada, Australien - andere Ausgangslage,
           ähnlicher Versorgungsauftrag.
  Gering:  USA und Länder mit grundlegend anderer Finanzierung oder
           Ressourcenlage. Nur nehmen, wenn die Fragestellung davon
           unabhängig ist.

Besonderheit dieses Themenfeldes: Verstaendlichkeit haengt an Sprache,
Bildungssystem und Versorgungsstruktur. Eine US-Studie zu Materialien in
einfachem Englisch sagt wenig ueber deutsche Beipackzettel; ein
Beratungsformat aus einem Land mit Gatekeeping-Hausarztsystem laesst sich
nicht ohne Weiteres auf die freie Arztwahl uebertragen. Ordne die Systeme
nach Vergleichbarkeit: hoch bei DACH, Niederlanden, Belgien und Frankreich,
mittel bei Skandinavien, Grossbritannien, Kanada und Australien, gering bei
den USA. Nenne im Feld transfer ausdruecklich, ob die Massnahme sprach- oder
systemgebunden ist - das ist hier die haeufigste Huerde.

Fuer jede Studie:
- journal: Journalname genau so, wie er in der Kopfzeile des Abstracts steht -
  Abkuerzung nicht aufloesen, nichts ergaenzen. (Wird ohnehin durch die Angabe
  aus PubMed ersetzt; rate hier nichts.)
- year: Erscheinungsjahr, z. B. "2026"
- pmid: die PubMed-ID
- title: praegnanter deutscher Titel, **hoechstens 160 Zeichen**. Der
  Torwaechter lehnt alles ueber 200 Zeichen ab und stoppt damit die ganze
  Ausgabe - Methode und Population gehoeren nicht in den Titel, sie stehen
  in sum und transfer.
  **Er MUSS mit der Frage nach Verstaendnis, Information oder Beteiligung
  beginnen, nicht mit der Erkrankung, an der sie untersucht wurde.** Fast
  jede Arbeit haengt an einem klinischen Traegerfall - Diabetes, Krebs,
  Schwangerschaft -, und die Abstracts sind danach betitelt. Uebernimmt der
  Titel das, liest sich der Hub wie eine beliebige klinische Sammlung. Nicht
  "Diabetes-Schulung in der Hausarztpraxis: ...", sondern
  "Verstaendliche Schulungsmaterialien senken ...".
- sum: 1 Satz auf Deutsch, was die Studie untersucht hat. Wenn der genannte
  Anlassfall nur das Material ist, an dem gerechnet wurde, sage das
  ausdruecklich - sonst haelt die Leserschaft ihn fuer den Gegenstand.
- result: Deutsch, die konkreten Zahlen/Befunde + ein kurzer Einordnungssatz.
  Deutsches Zahlenformat mit Komma (z. B. 0,63). **Der Einordnungssatz darf
  nicht behaupten, was die Autoren selbst ablehnen.** Wo ein Abstract eine
  Deutung ausdruecklich zurueckweist, diese Einschraenkung uebernehmen statt
  sie zu ueberschreiben. Ein Rechercheportal referiert, es wertet nicht auf.
- transfer: EIN Halbsatz (höchstens 12 Wörter), warum das Ergebnis für Deutschland
  taugt - oder wo die Grenze liegt. Nenne Land bzw. System und Datengrundlage.
  Keine ganzen Sätze, keine Wiederholung des Titels.
  Gut:      "Deutsche Klinikdaten, vergleichbare Dokumentationspflichten"
            "Niederlande, vergleichbares Versicherungssystem"
            "USA - nur der Sicherheitsbefund ist übertragbar"
  Schlecht: "Diese Studie ist gut übertragbar." (sagt nichts)

WICHTIG - Fachterminologie: Etablierte englische Fachbegriffe NICHT eindeutschen.
Sie sind auch im deutschen Fachdeutsch stehende Begriffe; eine woertliche
Uebersetzung wirkt unprofessionell und erschwert das Wiederfinden.
Beispiele fuer Begriffe, die englisch bleiben: Health Literacy (neben
Gesundheitskompetenz), Teach-Back, Shared Decision Making, Empowerment,
Plain Language, Numeracy. Uebersetze dagegen, was im Deutschen eine gaengige
Entsprechung hat: aus "decision aid" wird Entscheidungshilfe, aus
"informed consent" die Einwilligung nach Aufklaerung, aus "readability"
die Lesbarkeit.
Faustregel: Wuerde eine deutsche Fachzeitschrift wie Monitor Versorgungsforschung
den Begriff englisch stehen lassen, dann tue es auch. Im Zweifel englisch
belassen und bei Bedarf eine kurze deutsche Erlaeuterung in Klammern ergaenzen.

Gib ausschliesslich das geforderte JSON zurueck.

=== ABSTRACTS ===
{abstracts}
"""
