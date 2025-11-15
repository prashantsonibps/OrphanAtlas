from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
import pandas as pd
from fpdf import FPDF
import os
import re
import unicodedata
from openai import OpenAI
from flask import Flask, request, jsonify

app = Flask(__name__)

# Path to the local Excel file
file_path = "symposiumfile.xlsx"

# Global variable to store fetched data
fetched_data = {}

# OpenRouter API configuration for DeepSeek
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
deepseek_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

def clean_text(text):
    """Remove hidden Unicode characters and normalize text."""
    if isinstance(text, str):
        text = text.replace("\u200b", "")
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        text = unicodedata.normalize('NFKD', text)
        # Replace LaTeX-like symbols
        text = text.replace('$', '').replace('\\', '')
    return text

def format_text_for_pdf(text):
    """Format text by inserting new lines if there are more than 10 consecutive spaces."""
    return re.sub(r' {10,}', '\n', text)

def is_valid_url(text):
    """Check if a given text is a valid URL."""
    return re.match(r'^https?:\/\/\S+', text) is not None

def extract_urls(text):
    """Extract all URLs from the text and return them as a list."""
    urls = re.findall(r'https?:\/\/\S+', text)
    return urls

def format_urls_to_click_links(text):
    """Replace URLs in the text with 'Click Link' or 'Click Link1', 'Click Link2', etc., for multiple URLs."""
    urls = extract_urls(text)
    if not urls:
        return text

    if len(urls) == 1:
        # Single URL: Replace with "Click Link"
        link_html = f'<a href="{urls[0]}" target="_blank">Click Link</a>'
        return re.sub(r'https?:\/\/\S+', link_html, text, count=1)
    else:
        # Multiple URLs: Replace with "Click Link1", "Click Link2", etc.
        result = text
        for i, url in enumerate(urls, 1):
            link_html = f'<a href="{url}" target="_blank">Click Link{i}</a>'
            result = re.sub(r'https?:\/\/\S+', link_html, result, count=1)
        return result

def truncate_text(text, max_length=100):
    """Truncate text to a maximum length and add ellipsis if truncated."""
    if len(text) > max_length:
        return text[:max_length].rsplit(' ', 1)[0] + "..."
    return text

