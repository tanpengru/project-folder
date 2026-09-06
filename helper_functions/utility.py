import streamlit as st
import hmac
import hashlib

from PyPDF2 import PdfReader


# ============================================================
# 🔐 PASSWORD AUTHENTICATION
# ============================================================

def _get_password_version():
    """
    Create a non-reversible fingerprint of the current password.

    This lets the app detect when the configured password has
    changed without storing the password itself in session state.
    """

    configured_password = str(
        st.secrets.get("password", "")
    )

    return hashlib.sha256(
        configured_password.encode("utf-8")
    ).hexdigest()


def check_password():
    """
    Returns True if the user entered the correct password.

    Existing authenticated sessions are automatically invalidated
    if the password in Streamlit Secrets is changed.
    """

    configured_password = str(
        st.secrets.get("password", "")
    )

    # --------------------------------------------------------
    # Make sure a password has actually been configured
    # --------------------------------------------------------

    if not configured_password:
        st.error(
            "Application password has not been configured "
            "in Streamlit Secrets."
        )
        return False

    current_password_version = _get_password_version()

    # --------------------------------------------------------
    # Invalidate old login sessions if password changed
    # --------------------------------------------------------

    authenticated_version = st.session_state.get(
        "authenticated_password_version"
    )

    if (
        st.session_state.get("password_correct", False)
        and authenticated_version != current_password_version
    ):
        st.session_state["password_correct"] = False
        st.session_state.pop(
            "authenticated_password_version",
            None
        )

    # --------------------------------------------------------
    # Check entered password
    # --------------------------------------------------------

    def password_entered():
        """
        Validate the password entered by the user.
        """

        entered_password = str(
            st.session_state.get("password", "")
        )

        if hmac.compare_digest(
            entered_password,
            configured_password
        ):
            st.session_state["password_correct"] = True

            # Store only the fingerprint, not the password.
            st.session_state[
                "authenticated_password_version"
            ] = current_password_version

        else:
            st.session_state["password_correct"] = False
            st.session_state.pop(
                "authenticated_password_version",
                None
            )

        # Never retain the entered password.
        st.session_state.pop(
            "password",
            None
        )

    # --------------------------------------------------------
    # Already authenticated with CURRENT configured password
    # --------------------------------------------------------

    if (
        st.session_state.get("password_correct", False)
        and st.session_state.get(
            "authenticated_password_version"
        ) == current_password_version
    ):
        return True

    # --------------------------------------------------------
    # Login input
    # --------------------------------------------------------

    st.text_input(
        "Password",
        type="password",
        on_change=password_entered,
        key="password"
    )

    if (
        "password_correct" in st.session_state
        and not st.session_state["password_correct"]
    ):
        st.error("😕 Password incorrect")

    return False


# ============================================================
# 📄 PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(file):
    """
    Extract text from a PDF using PyPDF2.
    """

    reader = PdfReader(file)

    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text() or ""

        if page_text.strip():
            text_parts.append(
                page_text.strip()
            )

    return "\n\n".join(text_parts).strip()