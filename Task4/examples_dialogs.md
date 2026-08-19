# Примеры диалогов RAG-бота

LLM-бэкенд: `local` (`Qwen/Qwen2.5-0.5B-Instruct`)

## Успешные ответы

### Вопрос: What is the Void Core and what was its purpose?

```
Reasoning:
1. The context mentions two Void Core battles stations - DS-1 and DS-2.
2. Both stations were designed by the Dominion of Vess and were intended to be powerful weapons.
3. However, both stations were destroyed or rendered ineffective due to the actions of Peren Kaelis.
4. The context specifically refers to the DS-1 Void Core Mobile Battle Station, stating that it was "originally designed by the Geonosians during the waning years of the Concordance of Vess."
5. The question asks about the purpose of the Void Core, which is addressed in the following sentence: "It was designed to be more powerful than the original."
Conclusion: 
The Void Core was a gargantuan space station designed by the Dominion of Vess during the waning years of the Concordance of Vess. Its primary purpose was to be a more powerful weapon than the original design, allowing it to achieve greater destructive capabilities compared to the original version.
```

Источники: Void Core, Wilhuff Tarkos

best_score: 0.695

### Вопрос: Who trained Peren Kaelis and why was the High Council reluctant to accept him?

```
Reasoning:
1. The question asks about the training of Peren Kaelis and why the High Council was reluctant to accept him.
2. From the provided sources, we can gather that Peren Kaelis was trained by Thuun, who was willing to train him.
3. However, there is no mention of any reluctance or reasons for the High Council to refuse to accept Peren Kaelis.
4. The source "Peren Kaelis" refers to the son of Warden Knight Toren Kaelis and Senator Ilyra Sundari, suggesting this may be referring to another character rather than Peren Kaelis specifically.
5. Without additional information, it's difficult to determine if the High Council was indeed reluctant to accept Peren Kaelis based solely on the available sources.
Answer: The High Council was reluctant to accept Peren Kaelis because they sensed grave danger in his training.
```

Источники: Murkveil, Peren Kaelis, Thuun

best_score: 0.835

### Вопрос: Describe the planet Threnos and why it was destroyed.

```
Reasoning:
1. From the provided sources, we can gather basic information about Threnos.
2. However, the question asks specifically about why Threnos was destroyed, rather than just describing its appearance or features.
3. The source material mentions that Threnos was destroyed due to the presence of the Void Core battle station and its superweapon, the planet-killing superlaser.
4. This suggests that Threnos was targeted because of its strategic importance and potential threat to the Empire.
5. Given the context, it seems likely that the destruction of Threnos was part of a larger strategy to weaken the Empire and prepare for future conflicts.
Answer: Threnos was destroyed due to the presence of the Void Core battle station and its superweapon, the planet-killing superlaser.
```

Источники: Threnos, Wilhuff Tarkos

best_score: 0.699

### Вопрос: What happened during the Night of Sorrow?

```
Reasoning:
1. The question asks about the events during the Night of Sorrow.
2. From the provided context, we can see that the Night of Sorrow refers to a significant event in the history of the Warden Order.
3. The context mentions that this event occurred "after the Night of Sorrow" and "became known as the Night of Sorrow."
4. Therefore, the Night of Sorrow itself is described as a major event or catastrophe.
Answer: The Night of Sorrow was a catastrophic event that marked the end of the Warden Order and the beginning of the Dark Reign. It resulted in the loss of thousands of lives and destroyed much of the Warden Archive.
```

Источники: Concordance of Vess, Machine Wars, Nyxari, Thuun

best_score: 1.043

### Вопрос: Tell me about Zephyra and its tibanna gas mining.

```
Reasoning:
1. The context mentions that Zephyra is described as a gas giant in the Anoat sector.
2. It has two moons, indicating it may have multiple moons like other gas giants.
3. The text provides details about tibanna gas extraction, refining, and processing within the planet.
4. It notes that tibanna gas is extracted from repulsorlifted facilities and is used for various purposes such as fuel production and refining.
5. There is mention of mining complexes and cities like Ugnorgrad, but these are not specifically related to tibanna gas mining.
Based on this reasoning, I can conclude:

The main focus of Zephyra appears to be its tibanna gas mining operations, particularly focusing on extracting and refining tibanna gas through processes involving mining complexes and possibly refineries. However, without more specific details provided in the original sources, we cannot pinpoint exactly how much tibanna gas is mined or processed.
```

Источники: Groveheim, Zephyra

best_score: 0.617

## Случаи "Я не знаю"

### Вопрос: How do I reset my password in the Zendesk support portal?

```
Answer: I don't know. No relevant information was found in the knowledge base for this question.
```

best_score: 1.182 (порог: 1.1)

### Вопрос: What is the capital of France?

```
Answer: I don't know. No relevant information was found in the knowledge base for this question.
```

best_score: 1.276 (порог: 1.1)
