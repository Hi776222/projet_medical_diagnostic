# Système Multi-Agents Médical avec LangGraph

##  Description du Projet

**Diagnostic Médical** est une application académique qui simule un workflow d'orientation clinique via une architecture multi-agents basée sur **LangGraph**. Le système orchestre un processus complet allant de la collecte d'informations patient à la génération d'un rapport final, en passant par une validation humaine du médecin traitant.

###  Disclaimer Important

- **Ceci est un projet académique** - Le système est à but éducatif uniquement
- **N'est PAS un dispositif médical** - Le système ne doit pas être utilisé pour diagnostiquer ou traiter des conditions médicales
- **Ne remplace pas une consultation médicale** - Ce message doit figurer explicitement dans le rapport final
- **À usage démonstratif uniquement** - En aucun cas ne pas déployer en production pour des applications médicales réelles

---

##  Objectifs Pédagogiques

-  Modéliser un workflow multi-agents avec LangGraph
-  Gérer l'état partagé entre plusieurs agents
-  Intégrer les tools et le Human-in-the-Loop
-  Exposer un graphe via API FastAPI
-  Intégrer MCP pour les outils des agents
-  Développer une interface utilisateur
-  Tester et déboguer dans LangGraph Studio

---

##  Architecture

### Agents Principaux

1. **Supervisor** : Orchestre le workflow et décide des transitions entre étapes
2. **Diagnostic Agent** : Pose 5 questions au patient et génère une synthèse clinique préliminaire
3. **Physician Review** : Étape Human-in-the-Loop pour la validation du médecin traitant
4. **Report Agent** : Génère le rapport final structuré

### Workflow

```
START
  ↓
Supervisor
  ↓
Diagnostic Agent
  ├→ Tool: ask_patient (5 questions)
  └→ Tool: recommend_interim_care
  ↓
Supervisor
  ↓
Physician Review (Human-in-the-Loop)
  ↓
Supervisor
  ↓
Report Agent
  ↓
Supervisor
  ↓
END
```

---

##  Structure du Projet

```
project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── graph.py                  # Définition du graphe LangGraph
│   │   ├── state.py                  # État partagé (MedicalState)
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── supervisor.py         # Nœud Supervisor
│   │   │   ├── diagnostic_agent.py   # Nœud Diagnostic Agent
│   │   │   ├── physician_review.py   # Nœud Physician Review
│   │   │   └── report_agent.py       # Nœud Report Agent
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── patient_tools.py      # Tools pour questions patient
│   │   │   ├── care_tools.py         # Tools pour recommandations
│   │   │   └── mcp_client.py         # Client MCP
│   │   └── api.py                    # API FastAPI
│   ├── langgraph.json                # Config LangGraph Studio
│   ├── requirements.txt               # Dépendances Python
│   └── .env.example                   # Variables d'environnement
├── mcp_server/
│   ├── server.py                      # Serveur MCP
│   └── data/                          # Données MCP
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   └── README.md
├── tests/
│   ├── test_graph.py
│   ├── test_agents.py
│   └── test_api.py
├── README.md                          # Ce fichier
├── docker-compose.yml                # (Bonus) Orchestration
└── .gitignore
```

---

##  Technologies Utilisées

### Backend
- **Python 3.10+**
- **LangGraph** - Framework pour les graphes multi-agents
- **LangChain** - Framework LLM
- **FastAPI** - Framework API web
- **MCP** - Model Context Protocol
- **LLM** - Modèle de langage (OpenAI, Anthropic, etc.)

### Frontend
- **React** / Angular / Flutter / Streamlit (au choix)
- **Axios/Fetch API** - Requêtes HTTP
- **Tailwind CSS** / **Material-UI** (stylisation optionnelle)

### Outils
- **LangGraph Studio** - Visualisation et test du graphe
- **Postman** / **Insomnia** - Test API
- **Docker** / **docker-compose** (bonus)

