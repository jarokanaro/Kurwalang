from src.extensions import Extension


def dodaj(a, b):
    return a + b


EXTENSION = Extension(
    name="demo_ext",
    version="1.0.0",
    description="demo extension",
    functions={"dodaj": dodaj},
)
