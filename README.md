# ESP-Cloud

Sistem IoT pentru detectarea ocupării unui spațiu (ex. parcare) folosind senzor PIR pe **ESP32**, API **Flask** în cloud și model **MLP** (Varianta 2 – AI în Cloud).

## Arhitectură

```
ESP32 (PIR)  --POST /motion-->  Flask API  --inferență MLP-->  predicție + led_command
                                    |
                                    v
                            Azure Table Storage
```

1. ESP32 trimite `device_id` și `motion` către API.
2. API-ul rulează modelul MLP și returnează `prediction` (`occupied` / `empty`) și `led_command`.
3. Evenimentul este salvat în Azure Table Storage.

## Cerințe

- Python 3.10+
- Cont Azure Storage (Table Storage)
- ESP32 cu WiFi și senzor PIR

## Instalare

```bash
# clonează repo-ul
git clone https://github.com/HalmaghiAlexandraMaria/ESP-Cloud.git
cd ESP-Cloud

# mediu virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

## Configurare

Creează fișierul `.env` în rădăcina proiectului (nu se urcă pe GitHub):

```env
AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
TABLE_NAME=motionEvents
```

## Antrenare model MLP

```bash
python train_model.py
```

Generează `models/occupancy_mlp.pkl`. Rulează o dată după clone sau când reantrenezi modelul.

## Pornire API

```bash
python app.py
```

Serverul rulează pe `http://0.0.0.0:5000`. În codul ESP32, setează `serverUrl` la IP-ul PC-ului din rețea, de exemplu:

```
http://192.168.x.x:5000/motion
```

## Endpoints API

| Metodă | URL | Descriere |
|--------|-----|-----------|
| `POST` | `/motion` | Primește eveniment de la ESP32, rulează MLP, salvează în Azure |
| `GET` | `/api/events` | Listează evenimentele salvate |
| `GET` | `/api/model` | Status model ML încărcat |

### Exemplu `POST /motion`

**Request:**
```json
{
  "device_id": "esp32_pir_1",
  "motion": true
}
```

**Response:**
```json
{
  "message": "Event added successfully",
  "event": {
    "id": "...",
    "device_id": "esp32_pir_1",
    "motion": true,
    "received_at": "2026-05-22T12:00:00+00:00"
  },
  "prediction": "occupied",
  "led_command": true,
  "confidence": 0.95,
  "model": "MLP"
}
```

## ESP32 (Arduino)

Codul firmware este în `proiect/proiect.ino`.

1. Deschide folderul `proiect/` în **Arduino IDE** (Fișier → Deschide → `proiect.ino`).
2. Editează `ssid`, `password` și `serverUrl` (IP-ul PC-ului cu Flask).
3. Placă: **ESP32**, PIR pe pin 14, LED pe pin 33.
4. Încarcă sketch-ul pe placă.

Dispozitivul trimite JSON la schimbarea stării PIR și controlează LED-ul după `led_command` din răspunsul API.

## Structură proiect

```
ESP-Cloud/
├── app.py              # Flask API
├── train_model.py      # Antrenare MLP
├── requirements.txt
├── proiect/
│   └── proiect.ino     # Firmware ESP32
├── ml/
│   ├── features.py     # Extragere features
│   └── predictor.py    # Încărcare model + predict()
├── models/
│   └── occupancy_mlp.pkl
└── .env                # local only (gitignore)
```

## Componenta AI

- **Varianta:** AI în Cloud (Flask + scikit-learn MLP)
- **Input:** `motion` (de la ESP32) + context temporal (oră, weekend) calculat în API
- **Output:** clasificare `occupied` / `empty` → comandă LED

## Autor

Halmaghi Alexandra Maria
