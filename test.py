from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.environment import Environment

print(Document(Concat(Environment("test", "Hallo!"))))
