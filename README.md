# 🛡️ KnowledgeGuard AI

> **AI-Powered Knowledge Loss Detection & Risk Mitigation Platform**

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Usage](#-usage)

## 🎯 Overview

**KnowledgeGuard AI** is an intelligent knowledge management platform designed to help organizations identify, analyze, and mitigate risks associated with knowledge loss when employees leave. Built as a capstone project, it leverages AI, natural language processing, and graph theory to automatically map organizational knowledge dependencies and provide actionable insights.

🚀 **Live Demo:** [https://knowledgeguard-ai.streamlit.app/]


## 💡 Problem Statement

Organizations face significant challenges when key employees leave:

- **Knowledge Silos** - Critical information locked in individual employees
- **Undocumented Processes** - Tribal knowledge not captured in documents
- **Single Points of Failure** - Over-reliance on specific individuals
- **Slow Recovery** - Months to regain operational efficiency
- **High Costs** - Estimated 50-200% of annual salary to replace expertise

Traditional solutions are manual, time-consuming, and often incomplete.

## ✨ Solution

KnowledgeGuard AI provides an **automated, AI-driven approach** to:

1. **Extract Knowledge** - Automatically identify employees, systems, projects from documents
2. **Map Dependencies** - Build knowledge graphs showing who knows what
3. **Calculate Risk** - Score employees based on dependency and coverage
4. **Simulate Impact** - What-if analysis for employee departures
5. **Recommend Actions** - Actionable steps to mitigate risks

## 🚀 Key Features

### 1. **Smart Document Processing**
- Upload CSV, XLSX, PDF, DOCX files
- Automatic text extraction from multiple formats
- AI-powered entity recognition (employees, systems, projects)
- Multi-user support with complete data isolation

### 2. **Knowledge Graph Visualization**
- Interactive network diagram of organizational knowledge
- Visual representation of employees ↔ systems ↔ projects
- Color-coded risk levels (critical, high, medium, low)
- Relationship strength indicators

### 3. **Risk Analysis Engine**
- Automated dependency scoring for each employee
- Multi-dimensional risk assessment:
  - System dependency (which systems they own)
  - Process dependency (which processes they manage)
  - Project dependency (which projects they lead)
- Documentation coverage analysis
- Prioritized risk rankings

### 4. **Exit Impact Simulator**
- "What-if" scenario planning
- Comprehensive impact analysis for employee departures
- Affected systems, projects, and processes
- Recovery time estimates
- Mitigation recommendations

### 5. **AI Chat Assistant**
- Natural language queries about your knowledge base
- RAG (Retrieval Augmented Generation) powered
- Context-aware responses with source citations
- Ask questions like "Who owns the payment system?"

### 6. **Semantic Search**
- Vector similarity search using FAISS
- Find relevant documents by meaning, not just keywords
- Fast retrieval from large document repositories

### 7. **Admin Dashboard**
- User management and access control
- System analytics and metrics
- Audit logs for compliance
- Database backup and optimization

## 🛠️ Technology Stack

### **Backend**
- **Python 3.13** - Core programming language
- **Streamlit** - Web application framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Embedded database

### **AI & Machine Learning**
- **Groq API** - LLM for entity extraction (Llama 3.3 70B)
- **Sentence Transformers** - Text embeddings (all-MiniLM-L6-v2)
- **FAISS** - Vector similarity search

### **Data Processing**
- **Pandas** - Data manipulation
- **PyMuPDF** - PDF processing
- **python-docx** - Word document processing
- **openpyxl** - Excel file processing

### **Visualization**
- **Plotly** - Interactive charts
- **PyVis** - Network graph visualization

### **Security**
- **bcrypt** - Password hashing
- **python-jose** - JWT tokens

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Quick Start

```bash
# 1. Clone the repository
git clone [https://github.com/cvenkataravikiran/KnowledgeGuard-AI.git]
cd KnowledgeGuard-AI

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run system check
python check_system.py

# 6. Start the application
streamlit run app.py
```

### Automated Setup

```bash
# Run the automated setup script
python setup_app.py
```

## 📖 Usage

### 1. **Upload Documents**
- Navigate to **Upload Center**
- Upload your organizational documents:
  - Employee lists (CSV/XLSX)
  - Meeting notes (DOCX/PDF)
  - Project documentation
  - SOPs and processes
- Wait for processing (shows progress percentage)

### 2. **Explore Knowledge Graph**
- Go to **Knowledge Graph** page
- View interactive visualization of:
  - Employees (circles)
  - Systems (squares)
  - Projects (triangles)
- Hover over nodes for details
- Filter by entity type

### 3. **Run Risk Analysis**
- Navigate to **Risk Analysis**
- Click "Run Complete Risk Analysis"
- View risk scores and recommendations
- Identify high-risk employees

### 4. **Simulate Employee Exit**
- Go to **Exit Simulator**
- Select an employee
- View comprehensive impact analysis
- Get recovery time estimates
- Export report

### 5. **Ask Questions**
- Open **AI Assistant**
- Ask natural language questions:
  - "Who owns the deployment process?"
  - "Which systems does John manage?"
  - "What documentation is missing?"
- Get answers with source citations


## 🧪 Testing

```bash
# Run integration tests
python test_application.py

# Check system readiness
python check_system.py
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python test_application.py

# Check code quality
python -m py_compile app.py
```

## 👨‍💻 Author

**Your Name**
- GitHub: [@cvenkataravikiran]([https://github.com/cvenkataravikiran])
- Email: venkataravikiran.challa@gmail.com

## Future Enhancements

- Multi-language support
- Real-time collaboration features
- Integration with HR systems (HRIS)
- Advanced analytics dashboard
- Email notifications for risk alerts
- Mobile application
- API for third-party integrations
- Machine learning-based prediction models

---

**⭐ If you find this project helpful, please consider giving it a star!**