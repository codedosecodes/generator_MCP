# DOCUFIND – Intelligent Email and Invoice Processor powered by Gabriel M. Cortés

## 🚀 Overview
DOCUFIND is an extracurricular university project designed to **automate the classification and analysis of emails containing invoices and receipts**, seamlessly integrating with **Google Drive** and **Google Sheets** for secure storage and reporting.  

The key innovation is that the system is built on the **MCP (Model Context Protocol)**, an emerging standard that connects **Large Language Models (LLMs)** with external data sources and tools in a **secure, scalable, and standardized way**.

---

## 🔑 What is MCP and Why Does it Matter?
**MCP** (*Model Context Protocol*) is an **open, universal protocol** that works as the “HTTP of AI”. It allows LLMs (such as GPT, Claude, Gemini) to:

- 📂 Access **external data sources** (emails, files, databases, APIs).  
- 🔧 Use **standardized tools** defined in MCP servers without rewriting integrations.  
- 🔄 Switch between models (e.g., GPT → Claude) without reprogramming integration logic.  
- 🛡️ Ensure **security** via *Personal Access Tokens (PATs)* and permission controls.  

As highlighted in recent technical guides:contentReference[oaicite:0]{index=0}, MCP addresses three critical LLM limitations:
- **Outdated knowledge** (training data is static and quickly becomes obsolete).  
- **Lack of domain-specific expertise** (e.g., invoices, enterprise workflows).  
- **No unified integration standard** (every integration today is custom-made).  

In short, **MCP is the bridge between AI models and real-world organizational data**.

---

## 🎯 Project Goals
- **Automate** processing of invoices received via email.  
- **Organize** attachments in Google Drive with a structured hierarchy (`/Year/Month/EmailID`).  
- **Generate intelligent reports** in Google Sheets with AI-extracted data (amount, vendor, concept).  
- **Demonstrate** MCP’s potential in a real-world academic/business document management use case.  

---

## ⚙️ Technical Architecture
The system follows an **MCP-based modular architecture**:

- **MCP Client**: integrated in the LLM, decides when external data is required.  
- **MCP Server (custom, Python)**: defines tools such as:  
  - `fetch_emails` → retrieve emails via IMAP.  
  - `extract_invoice` → process attachments and extract structured data.  
  - `store_drive` → upload files to Google Drive.  
  - `update_sheet` → append invoice data into Google Sheets.  
- **MCP Host**: the DOCUFIND app itself, acting as user-facing interface.  

📊 **Workflow**:
1. User triggers batch → LLM detects need for external info.  
2. MCP Client sends request to MCP Server.  
3. Attachments are stored in Drive, invoices are extracted, and Sheets are updated.  
4. A final report is emailed back to the user.  

---

## 🏫 Academic and Extracurricular Value
This project is highly relevant for **university counselors and reviewers** because:  
- 🔬 **Applies cutting-edge AI**: leverages MCP, a newly adopted protocol in AI research.  
- 📡 **Connects with real-world systems**: Gmail/IMAP, Google Drive, Google Sheets.  
- 🌍 **Cross-disciplinary impact**: useful in accounting, law, digital government, administration.  
- 🧩 **Hands-on learning**: combines cloud APIs, NLP, security, and workflow automation.  
- 🏆 **University innovation**: positions the institution as a pioneer exploring **global AI interoperability standards**.

---

## 🛠️ Technologies Used
- **Programming Language**: Python 3.11  
- **Libraries**:  
  - `google-api-python-client` (Drive/Sheets APIs)  
  - `imaplib` (IMAP email access)  
  - `tqdm` (CLI progress visualization)  
- **MCP (Model Context Protocol)**:  
  - Client and Server MCP components in Python  
  - Tool definitions for standardized integrations  
- **Infrastructure**:  
  - Google Cloud APIs (Drive, Sheets)  
  - OAuth2 + Personal Access Tokens for authentication and security  

---

## 📂 Project Structure

```
DOCUFIND/
├── 📄 README.md                          # Guía principal del proyecto
├── 📄 INSTALLATION_GUIDE.md              # Guía de instalación detallada
├── 📄 requirements.txt                   # Dependencias de Python
├── 📄 setup_find_documents.ps1           # Script de instalación Windows
├── 📄 .env.template                      # Plantilla de variables de entorno
├── 📄 .gitignore                         # Archivos a ignorar en Git
├── 📄 config.json.template               # Plantilla de configuración
├── 📄 docker-compose.yml                 # Configuración Docker (opcional)
├── 📄 Dockerfile                         # Imagen Docker (opcional)
├── 
├── 📂 src/                               # Código fuente principal
│   ├── 📄 __init__.py
│   ├── 📄 find_documents_mcp.py          # Aplicación principal MCP
│   ├── 📄 email_processor.py             # Procesador de correos
│   ├── 📄 google_drive_client.py         # Cliente Google Drive
│   ├── 📄 invoice_extractor.py           # Extractor de datos de facturas
│   └── 📄 config_manager.py              # Gestor de configuraciones
│   
├── 📂 tests/                             # Tests unitarios
│   ├── 📄 __init__.py
│   ├── 📄 test_email_processor.py
│   ├── 📄 test_google_drive.py
│   ├── 📄 test_invoice_extractor.py
│   └── 📄 test_integration.py
│   
├── 📂 scripts/                           # Scripts de utilidad
│   ├── 📄 test_installation.py           # Verificar instalación
│   ├── 📄 validate_credentials.py        # Validar credenciales
│   ├── 📄 setup_google_auth.py           # Configurar Google OAuth
│   └── 📄 cleanup_temp_files.py          # Limpiar archivos temporales
│   
├── 📂 config/                            # Configuraciones
│   ├── 📄 credentials.json               # Credenciales Google (no incluir en Git)
│   ├── 📄 token.json                     # Token OAuth (se genera automático)
│   ├── 📄 config.json                    # Configuración principal
│   └── 📄 email_providers.json           # Configuraciones de proveedores email
│   
├── 📂 logs/                              # Archivos de log
│   ├── 📄 find_documents.log
│   ├── 📄 errors.log
│   └── 📄 processing_stats.log
│   
├── 📂 temp/                              # Archivos temporales
│   └── 📄 .gitkeep
│   
├── 📂 docs/                              # Documentación adicional
│   ├── 📄 API_REFERENCE.md               # Referencia de APIs
│   ├── 📄 TROUBLESHOOTING.md             # Solución de problemas
│   ├── 📄 EXAMPLES.md                    # Ejemplos de uso
│   └── 📄 CHANGELOG.md                   # Historial de cambios
│   
├── 📂 examples/                          # Ejemplos de configuración
│   ├── 📄 basic_usage.py                 # Uso básico
│   ├── 📄 advanced_filtering.py          # Filtrado avanzado
│   ├── 📄 batch_processing.py            # Procesamiento en lotes
│   └── 📂 sample_configs/                # Configuraciones de ejemplo
│       ├── 📄 gmail_config.json
│       ├── 📄 outlook_config.json
│       └── 📄 corporate_config.json
│   
└── 📂 venv_find_docs/                    # Entorno virtual (no incluir en Git)
    └── ...
```