---

##  Installation

### Prérequis
- Python 3.10 ou supérieur
- Node.js 16+ (pour le frontend React)
- pip et npm installés
- Clé API LLM (OpenAI, Anthropic, etc.)

### 1. Cloner le repository
```bash
git clone https://github.com/votre-repo/diagnostic-medical.git
cd diagnostic-medical
```

### 2. Installer les dépendances backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos clés API
```

Exemple `.env` :
```
OPENAI_API_KEY=sk-...
LANGGRAPH_API_KEY=your_langgraph_key
DATABASE_URL=sqlite:///./database.db
```

### 4. Installer les dépendances frontend

```bash
cd ../frontend
npm install
```

---

##  Exécution

### Lancer le Backend (FastAPI)

```bash
cd backend
python -m uvicorn app.api:app --reload --port 8000
```

L'API sera disponible à : `http://localhost:8000`
Documentation interactive : `http://localhost:8000/docs`

### Lancer le MCP Server

```bash
cd mcp_server
python server.py
```

### Lancer le Frontend

```bash
cd frontend
npm start
```

Le frontend sera disponible à : `http://localhost:3000`

### (Optionnel) Utiliser Docker Compose

```bash
docker-compose up -d
```

---

##  API Endpoints

### 1. Démarrer une session
```bash
POST /sessions/start
Content-Type: application/json

{
  "patient_initial_case": "Patient présentant une toux depuis 3 jours"
}
```

**Réponse :**
```json
{
  "session_id": "uuid-xxx",
  "status": "initiated"
}
```

### 2. Démarrer une consultation
```bash
POST /consultation/start
Content-Type: application/json

{
  "session_id": "uuid-xxx"
}
```

### 3. Reprendre une consultation
```bash
POST /consultation/resume
Content-Type: application/json

{
  "thread_id": "uuid-xxx",
  "user_input": "Réponse du patient",
  "action": "answer" | "physician_input"
}
```

### 4. Récupérer une consultation
```bash
GET /consultation/{thread_id}
```

### 5. Récupérer le rapport final
```bash
GET /consultation/{thread_id}/report
```

---

##  Tests dans LangGraph Studio

### Accéder à LangGraph Studio

```bash
# Démarrer le serveur LangGraph
langgraph dev --port 2024

# Accéder à http://localhost:2024
```

### Tests Obligatoires

1. **Cas 1 : Syndrome respiratoire simple**
   - Entrée : "Toux depuis 2 jours, pas de fièvre"
   - Vérifier : 5 questions, synthèse, recommandation intermédiaire, rapport final

2. **Cas 2 : Cas avec red flags**
   - Entrée : "Difficulté respiratoire, douleur thoracique"
   - Vérifier : Recommandation d'urgence, traitement médecin

3. **Cas 3 : Cas bénin**
   - Entrée : "Légère fatigue, aucun symptôme sérieux"
   - Vérifier : Conseil d'hydratation et repos

---

##  État Partagé du Graphe

```python
from typing import Annotated
from typing_extensions import TypedDict, Literal
from langgraph.graph.message import add_messages

class MedicalState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    next: Literal[
        "diagnostic_agent",
        "physician_review",
        "report_agent",
        "FINISH"
    ]
    question_count: int
    interim_care: str
    diagnostic_summary: str
    physician_treatment: str
    final_report: str
    patient_initial_case: str
    patient_answers: list
```

---

##  Intégration MCP

L'intégration MCP est obligatoire. Exemple avec un outil de recherche :

```python
# mcp_server/server.py

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("medical-tools-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_symptoms",
            description="Recherche des symptômes dans la base de données médicale",
            inputSchema={
                "type": "object",
                "properties": {
                    "symptom": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_symptoms":
        # Implémenter la logique
        return [TextContent(type="text", text="Résultats...")]
```

---

##  Exigences Minimales

