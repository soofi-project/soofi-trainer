# Supervised Fine-Tuning (SFT)

## Überblick

Supervised Fine-Tuning (SFT) ist eine Methode zur Anpassung eines vortrainierten Sprachmodells an eine spezifische Aufgabe durch Training auf gelabelten Input-Output-Paaren. Während des SFT lernt das Modell, strukturierte Prompts oder Eingaben auf gewünschte Ausgaben abzubilden, indem es klassische überwachte Lernziele optimiert. Im Gegensatz zum Continued Pretraining, das auf unlabeled Domänentext basiert, optimiert SFT das Modellverhalten direkt für klar definierte Aufgaben.

Im SOOFI-Kontext ermöglicht SFT eine kontrollierte und transparente Spezialisierung souveräner Foundation-Modelle, sofern qualitativ hochwertige gelabelte Daten verfügbar sind.

## Funktionsweise

Beim Supervised Fine-Tuning wird das vortrainierte Modell auf einem Datensatz trainiert, der aus Eingabe-Prompts und zugehörigen Zielantworten besteht. Der Trainingsprozess aktualisiert die Modellgewichte, um den Vorhersagefehler im Vergleich zu den gelabelten Zielausgaben zu minimieren. Je nach Setup wird entweder das gesamte Modell oder ein wesentlicher Teil seiner Parameter angepasst.

Durch die direkte Optimierung auf aufgabenspezifische Abbildungen kann SFT das Modellverhalten deutlich verändern und die Leistung auf klar definierten Zielgrößen verbessern.

## Wann einsetzen

SFT eignet sich besonders dann, wenn klar gelabelte Trainingsdaten verfügbar sind und eine starke aufgabenspezifische Performance erforderlich ist. Es wird häufig für strukturierte Generierungsaufgaben, Klassifikation, Zusammenfassung, Question Answering und domänenspezifische Antwortgenerierung eingesetzt.

Die Methode ist geeignet, wenn präzise Kontrolle über die Ausgaben und messbare Leistungsverbesserungen angestrebt werden.

## Vorteile

Ein zentraler Vorteil von SFT ist die hohe Anpassungsfähigkeit. Da die Modellgewichte direkt auf Basis gelabelter Supervision aktualisiert werden, kann die aufgabenspezifische Performance deutlich gesteigert werden. SFT ermöglicht eine präzise Ausrichtung auf gewünschte Ausgabeformate, Terminologie und Verhaltensvorgaben.

Im Vergleich zu rein promptbasierten Ansätzen bietet SFT eine konsistentere und zuverlässigere Aufgabenausführung.

## Einschränkungen

SFT erfordert qualitativ hochwertige gelabelte Input-Output-Daten, und die Leistungsfähigkeit hängt stark von Qualität, Abdeckung und Repräsentativität des Datensatzes ab. Die Erhebung und Kuratierung solcher Datensätze kann zeit- und kostenintensiv sein. Da Modellgewichte verändert werden, besteht das Risiko von Overfitting oder einer unbeabsichtigten Verschlechterung allgemeiner Fähigkeiten, wenn das Training nicht sorgfältig überwacht wird.

Eine geeignete Trainingsinfrastruktur ist erforderlich, und der Rechenaufwand steigt mit der Modellgröße. Die Wahl der Hyperparameter, die Trainingsdauer und die Evaluationsmethodik beeinflussen die endgültige Performance maßgeblich.

## Ressourcenanforderungen

Supervised Fine-Tuning erfordert einen kuratierten Datensatz gelabelter Input-Output-Paare, der auf die Zielaufgabe abgestimmt ist. Die Datensatzgröße kann je nach Aufgabenkomplexität und Modellgröße von einigen Tausend bis zu mehreren Millionen Beispielen reichen. Für das Training werden GPU-Ressourcen benötigt, wobei die Speicheranforderungen von der Modellgröße und der Optimierungsstrategie abhängen. Im Vergleich zu parameter-effizienten Methoden sind Rechen- und Speicheraufwand höher, wenn das vollständige Modell aktualisiert wird. Ein strukturiertes Evaluationsframework ist essenziell, um Leistungsverbesserungen zu validieren und mögliche Regressionen frühzeitig zu erkennen.

## Beispielanwendungen

Typische Anwendungsfälle umfassen aufgabenspezifische Textgenerierung, domänenspezifische Klassifikationssysteme, strukturierte Berichtserstellung, Question-Answering-Systeme sowie Assistenten zur Workflow-Automatisierung. SFT ist besonders effektiv, wenn klare Supervisionssignale vorliegen und Leistungsmetriken direkt messbar sind.

## Best Practices

Ein effektives SFT basiert auf gut konzipierten und repräsentativen Trainingsdatensätzen. Eine klare Definition von Evaluationsmetriken vor Trainingsbeginn unterstützt eine objektive Leistungsbewertung. Regelmäßige Validierung während des Trainings reduziert das Risiko von Overfitting. Versionskontrolle von Datensätzen und Modell-Checkpoints verbessert Reproduzierbarkeit und Governance.

## SOOFI Integrationsperspektive

Im SOOFI-Kontext stellt Supervised Fine-Tuning (SFT) einen zuverlässigen Mechanismus dar, um souveräne Foundation-Modelle mithilfe gelabelter Trainingsdatensätze an klar definierte Aufgaben anzupassen. Die Methode ermöglicht eine kontrollierte Spezialisierung, wenn domänenspezifische Supervisionssignale verfügbar sind und eine präzise Aufgabenleistung erforderlich ist. Innerhalb der SOOFI-Spezialisierungsworkflows kann SFT eingesetzt werden, um Modelle auf domänenspezifischen Datensätzen aus industriellen und öffentlichen Anwendungsbereichen zu trainieren. Dadurch kann das Modell domänenspezifische Terminologie, strukturierte Antwortformate und aufgabenspezifische Reasoning-Muster internalisieren. Dieser Ansatz unterstützt eine transparente und reproduzierbare Modellspezialisierung innerhalb der SOOFI-Trainingspipeline.