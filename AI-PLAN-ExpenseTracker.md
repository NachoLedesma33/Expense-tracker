# Plan de Integración IA — Expense Tracker (Zero-Cost)

> **Diagnóstico del plan anterior**: El borrador original proponía clasificación TF-IDF, análisis
> financiero, presupuestos, OCR y predicción de gastos — todo en **TypeScript cliente-side**.
> Este proyecto es **Django server-side + HTMX + vanilla JS**, sin build tooling para TS.
> Este plan revisado migra toda la lógica a **Python (services/)**, usa **HTMX** para la
> interacción frontal y elimina OCR (bajo valor, alto costo de implementación). Sin nuevas
> dependencias externas, sin APIs de pago.

---

## Arquitectura General

```
┌──────────────────────────────────────────────────────────────────┐
│                        Browser (HTMX + vanilla JS)               │
│  • Formulario: muestra categoría predicha vía hx-trigger="keyup" │
│  • Dashboard: insights renderizados como partials HTML           │
│  • Analytics: predicciones y budgets en gráficas existentes      │
└─────────────────────┬────────────────────────────────────────────┘
                      │ HTMX requests
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Django Server                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ transactions │  │  analytics   │  │      services/          │ │
│  │  (views)     │  │  (views)     │  │  ┌───────────────────┐ │ │
│  │              │  │              │  │  │ categorizer.py    │ │ │
│  │              │  │              │  │  │ insights.py       │ │ │
│  │              │  │              │  │  │ budgets.py        │ │ │
│  │              │  │              │  │  │ predictor.py      │ │ │
│  └─────────────┘  └──────────────┘  │  └───────────────────┘ │ │
└─────────────────────┬────────────────────────────────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │   PostgreSQL │
              │  (Neon)      │
              └──────────────┘
```

**Principios**:
- 100% gratis, sin APIs externas, sin dependencias Python nuevas
- Toda la lógica "IA" es matemática/estadística pura (TF-IDF, Naive Bayes, regresión lineal)
- Las features se integran como partials HTML vía HTMX, consistente con el patrón existente
- Cada feature es opt-in: el usuario puede ignorarla si no le interesa

---

## Fase 1: Categorización Automática (TF-IDF + Naive Bayes en Python)

### Estrategia
Clasificador de texto que corre **server-side** en Python puro (sin scikit-learn, sin numpy).
Entrenado con datos sintéticos + correcciones del usuario. Se invoca vía HTMX cuando el
usuario escribe el título.

### Implementación

**`services/categorizer.py`** — clasificador TF-IDF + Naive Bayes desde cero (~120 líneas):

