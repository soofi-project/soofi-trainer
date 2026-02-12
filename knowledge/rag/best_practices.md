# RAG Best Practices

## Chunking-Strategie

Die Wahl der Chunk-Größe ist entscheidend für die Retrieval-Qualität. Zu kleine Chunks verlieren Kontext, zu große verwässern die Relevanz. Ein typischer Sweet Spot liegt bei 256-512 Tokens mit Überlappung.

## Embedding-Modell

Bei der Wahl des Embedding-Modells sollte der Trade-off zwischen Qualität und Kosten berücksichtigt werden. OpenAI text-embedding-3-large bietet hohe Qualität, während kleinere Modelle kosteneffizienter für große Datenmengen sind.
