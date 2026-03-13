# Fallstricke bei RAG (Retrieval-Augmented Generation)

## Ungeeignete Chunk-Größe

Einer der häufigsten Fehler in RAG-Systemen ist die Wahl einer ungeeigneten Chunk-Größe bei der Dokumentsegmentierung. Zu kleine Chunks können wichtigen Kontext verlieren und zu unvollständigen oder fragmentierten Antworten führen. Zu große Chunks hingegen können die semantische Präzision verwässern und es dem Retrieval-System erschweren, die relevantesten Textpassagen zu identifizieren. Beide Extreme können die Qualität der Wissensverankerung (Grounding) reduzieren und das Risiko teilweise relevanter oder irreführender Antworten erhöhen. Eine sorgfältige experimentelle Abstimmung von Chunk-Größe und Überlappung ist daher notwendig, um ein Gleichgewicht zwischen Kontextvollständigkeit und Retrieval-Genauigkeit zu erreichen.

## Fehlende Metadatenfilterung

Ohne strukturierte Metadaten muss das Retrieval-System den gesamten Dokumentkorpus durchsuchen, was die Wahrscheinlichkeit irrelevanter oder verrauschter Ergebnisse erhöht. Das Fehlen von Metadatenfiltern kann die Präzision des Retrievals erheblich reduzieren, insbesondere in großen oder heterogenen Wissensbasen. Strukturierte Metadaten – etwa Dokumenttyp, Domänenkategorie, Versionsinformationen oder Zugriffsebenen – ermöglichen eine gezieltere Suche und verbessern die Relevanz der Ergebnisse. Gut gestaltete Metadatenschemata unterstützen zudem effiziente Filtermechanismen, Governance-Anforderungen und eine kontrollierte Nutzung von Wissensquellen.

## Geringe Embedding-Qualität

Ein weiteres häufiges Problem entsteht durch den Einsatz qualitativ schwacher oder schlecht abgestimmter Embedding-Modelle. Wenn das Embedding-Modell semantische Ähnlichkeiten nicht zuverlässig erfasst, kann das Retrieval-System Kontextpassagen zurückgeben, die oberflächlich ähnlich erscheinen, aber inhaltlich nicht relevant sind. Dies kann die Qualität der generierten Antworten verschlechtern und das Risiko von Halluzinationen erhöhen. Konsistente Embedding-Generierung sowie regelmäßige Evaluation der Retrieval-Leistung sind daher entscheidend für die Zuverlässigkeit des Systems.

## Zu viele abgerufene Dokumente (Over-Retrieval)

Das Abrufen zu vieler Dokument-Chunks kann das Kontextfenster des Modells überlasten und die Qualität der Generierung beeinträchtigen. Zu viel Kontext kann zusätzliches Rauschen oder widersprüchliche Informationen einführen, wodurch es für das Modell schwieriger wird, sich auf die relevantesten Fakten zu konzentrieren. Eine sorgfältige Abstimmung der Anzahl der abgerufenen Dokumente sowie der Einsatz von Reranking-Mechanismen können helfen, dieses Problem zu reduzieren.

## Fehlende Evaluation des Retrievals

Ein häufiger Fehler bei der Implementierung von RAG-Systemen besteht darin, sich ausschließlich auf die Qualität der generierten Antworten zu konzentrieren, während die Leistung der Retrieval-Komponente vernachlässigt wird. Ohne eine systematische Evaluation von Retrieval-Präzision und Recall können Schwächen im Retrieval-Layer unentdeckt bleiben. Regelmäßige Benchmarks der Retrieval-Genauigkeit und der Faktengrundlage der Antworten helfen sicherzustellen, dass das System langfristig robust und zuverlässig bleibt.