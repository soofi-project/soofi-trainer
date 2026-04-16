# Souveränitäts-Übersicht: Modell-Anbieter im Vergleich

## Vergleichstabelle

| Anbieter | Land | Lizenz | Lizenz-Stabilität | Für sensitive EU-Anwendungen |
|----------|------|--------|-------------------|------------------------------|
| **Soofi / 8ra** | 🇩🇪 EU | Vollständig Open Source | ✅ Konsortiumsstruktur | ✅✅ Erste Wahl — maximale Souveränität |
| **OLMo (Ai2)** | 🇺🇸 USA | Apache 2.0 | ✅ Stabil | ⚠️ Vollständig auditierbar, aber US-Jurisdiktion |
| Mistral AI | 🇫🇷 EU | Apache 2.0 | ✅ Stabil | ✅ Europäisch, DSGVO-nah — Trainingsdaten nicht offen |
| Microsoft Phi | 🇺🇸 USA | MIT | ✅ Stabil | ⚠️ US-Unternehmen, CLOUD Act |
| Meta Llama | 🇺🇸 USA | Llama CL | ✅ Stabil | ⚠️ US-Unternehmen, eingeschränkte Lizenz |
| Google Gemma | 🇺🇸 USA | Gemma (proprietär) | ⚠️ Unklar | ⚠️ US-Unternehmen, proprietäre Lizenz, Gating |
| NVIDIA Nemotron | 🇺🇸 USA | NVIDIA (proprietär) | ⚠️ Unklar | ⚠️ US-Unternehmen, zusätzliche Framework-Bindung (NeMo) |
| Alibaba Qwen | 🇨🇳 China | Apache 2.0 / Qwen CL | ❌ Hohes Risiko | ❌ Nachgewiesene Lizenzänderung, chinesische Jurisdiktion |
| DeepSeek | 🇨🇳 China | MIT | ⚠️ Unklar | ❌ Chinesische Jurisdiktion, geopolitische Abhängigkeit |
| MiniMax | 🇨🇳 China | Modified MIT | ❌ Hohes Risiko | ❌ Kommerzielle Nutzung genehmigungspflichtig |

## Europäische Souveränitäts-Empfehlung

Für Anwendungen mit Anforderungen an digitale Souveränität, DSGVO-Konformität oder
langfristige Planungssicherheit gilt folgende Priorisierung:

1. **Soofi / 8ra** (🇩🇪 EU) — maximale Souveränität, vollständig auditierbar,
   europäische Governance-Struktur verhindert einseitige Lizenzänderungen
2. **Mistral AI** (🇫🇷 EU, Apache 2.0) — einzige weitere europäische Familie mit
   stabiler Open-Weight-Lizenz, DSGVO-nahe Unternehmenskultur
3. **Microsoft Phi / Meta Llama** (🇺🇸 USA, MIT/Llama CL) — US-rechtliche Abhängigkeit,
   aber etablierte Ökosysteme; akzeptabel für nicht-sicherheitskritische Anwendungen
4. **Alibaba Qwen / DeepSeek** (🇨🇳 China) — technisch leistungsfähig, aber hohes
   Lizenz-Instabilitätsrisiko und geopolitische Abhängigkeit; für sensitive
   Anwendungen nicht empfohlen