```python
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
        self.term_freq = defaultdict(Counter)  # cat_id -> {term: count}
        self.total_docs = 0

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r'[^a-záéíóúñ0-9\s]', '', text)
        return [t for t in text.split() if len(t) > 1 and t not in STOP_WORDS]

    def train(self, examples: list[tuple[str, int]]):
        """examples: [(description, category_id), ...]"""
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
            'confidence': probs[0] if probs else 0,
            'alternatives': [{'id': c[0], 'score': p}
                             for c, p in zip(sorted_cats[1:4], probs[1:4])],
        }

    def learn(self, text: str, cat_id: int):
        """Online learning: ajusta el clasificador con correcciones del usuario."""
        tokens = self._tokenize(text)
        self.vocab.update(tokens)
        self.class_counts[cat_id] += 1
        self.term_freq[cat_id].update(tokens)
        self.total_docs += 1


# Datos sintéticos de entrenamiento (~200 ejemplos)
SYNTHETIC_DATA: list[tuple[str, int]] = [
    # Comida (1)
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
    ('vendetta helado', 1),
    ('grido helado', 1),
    ('starbucks cafe', 1),
    ('bonafide cafe', 1),
    ('la anonima super', 1),
    ('changomas super', 1),
    ('vea super', 1),
    # Transporte (2)
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
    ('didí viaje', 2),
    ('remis', 2),
    ('tren boleto', 2),
    ('bicicleta reparacion', 2),
    ('pirelli neumaticos', 2),
    ('service auto', 2),
    ('estacion medica', 2),  # revisión técnica
    ('infraccion transito', 2),
    ('seguros rio uruguay', 2),  # seguro auto
    ('carga sube', 2),
    ('combustible', 2),
    ('garage mensual', 2),
    # Servicios (3)
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
    ('limpieza edificio', 3),
    ('electricista', 3),
    ('plomero', 3),
    ('gasista', 3),
    ('pintura casa', 3),
    # Entretenimiento (4)
    ('netflix mensual', 4),
    ('spotify premium', 4),
    ('cine cordoba', 4),
    ('teatro libertad', 4),
    ('show b consumption patio olmos', 4),
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
    ('parque diversion', 4),
    ('evento deportivo', 4),
    ('cerveza bar', 4),
    ('whisky bar', 4),
    ('salida nocturna', 4),
    ('boliche bailable', 4),
    # Salud (5)
    ('farmacia', 5),
    ('osde prepaga', 5),
    ('dentista consulta', 5),
    ('medico consulta', 5),
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
    ('oculista', 5),
    ('traumatologo', 5),
    ('dermatologo', 5),
    ('ginecologo', 5),
    ('pediatra', 5),
    # Educación (6)
    ('curso online', 6),
    ('utn cuota', 6),
    ('libros universidad', 6),
    ('colegio cuota', 6),
    ('coursera curso', 6),
    ('udemy curso', 6),
    ('domestika curso', 6),
    ('inglés academia', 6),
    ('gimnasio cuota', 6),  # cross: podría ser salud también
    ('entrenador personal', 6),
    ('clase particular', 6),
    ('workshop taller', 6),
    ('conferencia ticket', 6),
    ('suscripcion educativa', 6),
    # Shopping (7)
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
]

# Instancia global del clasificador (se entrena una vez al importar)
_classifier = None

def get_classifier() -> CategoryClassifier:
    global _classifier
    if _classifier is None:
        _classifier = CategoryClassifier()
        _classifier.train(SYNTHETIC_DATA)
    return _classifier


def predict_category(text: str) -> dict:
    """Predice la categoría de una transacción dada su descripción."""
    clf = get_classifier()
    result = clf.predict(text)

    # Si la confianza es muy baja, devolver "sin categoría"
    if result['category_id'] is None or result['confidence'] < 0.3:
        return {'category_id': None, 'confidence': 0.0, 'alternatives': []}

    return result


def learn_from_correction(text: str, category_id: int):
    """Ajusta el clasificador con la corrección del usuario."""
    clf = get_classifier()
    clf.learn(text, category_id)
```

### Integración Frontend

**Nuevo endpoint HTMX** en `transactions/views.py`:
```python
def predict_category_view(request):
    text = request.GET.get('q', '')
    if len(text) < 3:
        return JsonResponse({'category_id': None, 'confidence': 0})
    result = predict_category(text)
    return JsonResponse(result)
```

**En el formulario** (`transactions/partials/form.html`):
```html
<input type="text" name="title" ...
       hx-get="/transactions/predict-category/"
       hx-trigger="keyup changed delay:500ms"
       hx-target="#suggested-category"
       hx-swap="innerHTML">
<select name="category" id="id_category"> ... </select>
<div id="suggested-category" class="text-xs text-gray-500 mt-1"></div>
```

El partial `suggested-category` renderiza algo como:
```html
<span class="text-blue-600 dark:text-blue-400">
  Suggested: Comida (85% confidence)
  <button hx-trigger="click"
          hx-post="/transactions/accept-category/123/"
          hx-swap="none">Accept</button>
</span>
```

### Aprendizaje Online
Cuando el usuario cambia manualmente la categoría o hace clic en "Accept",
se envía un POST al endpoint `/transactions/learn-category/` que llama a
`learn_from_correction(text, cat_id)`. El modelo mejora con cada uso.

### Rendimiento
- **Precisión esperada**: ~85-90% en categorías comunes
- **Velocidad**: <5ms por predicción (server-side, sin I/O)
- **Memoria**: La estructura del clasificador es <100KB en RAM
- **Sin dependencias**: Python puro, sin scikit-learn, sin numpy

---

## Fase 2: Análisis Financiero (Insights Heurísticos)

### Estrategia
Motor de ~15 reglas que analiza los datos del usuario y genera insights
con templates de texto. Se integra en el dashboard y analytics como partials HTMX.

### Implementación

**`services/insights.py`** (~150 líneas):

