import streamlit as st
import anthropic
import base64
import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kill the Bill",
    page_icon="🧾",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; color: #111; }

.stApp { background: #f7f7f5; color: #111; }

.hero { text-align:center; padding: 2rem 0 1rem; }
.hero h1 { font-size: 3rem; font-weight: 800; color: #111;
            letter-spacing: -1px; margin-bottom: 0.2rem; }
.hero .sub { color: #666; font-size: 1.05rem; }

.card { background:#fff; border:1px solid #e0e0e0; border-radius:16px;
        padding:1.5rem; margin-bottom:1rem; }

.item-row { display:flex; justify-content:space-between; align-items:center;
            padding: 0.5rem 0; border-bottom: 1px solid #eee; }
.item-row:last-child { border-bottom: none; }
.item-name { font-weight: 500; color: #111; }
.item-desc { font-size: 0.8rem; color: #888; }
.item-price { color: #1a7a3f; font-weight: 600; font-variant-numeric: tabular-nums; }

.person-total { display:flex; justify-content:space-between;
                padding: 0.6rem 0.8rem; background:#f0f7f3;
                border: 1px solid #d4eadd;
                border-radius:10px; margin-bottom:0.4rem; }
.person-name { font-weight:600; color: #111; }
.person-amt  { color:#1a7a3f; font-weight:700; }

.stButton>button {
    background: #111; color: #fff; border: none;
    border-radius: 10px; font-weight: 700; font-family: 'Syne', sans-serif;
    font-size: 1rem; padding: 0.6rem 1.8rem;
    transition: transform 0.15s, box-shadow 0.15s;
}
.stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px #0003; }

.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background: #fff; border: 1px solid #ddd; color: #111;
    border-radius: 10px;
}

[data-testid="stFileUploaderDropzone"] {
    background: #fff; border: 1.5px dashed #ccc; border-radius: 12px;
}
[data-testid="stFileUploaderDropzoneInstructions"] { color: #555; }
[data-testid="stFileUploaderDropzone"] svg { fill: #888; }
[data-testid="stFileUploaderDropzone"] button {
    background: #111; color: #fff; border: none;
    border-radius: 8px; font-weight: 700;
}
[data-testid="stFileUploaderDropzone"] button:hover { background: #333; }
[data-testid="stFileUploaderFile"] { background: #fff; color: #111; }
[data-testid="stFileUploaderFile"] svg { fill: #888; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🧾 Kill the Bill</h1>
  <p class="sub">Upload a receipt · Tell Claude who ate what · Done</p>
</div>
""", unsafe_allow_html=True)

# ── API key ──────────────────────────────────────────────────────────────────
try:
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
except Exception:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
if not api_key:
    api_key = st.text_input("🔑 Anthropic API key", type="password",
                             placeholder="sk-ant-...")
if not api_key:
    st.info("Enter your Anthropic API key to get started.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# ── Helpers ──────────────────────────────────────────────────────────────────
def parse_receipt_image(image_bytes: bytes, media_type: str) -> dict:
    b64 = base64.b64encode(image_bytes).decode()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                                              "media_type": media_type,
                                              "data": b64}},
                {"type": "text", "text": """Extract the receipt data from this image.

Return raw JSON only.
Do not use markdown.
Do not wrap the answer in ```json.

Use exactly this format:

{
  "merchant": "",
  "date": "",
  "currency": "",
  "items": [
    {
      "name": "",
      "description": "",
      "quantity": 1,
      "unit_price": 0.0,
      "total_price": 0.0
    }
  ],
  "subtotal": 0.0,
  "tax": 0.0,
  "total": 0.0
}

Rules for item naming:
- If the receipt item is already in English:
  - "name" must stay in the original receipt wording.
- If the receipt item is not in English:
  - "name" must keep the original receipt text and append a simple Latin transliteration in parentheses.
  - Format: "Original Text (Reading)"
  - Example: "დეკანტერო (Dekantero)"

"description" must be short, simple, generic, and useful for splitting a bill.
It should help a normal user distinguish items from each other.
Describe the most recognizable distinguishing trait of the item, such as:
- category (drink, dessert, side, household item)
- main type (sandwich, soup, pastry, medicine)
- key ingredient (cheese, vegetable, seafood)
- preparation style (fried, grilled, iced, sparkling)
- flavor/style (spicy, sweet, dark roast)

Good examples: "sparkling water", "iced coffee", "vegetable soup", "seafood pasta", "cheese pastry", "spicy sauce", "chocolate dessert", "potato side"
Bad examples: "food", "dish", "item", "meal", "drink"

Keep descriptions broad, human-friendly, and no longer than a few words.
Do not simply repeat the full item name unless necessary."""}
            ]
        }]
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise RuntimeError(
            f"Claude returned no text (stop_reason={response.stop_reason}); "
            "try again or increase max_tokens"
        )
    text = text_blocks[0].strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").removesuffix("```").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def split_bill_from_item_assignments(receipt: dict, item_assignments: dict) -> dict:
    items = [item for item in receipt["items"] if float(item.get("total_price", 0)) > 0]
    all_people = set()
    for people in item_assignments.values():
        all_people.update(people)

    totals = {p: 0.0 for p in all_people}
    details = {p: [] for p in all_people}

    for idx, assigned_people in item_assignments.items():
        if not assigned_people:
            continue
        item = items[idx]
        name = item["name"]
        quantity = float(item.get("quantity", 1))
        total_price = float(item["total_price"])
        share_amount = total_price / len(assigned_people)
        share_quantity = quantity / len(assigned_people)
        for p in assigned_people:
            totals[p] += share_amount
            details[p].append({
                "item": name,
                "quantity": round(share_quantity, 2),
                "amount": round(share_amount, 2),
            })

    return {
        p: {"total": round(totals[p], 2), "items": details[p]}
        for p in all_people
    }


# ── State ────────────────────────────────────────────────────────────────────
if "receipt" not in st.session_state:
    st.session_state.receipt = None
if "split_result" not in st.session_state:
    st.session_state.split_result = None

# ── Step 1: Upload receipt ───────────────────────────────────────────────────
st.markdown("### Step 1 · Upload receipt")
uploaded = st.file_uploader("Photo of your receipt", type=["jpg","jpeg","png","webp"])

if uploaded and st.session_state.receipt is None:
    with st.spinner("Claude is reading your receipt…"):
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        mime = {"jpg":"image/jpeg","jpeg":"image/jpeg",
                "png":"image/png","webp":"image/webp"}[ext]
        try:
            st.session_state.receipt = parse_receipt_image(uploaded.read(), mime)
            st.session_state.split_result = None
        except Exception as e:
            st.error(f"Could not parse receipt: {e}")

if st.session_state.receipt:
    r = st.session_state.receipt
    paid_items_display = [it for it in r["items"] if float(it.get("total_price", 0)) > 0]
    items_total = sum(float(it["total_price"]) for it in paid_items_display)

    st.markdown(f'<div class="card"><strong>{r.get("merchant","Receipt")}</strong>'
                f'<span style="float:right;color:#888">{r.get("date","")}</span>', unsafe_allow_html=True)
    for it in paid_items_display:
        st.markdown(f"""
        <div class="item-row">
          <div><div class="item-name">{it['name']}</div>
               <div class="item-desc">{it.get('description','')}</div></div>
          <div class="item-price">{r.get('currency','$')}{float(it['total_price']):.2f}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:right;padding-top:0.8rem">
      <strong>Total: {r.get('currency','$')}{items_total:.2f}</strong>
    </div></div>""", unsafe_allow_html=True)

    if st.button("🔄 Scan a different receipt"):
        st.session_state.receipt = None
        st.session_state.split_result = None
        st.rerun()

    # ── Step 2a: Who was there? ──────────────────────────────────────────────
    st.markdown("### Step 2 · Who was there?")
    num_people = st.number_input("Number of people", min_value=2, max_value=10, value=2)

    names = []
    name_cols = st.columns(int(num_people))
    for i in range(int(num_people)):
        n = name_cols[i].text_input(f"Person {i+1}", key=f"name_{i}",
                                     placeholder=f"e.g. Alice")
        if n:
            names.append(n)

    # ── Step 2b: Per item — who ate it? ─────────────────────────────────────
    if names:
        st.markdown("### Step 3 · Who ate each item?")
        st.caption("Tick who ate each item. Items split equally among ticked people.")

        paid_items_list = [it for it in r["items"] if float(it.get("total_price", 0)) > 0]

        # Build initial dataframe: rows = items, columns = people (bool)

        row_labels = [
            f"{it['name']} · {it.get('description','')}"
            for it in paid_items_list
        ]
        data = {"💰 Line Total": [f"{r.get('currency','$')}{float(it['total_price']):.2f}" for it in paid_items_list]}
        data.update({name: [False] * len(paid_items_list) for name in names})
        df = pd.DataFrame(data, index=row_labels)

        edited = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "💰 Line Total": st.column_config.TextColumn("💰 Line Total", disabled=True, width="small"),
                **{name: st.column_config.CheckboxColumn(name, width="small") for name in names}
            },
            disabled=["💰 Line Total"],
            hide_index=False,
            key="assignment_table",
        )

        # Convert edited df back to item_assignments dict
        item_assignments = {}
        for idx in range(len(paid_items_list)):
            selected = [name for name in names if edited.iloc[idx][name]]
            item_assignments[idx] = selected

        all_assigned = all(len(v) > 0 for v in item_assignments.values())
        if not all_assigned:
            st.warning("Tick at least one person for every item before splitting.")

        if all_assigned and st.button("✨ Split the bill"):
            try:
                st.session_state.split_result = split_bill_from_item_assignments(r, item_assignments)
            except Exception as e:
                st.error(f"Split failed: {e}")

    # ── Step 4: Final review ─────────────────────────────────────────────────
    if st.session_state.split_result:
        st.markdown("### Step 4 · Final Review")
        result = st.session_state.split_result
        r = st.session_state.receipt
        grand_total = sum(info["total"] for info in result.values())

        # Per-person breakdown like review_split()
        for person, info in sorted(result.items(), key=lambda x: -x[1]["total"]):
            amount = info["total"]
            st.markdown(f"""
            <div class="person-total">
              <span class="person-name">👤 {person}</span>
              <span class="person-amt">{r.get('currency','$')}{amount:.2f}</span>
            </div>""", unsafe_allow_html=True)
            for it in info["items"]:
                st.markdown(f"""
                <div class="item-row" style="padding-left:1rem">
                  <div class="item-desc">— {it['item']} ({it['quantity']} portion)</div>
                  <div style="color:#888;font-size:0.85rem">{r.get('currency','$')}{it['amount']:.2f}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align:right;font-weight:700;padding-top:0.6rem;border-top:1px solid #ddd;margin-top:0.4rem">
          TOTAL: {r.get('currency','$')}{grand_total:.2f}
        </div>""", unsafe_allow_html=True)
