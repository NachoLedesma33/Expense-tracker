import math
import re
from collections import Counter, defaultdict

STOP_WORDS = {
    'de', 'la', 'el', 'en', 'del', 'con', 'para', 'por', 'un', 'una',
    'los', 'las', 'su', 'que', 'y', 'e', 'o', 'a', 'al', 'lo', 'se',
    'no', 'es', 'mi', 'tu', 'me', 'te', 'le', 'les',
}


class CategoryClassifier:
    def __init__(self):
        self.vocab = set()
        self.class_counts = Counter()
        self.term_freq = defaultdict(Counter)
        self.total_docs = 0

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r'[^a-záéíóúñ0-9\s]', '', text)
        return [t for t in text.split() if len(t) > 1 and t not in STOP_WORDS]

    def train(self, examples: list[tuple[str, int]]):
        for text, cat_id in examples:
            tokens = self._tokenize(text)
            self.vocab.update(tokens)
            self.class_counts[cat_id] += 1
            self.term_freq[cat_id].update(tokens)
            self.total_docs += 1

    def predict(self, text: str) -> dict:
        tokens = self._tokenize(text)
        if not tokens:
            return {'category_id': None, 'confidence': 0.0, 'alternatives': []}

        scores = {}
        vocab_size = len(self.vocab)
        for cat_id, count in self.class_counts.items():
            log_prior = math.log(count / self.total_docs)
            log_likelihood = 0.0
            total_terms_in_cat = sum(self.term_freq[cat_id].values())
            for token in tokens:
                freq = self.term_freq[cat_id].get(token, 0)
                prob = (freq + 1) / (total_terms_in_cat + vocab_size)
                log_likelihood += math.log(prob)
            scores[cat_id] = log_prior + log_likelihood

        sorted_cats = sorted(scores.items(), key=lambda x: -x[1])
        top_score = sorted_cats[0][1] if sorted_cats else 0

        def softmax(vals):
            exps = [math.exp(v - top_score) for v in vals]
            s = sum(exps)
            return [e / s for e in exps]

        scores_list = [s for _, s in sorted_cats]
        probs = softmax(scores_list) if scores_list else []

        return {
            'category_id': sorted_cats[0][0],
            'confidence': round(probs[0] * 100, 1) if probs else 0,
            'alternatives': [
                {'id': c[0], 'score': round(p * 100, 1)}
                for c, p in zip(sorted_cats[1:4], probs[1:4])
            ],
        }

    def learn(self, text: str, cat_id: int):
        tokens = self._tokenize(text)
        self.vocab.update(tokens)
        self.class_counts[cat_id] += 1
        self.term_freq[cat_id].update(tokens)
        self.total_docs += 1