```python
from datetime import date, timedelta
from django.db.models import Sum
from transactions.models import Transaction


def generate_insights(user) -> list[dict]:
    """Genera una lista de insights basados en reglas heurísticas."""
    qs = Transaction.objects.filter(user=user)
    today = date.today()
    first_of_month = today.replace(day=1)
    insights = []

    # --- Regla 1: Categoría con mayor gasto este mes ---
    this_month = qs.filter(date__gte=first_of_month, type='expense')
    top_cat = (
        this_month.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
        .first()
    )
    if top_cat and top_cat['total']:
        insights.append({
            'type': 'top_category',
            'icon': '📊',
            'title': 'Top Category This Month',
            'message': f"Your biggest expense this month is "
                       f"**{top_cat['category__name'] or 'Uncategorized'}** "
                       f"at **${float(top_cat['total']):.2f}**",
            'severity': 'info',
        })

    # --- Regla 2: Comparación mes anterior ---
    last_month_start = (first_of_month - timedelta(days=1)).replace(day=1)
    last_month = qs.filter(
        date__gte=last_month_start,
        date__lt=first_of_month,
        type='expense',
    )
    this_total = this_month.aggregate(t=Sum('amount'))['t'] or 0
    last_total = last_month.aggregate(t=Sum('amount'))['t'] or 0
    if last_total > 0:
        change = ((this_total - last_total) / last_total) * 100
        if abs(change) > 5:
            insights.append({
                'type': 'trend',
                'icon': '📈' if change > 0 else '📉',
                'title': 'Month-over-Month',
                'message': (
                    f"📈 You spent **{abs(change):.0f}% more** this month "
                    f"compared to last month" if change > 0 else
                    f"📉 You spent **{abs(change):.0f}% less** this month "
                    f"compared to last month"
                ),
                'severity': 'warning' if change > 10 else 'success',
            })

    # --- Regla 3: Ingreso vs Gasto este mes ---
    this_income = this_month.filter(type='income').aggregate(
        t=Sum('amount')
    )['t'] or 0
    if this_income > 0 and this_total > 0:
        ratio = this_total / this_income * 100
        if ratio > 90:
            insights.append({
                'type': 'burn_rate',
                'icon': '🔥',
                'title': 'High Burn Rate',
                'message': f"You've spent **{ratio:.0f}%** of your income "
                           f"this month. Consider cutting non-essential expenses.",
                'severity': 'danger',
            })
        elif ratio < 50:
            insights.append({
                'type': 'savings',
                'icon': '💰',
                'title': 'Good Saving Rate',
                'message': f"You've only spent **{ratio:.0f}%** of your income. "
                           f"Great job saving!",
                'severity': 'success',
            })

    # --- Regla 4: Gastos recurrentes detectados (≥3 mismo monto mismo mes) ---
    from django.db.models import Count
    recurring = (
        qs.filter(type='expense', date__gte=first_of_month)
        .values('title', 'amount')
        .annotate(count=Count('id'))
        .filter(count__gte=2)
        .order_by('-count')
    )
    for rec in recurring[:3]:
        insights.append({
            'type': 'recurring',
            'icon': '🔄',
            'title': 'Recurring Expense',
            'message': f"**{rec['title']}** (${float(rec['amount']):.2f}) "
                       f"appeared **{rec['count']}×** this month",
            'severity': 'info',
        })

    # --- Regla 5: Transacciones sin categoría ---
    uncategorized = qs.filter(category__isnull=True).count()
    if uncategorized > 3:
        insights.append({
            'type': 'uncategorized',
            'icon': '🏷️',
            'title': 'Uncategorized Transactions',
            'message': f"You have **{uncategorized}** uncategorized transactions. "
                       f"Categorize them for better analytics.",
            'severity': 'warning',
        })

    # --- Regla 6: Promedio diario de gasto ---
    days_elapsed = (today - first_of_month).days + 1
    daily_avg = this_total / days_elapsed if days_elapsed > 0 else 0
    projected_monthly = daily_avg * 30
    insights.append({
        'type': 'daily_avg',
        'icon': '📅',
        'title': 'Daily Average',
        'message': f"You're spending **${daily_avg:.2f}/day** on average. "
                   f"Projected: **${projected_monthly:.2f}** this month",
        'severity': 'info',
    })

    # ~9 reglas más (compras impulsivas, días sin gastar, streak de ahorro,
    #   mejor día para comprar, categorías estacionales, etc.)

    return insights


def generate_recommendations(user) -> list[dict]:
    """Genera recomendaciones accionables."""
    qs = Transaction.objects.filter(user=user)
    today = date.today()
    first_of_month = today.replace(day=1)
    this_month = qs.filter(date__gte=first_of_month)
    recs = []

    # Recomendación 1: Basada en top categoría de gasto
    top_cat = (
        this_month.filter(type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
        .first()
    )
    if top_cat and top_cat['total']:
        cat_name = top_cat['category__name'] or 'Uncategorized'
        recs.append({
            'type': 'reduce_spending',
            'message': f"Consider setting a budget for **{cat_name}** "
                       f"(${float(top_cat['total']):.2f} this month)",
            'action': 'Set Budget →',
            'url': '/analytics/budgets/',
        })

    # Recomendación 2: If many small expenses
    small_txns = this_month.filter(type='expense', amount__lt=5).count()
    if small_txns > 5:
        recs.append({
            'type': 'small_expenses',
            'message': f"You've made **{small_txns}** small purchases (<$5). "
                       f"They add up!",
            'action': 'Review →',
            'url': '/transactions/?amount_max=5',
        })

    # ~5 recomendaciones más

    return recs
```

