import os
import base64
import re
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Landing Generator", layout="wide")
st.title("Landing Page Generator (from Product Image)")

# --- Load OpenAI key from Streamlit secrets or env ---
api_key = None
if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
elif os.environ.get("OPENAI_API_KEY"):
    api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    st.warning("OpenAI key missing. Add OPENAI_API_KEY in Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- UI ---
c1, c2 = st.columns([1, 1])

with c1:
    img_file = st.file_uploader("Upload product image", type=["png", "jpg", "jpeg", "webp"])
    brand = st.text_input("Brand / Store name", value="Pitiendas")
    product_hint = st.text_input("Product name hint (optional)", value="")
    language = st.selectbox("Language", ["English", "Français", "Español", "Arabic"], index=0)
    tone = st.selectbox("Tone", ["Direct-response", "Premium", "Minimal", "Playful"], index=0)

with c2:
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "MAD"], index=0)
    price = st.number_input("Price", min_value=0.0, value=49.99, step=1.0)
    apply_discount = st.checkbox("Apply -20% discount", value=True)
    shipping_line = st.text_input("Shipping line", value="Free shipping • 2–5 business days")
    cta = st.text_input("CTA button text", value="Buy Now")

model = st.text_input("Model", value="gpt-4.1-mini")

def to_data_url(uploaded_file):
    b = uploaded_file.getvalue()
    mime = uploaded_file.type or "image/jpeg"
    enc = base64.b64encode(b).decode("utf-8")
    return f"data:{mime};base64,{enc}"

def discounted_price(p: float) -> float:
    return round(p * 0.8, 2)

data_url = to_data_url(img_file) if img_file else None
final_price = discounted_price(price) if apply_discount else round(price, 2)

if img_file:
    st.image(img_file, caption="Uploaded image", use_container_width=True)

SYSTEM = """You are a world-class direct-response ecommerce landing page designer.
Return ONLY valid HTML (no markdown). Use inline CSS inside <style>.
Mobile-first. No external assets, no external fonts, no scripts.
"""

def user_prompt():
    return f"""
Create a single-page ecommerce landing page as HTML with inline CSS.
Language: {language}
Tone: {tone}
Brand/store: {brand}
Product name hint: {product_hint}

Offer:
- Price: {final_price} {currency}
- Shipping: {shipping_line}
- CTA text: {cta}

Layout order:
1) Sticky top bar with offer + CTA
2) Hero (headline, subheadline, hero image, price, CTA, trust bullets)
3) Problem → solution
4) Key benefits (3–6 bullets)
5) How it works (3 steps)
6) Social proof (3 short reviews, realistic)
7) FAQ (5 items)
8) Final CTA block
9) Footer (policy placeholders)

Rules:
- No medical claims, no guaranteed results, no extreme promises.
- Copy must match what you see in the product image.
- Use clean spacing, cards, and big readable typography.
Return ONLY HTML.
"""

def inject_first_img_src(html_text: str, src_value: str) -> str:
    pattern = r'(<img\\b[^>]*\\bsrc=")([^"]*)(")'
    return re.sub(pattern, r'\\1' + src_value + r'\\3', html_text, count=1)

if st.button("Generate landing page", type="primary", disabled=(data_url is None)):
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM}]},
            {"role": "user", "content": [
                {"type": "input_text", "text": user_prompt()},
                {"type": "input_image", "image_url": data_url},
            ]},
        ],
    )
    html = resp.output_text.strip()
    html = inject_first_img_src(html, data_url)

    st.subheader("Preview")
    st.components.v1.html(html, height=900, scrolling=True)

    st.subheader("HTML")
    st.code(html, language="html")

    st.download_button(
        "Download landing.html",
        data=html.encode("utf-8"),
        file_name="landing.html",
        mime="text/html",
    )