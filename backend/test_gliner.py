import gliner
import inspect

model = gliner.GLiNER.from_pretrained("knowledgator/gliner-relex-large-v1.0")
print("Signature of predict_relations:")
print(inspect.signature(model.predict_relations))

text = "Apple Inc. was founded by Steve Jobs."
entity_labels = ["ORGANIZATION", "PERSON"]
relation_labels = ["founded by", "CEO"]

entities = model.predict_entities(text, entity_labels)
print("Entities:", entities)

# Maybe it expects entities as input?
try:
    relations = model.predict_relations(text, entities, relation_labels)
    print("Relations:", relations)
except Exception as e:
    print("Error:", e)
