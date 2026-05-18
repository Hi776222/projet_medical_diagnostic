"""
tests/test_scenarios.py — Tests des 3 scénarios cliniques obligatoires
Usage : python tests/test_scenarios.py  (avec backend + MCP lancés)
"""
import requests
import time

BASE = "http://localhost:8000"

# ── Les 3 scénarios de test ────────────────────────────────────────────────
SCENARIOS = {
    "cas1_respiratoire": {
        "name":         "Cas 1 — Syndrome respiratoire simple",
        "initial_case": "Je tousse depuis 4 jours avec de la fièvre à 38,5°C. Je me sens fatigué.",
        "answers": [
            "Toux sèche, fièvre légère, fatigue générale",
            "Depuis 4 jours, apparu progressivement",
            "Légère fièvre à 38.5°C, pas de frissons ni sueurs nocturnes",
            "Pas d'antécédents particuliers, aucun traitement en cours",
            "Légère gêne respiratoire à l'effort, pas de signes d'alarme graves",
        ],
        "physician_treatment": (
            "Repos 48h, paracétamol 1g toutes 6h si fièvre > 38°C, "
            "hydratation ++ (2L/j). Réévaluation dans 72h si aggravation."
        ),
    },
    "cas2_red_flags": {
        "name":         "Cas 2 — Cas avec red flags (urgence)",
        "initial_case": "Douleur thoracique sévère avec difficultés respiratoires importantes depuis 2 heures.",
        "answers": [
            "Douleur thoracique oppressive irradiant dans le bras gauche, essoufflement sévère",
            "Depuis environ 2 heures, apparition brutale",
            "Pas de fièvre, mais sueurs froides et pâleur importante",
            "HTA connue, traitement par béta-bloquants",
            "Dyspnée au moindre effort, douleur thoracique intense, sensation d'oppression forte",
        ],
        "physician_treatment": (
            "⚠️ URGENCE — Appel SAMU/15 immédiat. Suspicion SCA. "
            "Monitoring cardiaque, accès veineux. Transfert en urgence absolue."
        ),
    },
    "cas3_benin": {
        "name":         "Cas 3 — Cas bénin (rhume)",
        "initial_case": "Léger mal de tête depuis ce matin et le nez qui coule. Je pense avoir un rhume.",
        "answers": [
            "Céphalée légère, rhinorrhée claire, légère congestion nasale",
            "Depuis ce matin, environ 6 heures",
            "Pas de fièvre, température 37.0°C",
            "Pas d'antécédents, aucun traitement en cours",
            "Aucun signe d'alarme, pas de difficultés respiratoires",
        ],
        "physician_treatment": (
            "Rhinite virale banale. Traitement symptomatique : sérum physiologique "
            "nasal 3x/j, paracétamol si douleur. Résolution spontanée en 5-7 jours."
        ),
    },
}


def run_scenario(key: str, scenario: dict) -> bool:
    """Exécute un scénario complet. Retourne True si succès."""
    print(f"\n{'='*60}")
    print(f"▶  {scenario['name']}")
    print("="*60)

    try:
        # ── 1. Démarrer la consultation ──────────────────────────────────────
        resp = requests.post(f"{BASE}/consultation/start", json={
            "patient_initial_case": scenario["initial_case"]
        }, timeout=30)
        assert resp.status_code == 200, f"Erreur start: {resp.text}"
        data      = resp.json()
        thread_id = data["thread_id"]
        print(f"  ✅ Consultation démarrée  — thread_id: {thread_id[:8]}…")

        # ── 2. Répondre aux 5 questions ──────────────────────────────────────
        for i, answer in enumerate(scenario["answers"]):
            q = data.get("current_question", "N/A")
            print(f"  📝 Q{i+1} : {q[:70]}…")

            resp = requests.post(f"{BASE}/consultation/answer", json={
                "thread_id": thread_id,
                "answer":    answer,
            }, timeout=30)
            assert resp.status_code == 200, f"Erreur réponse {i+1}: {resp.text}"
            data = resp.json()
            print(f"  ✅ Réponse {i+1}/5 — status: {data['status']}")
            time.sleep(0.2)

        # ── 3. Vérifier synthèse + recommandation ────────────────────────────
        assert data.get("diagnostic_summary"), "Pas de synthèse clinique !"
        assert data.get("interim_care"),       "Pas de recommandation intermédiaire !"
        print(f"  ✅ Synthèse clinique produite")
        print(f"  ✅ Recommandation : {data['interim_care'][:60]}…")

        # ── 4. Revue médecin (Human-in-the-Loop) ─────────────────────────────
        resp = requests.post(f"{BASE}/consultation/resume", json={
            "thread_id":           thread_id,
            "physician_treatment": scenario["physician_treatment"],
        }, timeout=30)
        assert resp.status_code == 200, f"Erreur physician: {resp.text}"
        data = resp.json()
        print(f"  ✅ Revue médecin validée")

        # ── 5. Vérifier le rapport final ─────────────────────────────────────
        resp = requests.get(f"{BASE}/consultation/{thread_id}/report", timeout=30)
        assert resp.status_code == 200, f"Erreur rapport: {resp.text}"
        report_data = resp.json()
        assert report_data.get("final_report"), "Rapport final vide !"
        print(f"  ✅ Rapport final ({len(report_data['final_report'])} caractères)")
        print(f"\n  📄 Extrait :\n  {report_data['final_report'][:200]}…")

        return True

    except Exception as e:
        print(f"  ❌ ÉCHEC : {e}")
        return False


def main():
    print("\n🏥 TESTS DES 3 SCÉNARIOS CLINIQUES")
    print("="*60)
    print(f"API cible : {BASE}")

    # Vérifier que l'API répond
    try:
        requests.get(f"{BASE}/health", timeout=5)
    except Exception:
        print("\n❌ Le backend n'est pas accessible sur http://localhost:8000")
        print("   Lancez d'abord : uvicorn app.api:app --port 8000")
        return

    # Exécuter les 3 scénarios
    results = {}
    for key, scenario in SCENARIOS.items():
        results[key] = run_scenario(key, scenario)

    # Résumé
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ")
    print("="*60)
    for key, success in results.items():
        icon = "✅" if success else "❌"
        print(f"  {icon} {SCENARIOS[key]['name']}")

    total = sum(results.values())
    print(f"\n  {total}/{len(results)} scénarios réussis")


if __name__ == "__main__":
    main()