- [x] Utiliser **LangGraph**
- [x] Contenir un **Supervisor**
- [x] Contenir au moins **2 agents métiers** (Diagnostic + Report)
- [x] Intégrer au moins **1 Human-in-the-Loop** (Physician Review)
- [x] Utiliser au least **1 tool via MCP**
- [x] Exposer une **API FastAPI**
- [x] Disposer d'un **Frontend**
- [x] Être testable dans **LangGraph Studio**

---

##  Bonus Possibles

- [ ] Sortie JSON structurée avec Pydantic
- [ ] Gestion avancée des erreurs
- [ ] Persistance en base de données
- [ ] Export PDF du rapport
- [ ] Historique des consultations
- [ ] Docker / docker-compose
- [ ] Tests unitaires et d'intégration
- [ ] Logging structuré

---

## Tests

### Exécuter les tests

```bash
cd backend
pytest tests/ -v
```

### Couverture de code

```bash
pytest --cov=app tests/
```

### Tests unitaires
```bash
pytest tests/test_agents.py -v
pytest tests/test_tools.py -v
```

### Tests d'intégration
```bash
pytest tests/test_api.py -v
pytest tests/test_graph.py -v
```

---

##  Documentation Complète

### Agents

Voir : [backend/app/nodes/README.md](./backend/app/nodes/README.md)

### Tools

Voir : [backend/app/tools/README.md](./backend/app/tools/README.md)

### API

Voir : [backend/API.md](./backend/API.md)

### Frontend

Voir : [frontend/README.md](./frontend/README.md)

---

## Configuration

### Fichier `langgraph.json`

```json
{
  "graph_id": "diagnostic-medical",
  "name": "Système Multi-Agents Médical",
  "description": "Workflow d'orientation clinique avec LangGraph",
  "entrypoint": "app.graph:graph",
  "python_version": "3.10"
}
```

### Variables d'Environnement

```
# LLM Configuration
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4-turbo

# LangGraph
LANGGRAPH_API_KEY=your_key
LANGGRAPH_ENDPOINT=http://localhost:8000

# MCP Server
MCP_HOST=localhost
MCP_PORT=5000

# Database (optionnel)
DATABASE_URL=sqlite:///./database.db

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

---

##  Lectures Recommandées

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/docs)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

---

##  Contribution

Les contributions sont bienvenues !

1. Fork le repository
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

##  Licence

Ce projet est fourni à des fins éducatives uniquement.

---

##  Auteur

**Projet Pédagogique** - Pr. Mohamed YOUSSFI

**Année Académique** : 2024-2025

---

## FAQ

**Q : Puis-je utiliser ce système pour un vrai diagnostic médical ?**
R : Non, absolument pas. C'est un projet académique uniquement.

**Q : Quels LLM sont supportés ?**
R : OpenAI, Anthropic, Hugging Face, Ollama (voir configuration).

**Q : Comment tester le graphe sans frontend ?**
R : Utiliser LangGraph Studio ou les endpoints FastAPI avec Postman/cURL.

**Q : Comment déployer en production ?**
R : Ne pas déployer en production à moins que ce ne soit pas à des fins médicales. Utiliser Docker et un orchestrateur comme Kubernetes.

---

##  Support

Pour toute question :
- Consulter la [documentation officielle LangGraph](https://python.langchain.com/docs/langgraph)
- Ouvrir une issue sur le repository
- Contacter l'instructeur

---

##  Sécurité

- **Ne jamais** partager les clés API
- **Ne jamais** stocker les clés en dur dans le code
- Utiliser des fichiers `.env` avec `.gitignore`
- Activer HTTPS en production
- Valider/Nettoyer toutes les entrées utilisateur

---

##  Roadmap

- [ ] v1.0 : Version MVP
- [ ] v1.1 : Export PDF
- [ ] v1.2 : Historique consultations
- [ ] v2.0 : Dashboard analytics

---


