from gliner import GLiNER
import inspect

m = GLiNER.from_pretrained("knowledgator/gliner-relex-large-v1.0")
print("TYPE:", type(m))
print("METHODS:", [n for n in dir(m) if "infer" in n or "predict" in n or "relation" in n.lower()])
if hasattr(m, "inference"):
    print("SIGNATURE:", inspect.signature(m.inference))