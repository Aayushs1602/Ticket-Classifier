# 🤖 VibeFI AI Ticket Classifier

A lightweight AI-assisted service that classifies **banking support tickets** into either an **AI Patch** or a **Vibe Workflow**, and generates contextual reasoning and actionable next steps.

This project was built as part of the **VibeFI AI Challenge (Step 2)** to demonstrate the ability to blend **AI reasoning** with **real-world product surfaces**.

---

## 🧩 Features

- 🧠 **AI Reasoning** — Generates dynamic reasoning and next-step checklists using a local language model (no paid API).
- ⚙️ **Rule-based Classification** — Decides between *AI Patch* or *Vibe Workflow* based on ticket severity, keywords, and source.
- 💻 **Streamlit UI** — Clean, interactive interface for submitting and visualizing ticket classifications.
- 🧪 **Testing Support** — Includes test scripts with multiple ticket scenarios.
- 🪶 **Offline AI** — Uses Hugging Face transformers (e.g., DistilGPT-2) for text generation instead of remote APIs.

---

## 🚀 Demo Preview

**Example Input:**

| Channel | Severity | Summary                                               |
|----------|-----------|------------------------------------------------------|
| email    | high      | Payment module crashes with NullPointerException    |

**Output:**
- **Decision:** AI_PATCH  
- **Reasoning:** The issue involves a backend exception; likely a code-level bug requiring patch deployment.  
- **Checklist:**
  1. Collect logs and stack traces.  
  2. Reproduce the issue in staging.  
  3. Deploy AI-generated patch suggestion.  
  4. Run regression tests.  
  5. Monitor production metrics.  

---

## 🧠 Architecture Overview

.
├── app.py # Streamlit app for UI
├── classifier.py # Core logic (decision + AI reasoning)
├── test_classifier.py # Unit tests and sample runs
├── requirements.txt # Dependencies
├── README.md # Project documentation
└── .gitignore # Ignore rules


**Logic Flow:**
1. The app receives ticket metadata (channel, severity, summary).  
2. The classifier determines the category using heuristic and keyword-based rules.  
3. A local language model (DistilGPT-2) generates reasoning and a dynamic checklist.  
4. Streamlit displays structured output to the user.

---

## 🧪 Testing the Classifier

You can test the system from the command line:

```bash
python test_classifier.py
```

```bash
Sample output:

🧩 Input: {'channel': 'email', 'severity': 'high', 'summary': 'Payment module crashes with NullPointerException'}
✅ Output: {'decision': 'AI_PATCH', 'reasoning': '...', 'checklist': [...]}
```

## 💻 Running the App Locally
1. Clone the repository
```bash
git clone https://github.com/Aayushs1602/Ticket-Classifier.git
cd Ticket-Classifier
```

2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
# or
source venv/bin/activate   # On macOS/Linux
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Launch Streamlit app
```bash
streamlit run app.py
```

The app will open in your browser at:
👉 http://localhost:8501

## 🧩 Example Scenarios
|Channel   |Severity   |Summary	                                            |Expected Decision|
|----------|-----------|----------------------------------------------------------------------|
|email	   |high	   |Payment module crashes with NullPointerException	|AI_PATCH         |
|----------|-----------|----------------------------------------------------------------------|
|chat	   |medium	   |User unable to access dashboard due to config error	|VIBE_WORKFLOW    |
|----------|-----------|----------------------------------------------------------------------|
|web	   |high	   |Script failed due to missing API key	            |AI_PATCH         |
|----------|-----------|----------------------------------------------------------------------|
|phone	   |low	       |User forgot password	                            |VIBE_WORKFLOW    |
|----------|-----------|----------------------------------------------------------------------|

## ⚙️ Tech Stack
Component       |Library / Tool	          |       Purpose|
|----------|-----------|----------------------------------------------------------------------|
Frontend UI	    |Streamlit	|Interactive ticket submission|
|----------|-----------|----------------------------------------------------------------------|
AI Text Model	|HuggingFace Transformers	|Dynamic reasoning & checklist|
|----------|-----------|----------------------------------------------------------------------|
Heuristics	    |Python + Regex	|Decision rules|
|----------|-----------|----------------------------------------------------------------------|
Testing	   |Python (unittest)	|Validation of logic|
|----------|-----------|----------------------------------------------------------------------|
Deployment	|Local / Cloud Run	|Easily deployable Streamlit app|
|----------|-----------|----------------------------------------------------------------------|


## 🧩 Trade-offs
Area	|Decision	|Trade-off|
|----------|-----------|----------------------------------------------------------------------|
AI Model	|Used local DistilGPT-2	|Slightly less coherent than GPT-4 but offline and free|
|----------|-----------|----------------------------------------------------------------------|
Classification	|Rule-based	|Faster but less adaptive; could be replaced with fine-tuned model later|
|----------|-----------|----------------------------------------------------------------------|
Checklist Generation	|LLM-based	|Adds interpretability but occasional generic steps|
|----------|-----------|----------------------------------------------------------------------|
Validation	|Heuristic tests only	|Could expand to a labeled dataset later|
|----------|-----------|----------------------------------------------------------------------|


## 🧬 Future Improvements

- Integrate a fine-tuned small language model for more accurate reasoning.
- Store ticket history with session logs in Streamlit.
- Add feedback loop for model improvement.
- Use few-shot prompting for contextual decision-making.