def fetch_diseases():
    """Load data from all sheets into a dictionary."""
    global fetched_data
    sheets_to_load = [
        "Prevalence",
        "Publications",
        "Classification",
        "Symptoms",
        "Inheritance",
        "Genetic Variation",
        "Approved Treatments",
        "Biopharma Pipeline",
    ]

    for sheet in sheets_to_load:
        try:
            print(f"Loading sheet: {sheet}")
            data = pd.read_excel(file_path, sheet_name=sheet)
            data.fillna("No details available", inplace=True)
            print(f"Columns in {sheet}: {list(data.columns)}")
            fetched_data[sheet] = data
            print(f"Loaded {len(data)} rows from {sheet}.")
        except Exception as e:
            print(f"Error loading sheet '{sheet}': {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    """Render the search page for disease names."""
    global fetched_data
    if not fetched_data:
        fetch_diseases()

    all_diseases = set()
    for sheet in fetched_data.values():
        if 'Disease' in sheet.columns:
            all_diseases.update(sheet['Disease'].dropna().unique())
    all_diseases = sorted(all_diseases)

    query = request.form.get("query", "").strip() if request.method == "POST" else ""
    if query:
        return search(query)

    return render_template("index.html", diseases=all_diseases)

@app.route("/search/<path:query>", methods=["GET"])
def search(query):
    global fetched_data
    query = query.replace("%20", " ").replace("%0A", "\n").strip()
    sheets = list(fetched_data.keys())  # e.g., ["Prevalence", "Publications", ...]
    # Insert "Geographic Spread" after "Prevalence"
    try:
        prevalence_index = sheets.index("Prevalence")
        sheets.insert(prevalence_index + 1, "Geographic Spread")
    except ValueError:
        # If "Prevalence" is not found, append "Geographic Spread" at the end
        sheets.append("Geographic Spread")
    # Append "AI Generated Data" at the end
    sheets.append("AI Generated Data")
    return render_template("blocks.html", query=query, sheets=sheets)

@app.route("/search_suggestions")
def search_suggestions():
    """Fetch disease name suggestions as the user types."""
    global fetched_data
    query = request.args.get("query", "").strip().lower()

    if not query:
        return jsonify([])

    all_diseases = set()
    for sheet in fetched_data.values():
        if 'Disease' in sheet.columns:
            all_diseases.update(sheet['Disease'].dropna().unique())

    # Match diseases starting with the query
    matching_diseases = sorted([d for d in all_diseases if str(d).lower().startswith(query)])
    return jsonify(matching_diseases[:10])

@app.route("/get_diseases")
def get_diseases():
    """Fetch disease names based on the requested type (alphabetical, prevalence order, or sheet order)."""
    global fetched_data
    disease_type = request.args.get("type")
    reverse_order = request.args.get("reverse", "false").lower() == "true"

    if disease_type == "alphabetical":
        diseases = sorted(fetched_data.get("Prevalence", pd.DataFrame()).get("Disease", []).dropna().unique())
        return jsonify({"diseases": diseases})
    elif disease_type == "prevalence":
        # Fetch the Prevalence sheet and return Disease and Estimated prevalence(/100,000)
        prevalence_df = fetched_data.get("Prevalence", pd.DataFrame())
        if "Disease" not in prevalence_df.columns or "Estimated prevalence(/100,000)" not in prevalence_df.columns:
            return jsonify({"error": "Required columns not found in Prevalence sheet"}), 400
        # Select only the Disease and Estimated prevalence(/100,000) columns
        prevalence_data = prevalence_df[["Disease", "Estimated prevalence(/100,000)"]].dropna(subset=["Disease"])
        # Convert to list of dictionaries
        diseases = prevalence_data.to_dict('records')
        if reverse_order:
            diseases.reverse()
        return jsonify({"diseases": diseases})
    elif disease_type == "sheet_order":
        diseases = fetched_data.get("Prevalence", pd.DataFrame()).get("Disease", []).dropna().tolist()
        if reverse_order:
            diseases.reverse()
        return jsonify({"diseases": diseases})
    else:
        return jsonify({"error": "Invalid type"}), 400

@app.route("/fetch_data", methods=["POST"])
def fetch_data():
    """Fetch data for a specific sheet when clicked, including AI Generated Data from DeepSeek via OpenRouter."""
    global fetched_data
    sheet_name = request.json.get("sheet_name")
    query = request.json.get("query", "").strip().lower().replace("\n", " ")

    if sheet_name == "AI Generated Data":
        prompt = f"Generate 10 concise lines of hypothetical data about the disease '{query.capitalize()}' " \
                 f"including prevalence, symptoms, treatments, or research insights. Format each line as a sentence."
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek/deepseek-chat:free",
                messages=[
                    {"role": "system", "content": "You are a medical data generator assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            generated_text = response.choices[0].message.content.strip()
            lines = generated_text.split("\n")[:10]
            if len(lines) < 10:
                lines += ["No additional data available."] * (10 - len(lines))
            results = [{"AI Generated Data": line} for line in lines]
            results.append({"NOTE": "This data is generated by Deepseek V3 AI model"})
            return jsonify({"sheet": sheet_name, "data": results})
        except Exception as e:
            return jsonify({"error": f"Failed to generate data: {str(e)}"}), 500

    elif sheet_name in fetched_data:
        data = fetched_data[sheet_name]
        if "Disease" in data.columns:
            filtered = data[data["Disease"].str.lower().replace("\n", " ") == query]
            results = filtered.to_dict(orient="records")
            if not results:
                return jsonify({"error": "No matching records found for this disease."}), 404
            # Exclude specific column for Publications sheet
            if sheet_name == "Publications":
                for result in results:
                    if "Number of Approximate Publications in Last Five Years (Searching in Title/Abstract on Pubmed)" in result:
                        del result["Number of Approximate Publications in Last Five Years (Searching in Title/Abstract on Pubmed)"]
            # Add note for Inheritance sheet
            if sheet_name == "Inheritance":
                results.append({
                    "NOTE": "Not applicable is used for diseases that are not inherited. "
                            "Unknown is applied when the mode of inheritance is not yet determined. "
                            "Multigenic/multifactorial describes disorders where a combination of one or more genes "
                            "and/or environmental factors contributes to the expression of the phenotype."
                })
            if sheet_name == "Prevalence":
                results.append({"NOTE": "Without specification published figures are worldwide | An asterisk * indicates European data | BP indicates birth prevalence."})

            # Format URLs as "Click Link" for specific sheets
            if sheet_name in ["Biopharma Pipeline", "Publications", "Approved Treatments"]:
                for result in results:
                    for key, value in result.items():
                        if isinstance(value, str):
                            result[key] = format_urls_to_click_links(value)

            return jsonify({"sheet": sheet_name, "data": results})
        elif sheet_name == "Classification":
            results = []
            first_column = data.columns[0]
            filtered = data[data[first_column].str.lower().replace("\n", " ") == query]
            for index, row in filtered.iterrows():
                result_entry = {"Disease": query.capitalize()}
                for col in data.columns[1:]:
                    if pd.notna(row[col]) and row[col] != "No details available":
                        result_entry[col] = clean_text(str(row[col]))
                results.append(result_entry)
            if not results:
                return jsonify({"error": "No matching records found in Classification."}), 404
            return jsonify({"sheet": sheet_name, "data": results})
        else:
            return jsonify({"error": "No 'Disease' column found in sheet"}), 404
    else:
        return jsonify({"error": "Sheet not found"}), 404

@app.route("/fetch_data_stream", methods=["POST"])
def fetch_data_stream():
    """Stream data for the AI Generated Data block."""
    sheet_name = request.json.get("sheet_name")
    query = request.json.get("query", "").strip().lower().replace("\n", " ")

    if sheet_name != "AI Generated Data":
        return jsonify({"error": "Streaming only supported for AI Generated Data"}), 400

    prompt = f"Generate 10 concise lines of hypothetical data about the disease '{query.capitalize()}' " \
             f"including prevalence, symptoms, treatments, or research insights. Format each line as a sentence."

    def generate_stream():
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek/deepseek-chat:free",
                messages=[
                    {"role": "system", "content": "You are a medical data generator assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content.encode('utf-8')
        except Exception as e:
            yield f"Error: Failed to generate data: {str(e)}".encode('utf-8')

    return Response(stream_with_context(generate_stream()), content_type='text/plain; charset=utf-8')

@app.route("/download/<path:query>", methods=["GET"])
def download_pdf(query):
    """Generate and download a PDF report for the searched disease in a hospital report format."""
    global fetched_data
    query = query.replace("%20", " ").replace("%0A", "\n").strip()
    
    # Initialize PDF with hospital report formatting
    pdf = FPDF()
    pdf.set_margins(left=10, top=10, right=10)  # Reduced margins to fit more content
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    # Header: OrphanAtlas branding
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "OrphanAtlas", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 6, "Together, we turn hope into action for rare disease patients", ln=True, align="C")
    pdf.ln(5)

    # Report Title
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"Disease Report: {query.capitalize()}", ln=True, align="C")
    pdf.ln(5)

    # Add a horizontal line to separate header
    pdf.set_draw_color(100, 100, 100)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Define sheets to include (exclude AI Generated Data and Geographic Spread)
    sheets_to_include = list(fetched_data.keys())

    for sheet_name in sheets_to_include:
        # Correct typo in sheet name comparison
        if sheet_name == "Publications":
            display_name = "Publications"
        else:
            display_name = sheet_name

        data = fetched_data[sheet_name]
        if "Disease" in data.columns:
            filtered = data[data["Disease"].str.lower().replace("\n", " ") == query.lower()]
            results = filtered.to_dict(orient="records")
        elif sheet_name == "Classification":
            filtered = pd.DataFrame(columns=data.columns)
            first_column = data.columns[0]
            filtered = data[data[first_column].str.lower().replace("\n", " ") == query.lower()]
            results = []
            for _, row in filtered.iterrows():
                categories = [key for key, value in row.items() 
                             if key != data.columns[0] 
                             and pd.notna(value) 
                             and value != "No details available"]
                if categories:  # Only include if there are meaningful categories
                    results.append(categories)
        else:
            continue

        if not results:
            continue  # Skip sections with no data

        # Section header
        pdf.set_font("Arial", "B", 10)  # Smaller font for section headings
        pdf.cell(0, 6, f"{display_name}:", ln=True)
        pdf.ln(2)

        pdf.set_font("Arial", "", 8)  # Smaller font for body text
        if sheet_name == "Classification":
            for categories in results:
                categories_str = ", ".join(categories) if categories else "N/A"
                pdf.multi_cell(0, 4, f"Categories: {categories_str}")
                pdf.ln(2)
        else:
            for result in results:
                has_data = False
                # For Biopharma Pipeline, treat each entry as a continuous list without "Unnamed" labels
                if sheet_name == "Biopharma Pipeline":
                    entries = []
                    for col, val in result.items():
                        if col == "Disease" or pd.isna(val) or val == "No details available" or col.startswith("Unnamed"):
                            continue
                        val = clean_text(str(val))
                        val = format_text_for_pdf(val)
                        entries.append((col, val))
                    # Process unnamed columns as a continuous list
                    unnamed_entries = []
                    for col, val in result.items():
                        if col.startswith("Unnamed"):
                            val = clean_text(str(val))
                            val = format_text_for_pdf(val)
                            if val and val != "No details available":
                                unnamed_entries.append(val)
                    if entries or unnamed_entries:
                        has_data = True
                        for col, val in entries:
                            pdf.cell(30, 4, f"{col}: ", ln=False)
                            pdf.multi_cell(0, 4, val if val else "N/A")
                        for entry in unnamed_entries:
                            urls = extract_urls(entry)
                            if urls:
                                # If there are URLs, replace them with "Click Link" labels
                                if len(urls) == 1:
                                    # Single URL: "Click Link"
                                    entry = re.sub(r'https?:\/\/\S+', '', entry).strip()
                                    entry = truncate_text(entry, max_length=100)
                                    if entry:
                                        pdf.multi_cell(0, 4, entry + " ")
                                    pdf.set_text_color(0, 0, 255)
                                    pdf.cell(0, 4, "Click Link", ln=True, link=urls[0])
                                    pdf.set_text_color(0, 0, 0)
                                else:
                                    # Multiple URLs: "Click Link1", "Click Link2", etc.
                                    entry = re.sub(r'https?:\/\/\S+', '', entry).strip()
                                    entry = truncate_text(entry, max_length=100)
                                    if entry:
                                        pdf.multi_cell(0, 4, entry + " ")
                                    pdf.set_text_color(0, 0, 255)
                                    for i, url in enumerate(urls, 1):
                                        pdf.cell(0, 4, f"Click Link{i}" + (" " if i < len(urls) else ""), ln=(i == len(urls)), link=url)
                                    pdf.set_text_color(0, 0, 0)
                            else:
                                entry = truncate_text(entry, max_length=100)
                                pdf.multi_cell(0, 4, entry if entry else "N/A")
                else:
                    # Handle other sections
                    for col, val in result.items():
                        if col == "Disease" or pd.isna(val) or val == "No details available" or col == "NOTE":
                            continue
                        # Skip sections with only URLs and no other meaningful data
                        if sheet_name in ["Publications", "Approved Treatments"]:
                            urls = extract_urls(str(val))
                            if urls and not re.sub(r'https?:\/\/\S+', '', str(val)).strip():
                                continue
                        has_data = True
                        val = clean_text(str(val))
                        val = format_text_for_pdf(val)
                        # Special handling for sections with URLs
                        if sheet_name in ["Publications", "Approved Treatments"]:
                            urls = extract_urls(val)
                            if urls:
                                # If there are URLs, replace them with "Click Link" labels
                                if len(urls) == 1:
                                    # Single URL: "Click Link"
                                    val = re.sub(r'https?:\/\/\S+', '', val).strip()
                                    pdf.cell(30, 4, f"{col}: ", ln=False)
                                    if val:
                                        pdf.multi_cell(0, 4, val + " ")
                                    pdf.set_text_color(0, 0, 255)
                                    pdf.cell(0, 4, "Click Link", ln=True, link=urls[0])
                                    pdf.set_text_color(0, 0, 0)
                                else:
                                    # Multiple URLs: "Click Link1", "Click Link2", etc.
                                    val = re.sub(r'https?:\/\/\S+', '', val).strip()
                                    pdf.cell(30, 4, f"{col}: ", ln=False)
                                    if val:
                                        pdf.multi_cell(0, 4, val + " ")
                                    pdf.set_text_color(0, 0, 255)
                                    for i, url in enumerate(urls, 1):
                                        pdf.cell(0, 4, f"Click Link{i}" + (" " if i < len(urls) else ""), ln=(i == len(urls)), link=url)
                                    pdf.set_text_color(0, 0, 0)
                            else:
                                # No URLs, render as normal
                                val = truncate_text(val, max_length=100)
                                pdf.cell(30, 4, f"{col}: ", ln=False)
                                pdf.multi_cell(0, 4, val if val else "N/A")
                        else:
                            # Special handling for prevalence to format numbers
                            if col == "Estimated prevalence(/100,000)":
                                try:
                                    val = "{:,.2f}".format(float(val.replace(",", "")))
                                except (ValueError, TypeError):
                                    val = val if val else "N/A"
                            pdf.cell(30, 4, f"{col}: ", ln=False)
                            pdf.multi_cell(0, 4, val if val else "N/A")
                if has_data:
                    pdf.ln(2)

            # Add notes if applicable
            if sheet_name == "Prevalence":
                pdf.set_font("Arial", "I", 7)
                pdf.multi_cell(0, 4, "Note: Without specification, published figures are worldwide | An asterisk * indicates European data | BP indicates birth prevalence.")
                pdf.ln(2)
            if sheet_name == "Inheritance":
                pdf.set_font("Arial", "I", 7)
                pdf.multi_cell(0, 4, "Note: Not applicable is used for diseases that are not inherited. "
                                     "Unknown is applied when the mode of inheritance is not yet determined. "
                                     "Multigenic/multifactorial describes disorders where a combination of one or more genes "
                                     "and/or environmental factors contributes to the expression of the phenotype.")
                pdf.ln(2)

            pdf.ln(3)

    # Footer: Add a timestamp
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Generated on: May 14, 2025", ln=True, align="C")

    pdf_file = f"{query.replace('/', '_')}_report.pdf"
    pdf.output(pdf_file, "F")
    return send_file(pdf_file, as_attachment=True)

@app.route("/ask_bot", methods=["POST"])
def ask_bot():
    user_query = request.json.get("question", "").strip()
    if not user_query:
        return jsonify({"answer": "Please ask something about a rare disease."})

    # Check for "I'm really chatting with a person" query
    if user_query.lower().strip() in ["i'm really chatting with a person", "im really chatting with a person", "am i chatting with a person"]:
        response_text = """
I'm glad you feel that way! I'm OrphanAtlas Assistant, an AI designed to chat with you in a friendly and helpful way. I aim to make our conversation feel as natural as possible while providing you with accurate information about rare diseases. While I'm not a human, I'm here to assist you with a human touch! 😊<br><br>
How can I help you today?
"""
        html_answer = response_text.replace("\n", "<br>")
        return jsonify({"answer": html_answer})

    disease_count = 0
    if "Prevalence" in fetched_data and "Disease" in fetched_data["Prevalence"].columns:
        disease_count = fetched_data["Prevalence"]["Disease"].dropna().nunique()

    prompt = f"""
You are OrphanAtlas Assistant, a friendly, well-informed AI chatbot developed by Prashant Soni.
Your database contains information on {disease_count} rare diseases.

If someone asks "who created you" or "who designed you", reply:
"I was designed and developed by Prashant Soni, a passionate AI researcher and developer."

Always respond with:
- Clean HTML formatting
- Bullet points
- Clickable hyperlinks when possible
- Structured text for readability

User: {user_query}
"""

    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek/deepseek-chat:free",
            messages=[
                {"role": "system", "content": "You are a rare disease assistant that replies with clean HTML for the web."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        if response and response.choices and response.choices[0].message:
            raw_answer = response.choices[0].message.content.strip()
        else:
            return jsonify({"answer": "Sorry, I couldn't generate a response. Please try again."})

        # Format URLs in the chatbot response
        html_answer = raw_answer.replace("\n", "<br>")
        html_answer = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_answer)
        html_answer = format_urls_to_click_links(html_answer)

        return jsonify({"answer": html_answer})

    except Exception as e:
        return jsonify({"answer": f"Error: {str(e)}"})

@app.route("/get_disease_count")
def get_disease_count():
    """Return the total number of unique diseases from the Prevalence sheet."""
    global fetched_data
    if "Prevalence" in fetched_data and "Disease" in fetched_data["Prevalence"].columns:
        count = fetched_data["Prevalence"]["Disease"].dropna().nunique()
        return jsonify({"count": count})
    return jsonify({"count": 0, "error": "Prevalence sheet or Disease column not found"}), 404

@app.route("/get_geographic_spread", methods=["POST"])
def get_geographic_spread():
    """Returns a JSON list of predicted countries where the disease is most common, generated via DeepSeek model."""
    try:
        query = request.json.get("query", "").strip()
        prompt = f"List 10 countries where the disease '{query}' is most commonly found based on prevalence. Respond only with the country names separated by commas."

        response = deepseek_client.chat.completions.create(
            model="deepseek/deepseek-chat:free",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only country names."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5
        )

        if response and response.choices and hasattr(response.choices[0], "message"):
            text = response.choices[0].message.content
            countries = [c.strip() for c in re.split(r",|\n", text) if c.strip()]
            return jsonify({"locations": countries})

        return jsonify({"locations": []})
    except Exception as e:
        return jsonify({"error": str(e), "locations": []})

if __name__ == "__main__":  
    app.run(debug=True)