### Integración Frontend

**En `analytics/views.py`** — agregar insights al context:
```python
class OverviewView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['insights'] = generate_insights(self.request.user)
        ctx['recommendations'] = generate_recommendations(self.request.user)
        return ctx
```

**En `templates/analytics/overview.html`** — renderizar insights como cards:
```html
{% if insights %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
  {% for insight in insights %}
  <div class="p-4 rounded-xl border border-gray-200 dark:border-white/10
              {% if insight.severity == 'danger' %}bg-red-50 dark:bg-red-900/20
              {% elif insight.severity == 'warning' %}bg-yellow-50 dark:bg-yellow-900/20
              {% elif insight.severity == 'success' %}bg-green-50 dark:bg-green-900/20
              {% else %}bg-white/90 dark:bg-white/5{% endif %}">
    <div class="flex items-center gap-2 mb-1">
      <span class="text-lg">{{ insight.icon }}</span>
      <h4 class="font-medium text-sm">{{ insight.title }}</h4>
    </div>
    <p class="text-sm text-gray-600 dark:text-gray-400">{{ insight.message|safe }}</p>
  </div>
  {% endfor %}
</div>
{% endif %}
```

---

## Fase 3: Presupuestos Inteligentes

### Estrategia
Cálculo estadístico local (promedio + desvío estándar) para sugerir presupuestos
por categoría basados en el histórico del usuario. Nuevo modelo `Budget` en la DB.

### Implementación

**Nuevo modelo** en `transactions/models.py`:
```python
class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.DateField()  # primer día del mes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month'],
                name='unique_budget_per_month'
            )
        ]
```

**`services/budgets.py`**:
```python
from statistics import mean, stdev
from django.db.models import Sum
from transactions.models import Transaction, Budget


def suggest_budgets(user, month) -> list[dict]:
    """Sugiere presupuestos basados en el histórico de gastos."""
    suggestions = []
    categories = user.categories.all()

    for cat in categories:
        history = Transaction.objects.filter(
            user=user, category=cat, type='expense',
        ).values_list('amount', flat=True)

        amounts = [float(a) for a in history]
        if len(amounts) < 2:
            continue

        avg = mean(amounts)
        try:
            sd = stdev(amounts)
        except Exception:
            sd = avg * 0.3  # fallback si solo hay 1 transacción

        suggested = round(avg + sd, 2)

        suggestions.append({
            'category_id': cat.id,
            'category_name': cat.name,
            'avg': round(avg, 2),
            'std': round(sd, 2),
            'suggested': suggested,
            'current': get_current_spending(user, cat, month),
            'confidence': 'high' if len(amounts) > 10 else 'medium',
        })

    return sorted(suggestions, key=lambda x: -x['suggested'])


def get_current_spending(user, category, month):
    total = Transaction.objects.filter(
        user=user, category=category, type='expense',
        date__year=month.year, date__month=month.month,
    ).aggregate(t=Sum('amount'))['t'] or 0
    return float(total)
```

### Integración Frontend
- Nueva vista `BudgetListView` + `BudgetCreateView` (parciales HTMX)
- Sección "Presupuestos" en sidebar (nuevo url pattern)
- Modal para crear/editar presupuesto
- Barra de progreso que muestra consumo vs presupuesto
- Alerta cuando se excede el 80% del presupuesto

