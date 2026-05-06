"""
FinancialProof — Erststart-Acknowledgement (Streamlit).

Umsetzung der dringenden Empfehlung aus dem Rechtsaudit (§ 32 KWG /
§ 2 Abs. 9 WpHG). Vor der Nutzung der App muss der Anwender einmalig
bestätigen, dass er

  1. verstanden hat, dass das Tool KEINE Anlageberatung ist,
  2. verstanden hat, dass angezeigte Indikatoren historische
     statistische Muster sind (keine Prognosen),
  3. Anlageentscheidungen auf eigene Verantwortung trifft und sich mit
     qualifizierten Fachleuten abstimmt,
  4. das Tool auf eigenes Risiko nutzt (§ 521 BGB).

Persistenz:
  * ``st.session_state["disclaimer_accepted"]`` — aktuelle Session
  * ``data/.disclaimer_acceptance.json`` — dauerhaft über Sessions
    hinweg, mit SHA-256-Hash des bestätigten Disclaimer-Textes.
    Bei Textänderung (neuer Hash) wird erneut bestätigt.

Vorbild: ``verordnungsampel/gui/disclaimer_dialog.py`` (PySide6-Variante).
Hier: Streamlit-Block vor der Haupt-UI, gesteuert durch
``ensure_acknowledged()``, der ``st.stop()`` ruft, wenn noch nicht
akzeptiert oder wenn der Anwender ablehnt.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import streamlit as st

from config import config, texts


# ---------------------------------------------------------------------------
# Persistenz-Layer (Datei-basiert, App-weit)
# ---------------------------------------------------------------------------

_ACCEPTANCE_FILE = config.DATA_DIR / ".disclaimer_acceptance.json"


def _build_disclaimer_text() -> str:
    """Baut den exakten Disclaimer-Text, der dem Nutzer angezeigt wird.

    Aus diesem Text wird der Hash gebildet. Jede Änderung am Text
    (Intro, Body oder einer der vier Checkboxen) erzwingt automatisch
    eine erneute Bestätigung durch den Anwender — weil sich der Hash
    ändert.
    """
    parts = [
        f"VERSION: {texts.DISCLAIMER_VERSION}",
        texts.DISCLAIMER_INTRO,
        texts.DISCLAIMER_BODY,
        texts.DISCLAIMER_CHECK_NO_ADVICE,
        texts.DISCLAIMER_CHECK_HISTORICAL,
        texts.DISCLAIMER_CHECK_OWN_RESPONSIBILITY,
        texts.DISCLAIMER_CHECK_OWN_RISK,
    ]
    return "\n\n".join(parts)


def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_acceptance() -> Optional[dict]:
    if not _ACCEPTANCE_FILE.is_file():
        return None
    try:
        return json.loads(_ACCEPTANCE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _save_acceptance(record: dict) -> None:
    try:
        _ACCEPTANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _ACCEPTANCE_FILE.write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        # Defensive: bei Schreibfehler bleibt die Session-Bestätigung,
        # beim nächsten Start wird neu gefragt.
        pass


def _persisted_acceptance_valid(current_hash: str) -> bool:
    record = _load_acceptance()
    if not record:
        return False
    if record.get("disclaimer_hash") != current_hash:
        return False
    if not record.get("accepted_at"):
        return False
    return True


# ---------------------------------------------------------------------------
# Streamlit-Block
# ---------------------------------------------------------------------------


def _render_acknowledgement_screen(current_text: str, current_hash: str) -> None:
    """Rendert den Vollscreen-Block. Ruft ``st.stop()`` am Ende.

    Hinweis: ``st.set_page_config`` wird hier NICHT gerufen — das
    passiert in ``app.py`` ganz am Anfang (Streamlit erlaubt genau
    einen Aufruf pro Run).
    """
    st.title("⚠️ " + texts.DISCLAIMER_TITLE)
    st.markdown(
        "> **No Financial Advice.** FinancialProof is a technical tool "
        "for historical statistical pattern analysis. It is NOT "
        "investment advice, NOT a buy/sell recommendation, and NOT a "
        "forecast. Please confirm the four points below."
    )

    st.info(texts.DISCLAIMER_INTRO)

    with st.container(border=True):
        st.markdown("### Haftungshinweis im Wortlaut")
        st.text_area(
            label="Disclaimer-Text",
            value=texts.DISCLAIMER_BODY,
            height=320,
            disabled=True,
            label_visibility="collapsed",
        )

    st.markdown("### Pflicht-Bestätigungen")

    cb1 = st.checkbox(
        texts.DISCLAIMER_CHECK_NO_ADVICE,
        key="_disclaimer_cb_no_advice",
    )
    cb2 = st.checkbox(
        texts.DISCLAIMER_CHECK_HISTORICAL,
        key="_disclaimer_cb_historical",
    )
    cb3 = st.checkbox(
        texts.DISCLAIMER_CHECK_OWN_RESPONSIBILITY,
        key="_disclaimer_cb_own_responsibility",
    )
    cb4 = st.checkbox(
        texts.DISCLAIMER_CHECK_OWN_RISK,
        key="_disclaimer_cb_own_risk",
    )

    st.caption(texts.DISCLAIMER_INFO_BUTTONS)

    all_checked = cb1 and cb2 and cb3 and cb4

    col_reject, col_spacer, col_accept = st.columns([1, 2, 1])
    with col_reject:
        rejected = st.button(
            texts.DISCLAIMER_BTN_REJECT,
            width="stretch",
            key="_disclaimer_reject",
        )
    with col_accept:
        accepted = st.button(
            texts.DISCLAIMER_BTN_ACCEPT,
            type="primary",
            disabled=not all_checked,
            width="stretch",
            key="_disclaimer_accept",
        )

    if rejected:
        # Hinweis anzeigen und hart stoppen.
        st.error(texts.DISCLAIMER_REJECTED)
        st.stop()

    if accepted and all_checked:
        record = {
            "disclaimer_version": texts.DISCLAIMER_VERSION,
            "disclaimer_hash": current_hash,
            "accepted_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
            "acknowledged_labels": [
                texts.DISCLAIMER_CHECK_NO_ADVICE,
                texts.DISCLAIMER_CHECK_HISTORICAL,
                texts.DISCLAIMER_CHECK_OWN_RESPONSIBILITY,
                texts.DISCLAIMER_CHECK_OWN_RISK,
            ],
        }
        _save_acceptance(record)
        st.session_state["disclaimer_accepted"] = True
        st.session_state["disclaimer_hash"] = current_hash
        st.rerun()

    # Solange nicht akzeptiert/abgelehnt: Haupt-UI nicht laden.
    st.stop()


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def ensure_acknowledged() -> None:
    """Hauptfunktion: vor dem Rendern der App aufrufen.

    Semantik:
      * Prüft zuerst die Session (``st.session_state``).
      * Fällt zurück auf die dauerhafte Datei-Persistenz — und
        akzeptiert NUR, wenn der Hash des aktuellen Disclaimer-Textes
        mit dem gespeicherten Hash übereinstimmt.
      * Ansonsten: blockiert die App via ``st.stop()`` und zeigt den
        Acknowledgement-Block.
    """
    current_text = _build_disclaimer_text()
    current_hash = _compute_hash(current_text)

    # Session-Cache
    if (
        st.session_state.get("disclaimer_accepted") is True
        and st.session_state.get("disclaimer_hash") == current_hash
    ):
        return

    # Datei-Persistenz (über Sessions hinweg)
    if _persisted_acceptance_valid(current_hash):
        st.session_state["disclaimer_accepted"] = True
        st.session_state["disclaimer_hash"] = current_hash
        return

    # Nicht akzeptiert — Block rendern und stoppen.
    _render_acknowledgement_screen(current_text, current_hash)


__all__ = [
    "ensure_acknowledged",
]