SYNTHETIC_DATA: list[tuple[str, int]] = [
    ('McDonalds Patio Olmos', 1),
    ('Mostaza nueva cordoba', 1),
    ('Disco supermercado', 1),
    ('pedidos ya delivery', 1),
    ('havanna cafe', 1),
    ('supermercado carrefour', 1),
    ('panaderia centenario', 1),
    ('almacen barrio', 1),
    ('restaurante centro', 1),
    ('pizzeria roma', 1),
    ('heladeria', 1),
    ('kiosco 24', 1),
    ('carniceria', 1),
    ('verdueria', 1),
    ('maxikiosco', 1),
    ('comida rapida', 1),
    ('almuerzo ejecutivo', 1),
    ('cena restaurante', 1),
    ('desayuno cafeteria', 1),
    ('delivery comida', 1),
    ('compras supermercado', 1),
    ('almacen natural', 1),
    ('dietetica', 1),
    ('fiambreria', 1),
    ('pescaderia', 1),
    ('starbucks cafe', 1),
    ('la anonima super', 1),
    ('changomas super', 1),
    ('vea super', 1),
    ('burger king', 1),
    ('kentucky fried chicken', 1),
    ('comida china delivery', 1),
    ('uber viaje centro', 2),
    ('cabify aeropuerto', 2),
    ('YPF nafta super', 2),
    ('taxi cordoba', 2),
    ('colectivo boleto', 2),
    ('sube recarga', 2),
    ('estacionamiento', 2),
    ('shell nafta', 2),
    ('peaje autopista', 2),
    ('uber viaje', 2),
    ('didi viaje', 2),
    ('remis', 2),
    ('tren boleto', 2),
    ('service auto', 2),
    ('seguros rio uruguay', 2),
    ('carga sube', 2),
    ('combustible', 2),
    ('garage mensual', 2),
    ('EPEC luz', 3),
    ('internet fibertel', 3),
    ('expensas edificio', 3),
    ('agua aguas cordobesas', 3),
    ('gas Ecogas', 3),
    ('telefono personal', 3),
    ('celular claro', 3),
    ('seguro hogar', 3),
    ('alquiler mensual', 3),
    ('ABL municipal', 3),
    ('tasa municipal', 3),
    ('cablevision tv', 3),
    ('internet iplan', 3),
    ('celular movistar', 3),
    ('alarma monitoreo', 3),
    ('electricista', 3),
    ('plomero', 3),
    ('gasista', 3),
    ('pintura casa', 3),
    ('netflix mensual', 4),
    ('spotify premium', 4),
    ('cine cordoba', 4),
    ('teatro libertad', 4),
    ('recital', 4),
    ('libro libreria', 4),
    ('playstation store', 4),
    ('steam juego', 4),
    ('disney plus', 4),
    ('hbo max', 4),
    ('amazon prime video', 4),
    ('crunchyroll', 4),
    ('youtube premium', 4),
    ('apple music', 4),
    ('concierto', 4),
    ('museo entrada', 4),
    ('evento deportivo', 4),
    ('cerveza bar', 4),
    ('salida nocturna', 4),
    ('boliche bailable', 4),
    ('farmacia', 5),
    ('osde prepaga', 5),
    ('dentista consulta', 5),
    ('medico consulta', 5),
    ('remedio farmacia', 5),
    ('ibuprofeno farmacia', 5),
    ('paracetamol', 5),
    ('pastillas receta', 5),
    ('medicamentos farmacia', 5),
    ('farmacity farmacia', 5),
    ('analisis clinicos', 5),
    ('oftalmologo', 5),
    ('psicologo sesion', 5),
    ('kinesiologo', 5),
    ('medicamentos', 5),
    ('farmacity', 5),
    ('obra social', 5),
    ('clinica internacion', 5),
    ('emergencias', 5),
    ('ecografia', 5),
    ('radiografia', 5),
    ('odontologo', 5),
    ('traumatologo', 5),
    ('dermatologo', 5),
    ('ginecologo', 5),
    ('pediatra', 5),
    ('curso online', 6),
    ('utn cuota', 6),
    ('libros universidad', 6),
    ('colegio cuota', 6),
    ('coursera curso', 6),
    ('udemy curso', 6),
    ('domestika curso', 6),
    ('ingles academia', 6),
    ('gimnasio cuota', 6),
    ('entrenador personal', 6),
    ('clase particular', 6),
    ('workshop taller', 6),
    ('conferencia ticket', 6),
    ('suscripcion educativa', 6),
    ('falabella ropa', 7),
    ('musimundo electronica', 7),
    ('fravega electrodomesticos', 7),
    ('mercadolibre compra', 7),
    ('amazon compra', 7),
    ('zapatillas deportivas', 7),
    ('indumentaria', 7),
    ('tienda oficial', 7),
    ('outlet shopping', 7),
    ('electrodomestico', 7),
    ('celular nuevo', 7),
    ('notebook', 7),
    ('accesorios computacion', 7),
    ('muebles', 7),
    ('decoracion hogar', 7),
    ('juguete', 7),
    ('regalo', 7),
    ('perfumeria', 7),
    ('cosmeticos', 7),
    ('ferreteria', 7),
    ('bazar', 7),
    ('dia del nino', 7),
    ('ropa deportiva', 7),
]

_classifier = None


def get_classifier() -> CategoryClassifier:
    global _classifier
    if _classifier is None:
        _classifier = CategoryClassifier()
        _classifier.train(SYNTHETIC_DATA)
    return _classifier


def predict_category(text: str) -> dict:
    clf = get_classifier()
    result = clf.predict(text)
    if result['category_id'] is None or result['confidence'] < 20.0:
        return {'category_id': None, 'confidence': 0.0, 'alternatives': []}
    return result


def learn_from_correction(text: str, category_id: int):
    clf = get_classifier()
    clf.learn(text, category_id)
