from defs import add_post, add_reaction
from mimesis import Generic
from mimesis.locales import Locale
import random

def hype():
    count = 100
    while count > 0:
        generic = Generic(locale=Locale.RU)
        words = generic.text.words()
        text = ' '.join(words)
        add_post(text, 1, 0)
        count -= 1

def reactio():
    count = 10000
    while count > 0:
        react = ["cool", "cool", "cool"]
        random_index = random.randrange(len(react))
        add_reaction(random.randint(1, 25), react[random_index])
        count -= 1
