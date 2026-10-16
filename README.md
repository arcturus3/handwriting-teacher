# [Handwriting Teacher](betterletters.app)
[betterletters.app/](https://betterletters.app/)

**HackMIT 2023 Education Track Winner**

An adaptive handwriting practice app that uses OCR and sequence alignment to track your progress and generate personalized practice sentences.

## How It Works

1. **Get a sentence** - GPT-6 Luna (low reasoning effort) generates a practice sentence weighted toward letters you struggle with
2. **Write it** - Draw on the canvas or upload a photo of your handwriting. On a phone or tablet, **Full screen** turns the whole screen into the canvas
3. **Get feedback** - PaddleOCR reads your writing, Biopython's sequence alignment scores accuracy
4. **Improve** - Character mastery grid updates, new sentences focus on weak letters

## Tech Stack

- **Backend**: Flask, PaddleOCR, Biopython (pairwise sequence alignment), OpenAI GPT-6 Luna
- **Frontend**: Vanilla JS, p5.js for drawing canvas
- **ML**: PaddleOCR for handwriting recognition (PP-OCRv6 for English, PP-OCRv5 for Russian and Arabic)

## Setup

```bash
# Clone and enter directory
git clone https://github.com/arcturus3/handwriting-teacher.git
cd handwriting-teacher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the app
python app.py
```

Visit `http://localhost:5123`

Tests: `OPENAI_API_KEY=test python -m pytest`. The phone-layout tests in `fullscreen_test.py`
drive headless Chromium and run only where Playwright is installed
(`pip install playwright && playwright install chromium-headless-shell`); the Docker build skips them.

## Analytics

Usage goes to the Umami instance at [analytics.davidteju.dev](https://analytics.davidteju.dev)
(website "BetterLetters").

- **Page views:** Umami's script in each page under `static/`. It counts only on
  betterletters.app, so local runs stay out of the numbers.
- **Practice events:** sent from the server by `analytics.py`, so ad blockers can't hide them.
  They are filed under the page `/practice`:

| Event | Data |
| --- | --- |
| `language-changed` | `language` |
| `sentence-generated` | `language`, `ms` (generation time) |
| `sentence-failed` | `language`, `error` (exception type) |
| `submission-scored` | `language`, `letters`, `matched`, `read_anything`, `ocr_ms` |

Events carry counts only: no handwriting, sentence or recognized text leaves the server.
Server events are off unless `UMAMI_URL` and `UMAMI_WEBSITE_ID` are set (see `.env.example`).

Umami counts a visitor by address and User-Agent, so each event is sent with those of the browser
whose request caused it (nginx's `X-Real-IP` and the request's `User-Agent`), and lands in that
browser's visit, with its location. An event sent outside a request goes out as the server, with
a Beaker Browser User-Agent: Umami ignores bots, and nobody uses Beaker, so it stands out.

## Deployment

Docker:
```bash
docker build -t handwriting-teacher .
docker run -p 5123:5123 -e OPENAI_API_KEY=your_key handwriting-teacher
```

Or deploy directly to Railway/Render with the included Dockerfile.

## Team

Built at HackMIT 2023 by:
- [David Tejuosho](https://devpost.com/DavidTeju)
- [Arti Schmidt](https://devpost.com/arcturus3)
- [Hannah Park-Kaufmann](https://devpost.com/hakuupi)
- [Elliot Harris](https://devpost.com/elliotmharris)

## Links

- [Devpost](https://devpost.com/software/handwriting-teacher)