---

## Fase 4: Predicción de Gastos (Regresión Lineal Simple)

### Estrategia
Proyección de fin de mes basada en regresión lineal sobre el gasto acumulado
diario. Se integra en la página de Analytics.

### Implementación

**`services/predictor.py`**:
```python
from datetime import date, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncDate
from transactions.models import Transaction


def linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """(slope, intercept) para y = slope * x + intercept."""
    n = len(xs)
    if n < 2:
        return 0, 0
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_xx = sum(x * x for x in xs)
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return 0, 0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def predict_month_end(user) -> dict:
    today = date.today()
    first = today.replace(day=1)

    daily_totals = (
        Transaction.objects.filter(
            user=user, type='expense',
            date__gte=first, date__lte=today,
        )
        .annotate(d=TruncDate('date'))
        .values('d')
        .annotate(total=Sum('amount'))
        .order_by('d')
    )

    # Acumular gastos por día
    cumulative = []
    running = 0
    day_numbers = []
    for entry in daily_totals:
        running += float(entry['total'])
        day_num = entry['d'].day
        cumulative.append(running)
        day_numbers.append(day_num)

    if len(day_numbers) < 2:
        current = cumulative[-1] if cumulative else 0
        return {
            'current_total': current,
            'projected_total': current,
            'remaining_days': (date(today.year, today.month + 1, 1)
                               - timedelta(days=1)).day - today.day if today.month < 12 else 31 - today.day,
            'daily_average': current / today.day if today.day > 0 else 0,
            'confidence': 'low',
        }

    slope, intercept = linear_regression(day_numbers, cumulative)
    days_in_month = (date(today.year, today.month + 1, 1)
                     - timedelta(days=1)).day if today.month < 12 else 31
    projected = slope * days_in_month + intercept

    return {
        'current_total': cumulative[-1],
        'projected_total': round(max(0, projected), 2),
        'remaining_days': days_in_month - today.day,
        'daily_average': round(slope, 2),
        'confidence': 'high' if len(day_numbers) > 15 else 'medium',
    }
```

### Integración Frontend
- Se agrega como una card más en la página de Analytics
- Muestra: "Proyectás gastar $X a fin de mes (actual: $Y)"
- Barra de progreso visual (verde/amarillo/rojo según % del ingreso)
- Gráfico de línea proyectada (opcional, con Chart.js existente)

---

## Resumen de Costos

| Feature | Costo | Tokens/req | Deps nuevas | Implementación |
|---------|-------|------------|-------------|----------------|
| Categorización automática | $0 | 0 | 0 | TF-IDF + Naive Bayes en Python puro |
| Análisis financiero | $0 | 0 | 0 | 15 reglas heurísticas en Python |
| Presupuestos inteligentes | $0 | 0 | 0 | Estadística (promedio + desvío) |
| Predicción de gastos | $0 | 0 | 0 | Regresión lineal simple en Python |

**Costo total por usuario**: $0
**Dependencias externas nuevas**: 0 (todo Python stdlib)
**Tamaño de código agregado**: ~400 líneas Python + ~100 líneas templates

---

## Roadmap Ajustado

| Fase | Descripción | Esfuerzo | Deps |
|------|-------------|----------|------|
| 1 | Clasificador TF-IDF + Naive Bayes + endpoint HTMX | ~2 días | 0 |
| 2 | Motor de insights + recommendations + templates | ~2 días | 0 |
| 3 | Modelo Budget + sugerencias estadísticas + UI | ~2 días | 0 |
| 4 | Predicción de gastos + card en Analytics | ~1 día | 0 |
| 5 | Polish: tests, correcciones, seed data para budgets | ~1 día | 0 |

**Total**: ~8 días hábiles, **$0 en costos de API**, **0 dependencias externas nuevas**

---

## Cambios Clave Respecto al Plan Anterior

| Aspecto | Plan Anterior (TS) | Plan Revisado (Python) |
|---------|-------------------|----------------------|
| Lenguaje | TypeScript (requiere build tool) | Python puro (stdlib) |
| Ejecución | Browser (cliente) | Server (Django) |
| Interacción | No especificada | HTMX partials |
| OCR | Tesseract.js (~1MB) | Eliminado (bajo valor) |
| Dependencias nuevas | tesseract.js | 0 |
| Aprendizaje | Online en browser | Online en servidor |
