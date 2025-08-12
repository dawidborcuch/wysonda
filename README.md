# Wysonda - Platforma Sondaży Politycznych

Wysonda to nowoczesna aplikacja webowa do przeprowadzania sondaży politycznych w sposób wiarygodny i bezpieczny. Aplikacja została stworzona w Django z wykorzystaniem Bootstrap 5 i oferuje zaawansowane funkcjonalności dla użytkowników i administratorów.

## 🚀 Funkcjonalności

### Dla użytkowników:
- **Strona główna** - lista aktualnych sondaży z sortowaniem według daty
- **Głosowanie** - bezpieczny system głosowania z zabezpieczeniami:
  - Blokada po adresie IP
  - Zapisywanie w LocalStorage
  - Fingerprint przeglądarki
- **Wyniki na żywo** - aktualne wyniki odświeżane w czasie rzeczywistym
- **Profile kandydatów** - szczegółowe informacje o kandydatach i partiach
- **Historia sondaży** - przegląd zakończonych wydarzeń
- **System komentarzy** - możliwość komentowania profili kandydatów

### Dla administratorów:
- **Panel administracyjny** - pełne zarządzanie sondażami
- **Tworzenie wydarzeń** - dodawanie nowych sondaży
- **Zarządzanie kandydatami** - dodawanie i edycja kandydatów
- **Moderacja komentarzy** - zatwierdzanie i usuwanie komentarzy
- **Eksport wyników** - eksport do CSV/Excel
- **Analityka** - szczegółowe statystyki i raporty

### Dodatkowe funkcje:
- **API REST** - publiczne API dla integracji zewnętrznych
- **Responsywny design** - pełna obsługa urządzeń mobilnych
- **System odznak** - gamifikacja dla użytkowników
- **Profil premium** - rozszerzone funkcje dla kandydatów
- **Geolokalizacja** - anonimowe dane geograficzne

## 🛠️ Technologie

- **Backend**: Python 3.10+, Django 5.2
- **Frontend**: Bootstrap 5, JavaScript (ES6+)
- **Baza danych**: SQLite (development), PostgreSQL (production)
- **Dodatkowe**: Django REST Framework, Django Allauth, Crispy Forms

## 📋 Wymagania systemowe

- Python 3.10 lub nowszy
- pip (menedżer pakietów Python)
- Git

## 🚀 Instalacja i uruchomienie

### 1. Klonowanie repozytorium
```bash
git clone <url-repozytorium>
cd wysonda
```

### 2. Tworzenie wirtualnego środowiska
```bash
python -m venv .venv
```

### 3. Aktywacja środowiska wirtualnego

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 5. Konfiguracja bazy danych
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Tworzenie superużytkownika
```bash
python manage.py createsuperuser
```

### 7. Uruchomienie serwera deweloperskiego
```bash
python manage.py runserver
```

Aplikacja będzie dostępna pod adresem: http://127.0.0.1:8000/

## 📁 Struktura projektu

```
wysonda/
├── wysonda/              # Główna konfiguracja Django
├── polls/                # Aplikacja sondaży
│   ├── models.py         # Modele danych
│   ├── views.py          # Widoki
│   ├── forms.py          # Formularze
│   ├── admin.py          # Panel administracyjny
│   └── utils.py          # Funkcje pomocnicze
├── api/                  # API REST
│   ├── views.py          # Widoki API
│   └── serializers.py    # Serializery
├── accounts/             # Zarządzanie użytkownikami
├── templates/            # Szablony HTML
├── static/               # Pliki statyczne
│   ├── css/             # Style CSS
│   ├── js/              # Skrypty JavaScript
│   └── images/          # Obrazy
├── media/                # Pliki uploadowane przez użytkowników
└── requirements.txt      # Zależności Python
```

## 🔧 Konfiguracja

### Zmienne środowiskowe
Utwórz plik `.env` w głównym katalogu projektu:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### Ustawienia produkcyjne
Dla wdrożenia produkcyjnego:

1. Zmień `DEBUG = False` w `settings.py`
2. Skonfiguruj bazę danych PostgreSQL
3. Ustaw `SECRET_KEY` jako zmienną środowiskową
4. Skonfiguruj serwer web (nginx + gunicorn)

## 📊 API

Aplikacja udostępnia REST API pod adresem `/api/`:

- `GET /api/events/` - lista wydarzeń
- `GET /api/events/{id}/` - szczegóły wydarzenia
- `GET /api/events/{id}/results/` - wyniki wydarzenia
- `POST /api/votes/` - oddanie głosu
- `GET /api/statistics/` - statystyki aplikacji

## 🔒 Bezpieczeństwo

Aplikacja implementuje następujące zabezpieczenia:

- **CSRF Protection** - ochrona przed atakami CSRF
- **XSS Protection** - ochrona przed skryptami cross-site
- **SQL Injection Protection** - ochrona przed wstrzykiwaniem SQL
- **Rate Limiting** - ograniczenie liczby żądań
- **Input Validation** - walidacja danych wejściowych
- **Secure Headers** - bezpieczne nagłówki HTTP

## 🧪 Testy

Uruchomienie testów:
```bash
python manage.py test
```

## 📝 Licencja

Ten projekt jest dostępny na licencji MIT. Zobacz plik `LICENSE` dla szczegółów.

## 🤝 Współpraca

1. Fork projektu
2. Utwórz branch dla nowej funkcjonalności (`git checkout -b feature/AmazingFeature`)
3. Commit zmian (`git commit -m 'Add some AmazingFeature'`)
4. Push do brancha (`git push origin feature/AmazingFeature`)
5. Otwórz Pull Request

## 📞 Wsparcie

W przypadku problemów lub pytań:
- Utwórz issue w repozytorium GitHub
- Skontaktuj się z zespołem deweloperskim

## 🔄 Aktualizacje

Aby zaktualizować aplikację:

```bash
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
```

## 📈 Monitorowanie

Aplikacja zawiera wbudowane narzędzia monitorowania:
- Logi aplikacji
- Metryki wydajności
- Analityka użytkowników
- Raporty błędów

---

**Wysonda** - Wiarygodne sondaże polityczne dla demokratycznego społeczeństwa.
