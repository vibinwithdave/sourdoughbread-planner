# 🍞 Sourdough Baking Planner

A web-based tool for generating detailed sourdough baking schedules with precise timing, temperature-aware fermentation estimates, and ingredient calculations based on baker's percentages.

This planner is heavily inspired by the [Alexandra Cooks Artisan Sourdough Method](https://alexandracooks.com/2017/10/24/artisan-sourdough-made-simple-sourdough-bread-demystified-a-beginners-guide-to-sourdough-baking/), emphasizing visual cues, temperature awareness, and long cold proofs.

## Features

- 📊 **Starter-Centric Calculations**: Input your desired total flour weight, and the app calculates the exact starter feeding required to produce enough active starter for the recipe *plus* a remainder for your next bake.
- 🌡️ **Temperature-Aware Fermentation**: Bulk fermentation time is dynamically estimated based on your ambient kitchen temperature.
- ⏰ **Modular Timeline**: Toggle specific steps (like Autolyse or Pre-shape) on or off to match your preferred baking method.
- 📱 **Visual UI**: A clean, responsive interface with a visual timeline and clear separation of starter feeding vs. main dough mixing.

## Architecture

The application is built with a modular architecture:

- **Backend**: Python/Flask
  - `sourdough_planner/calculator.py`: Handles baker's percentage math and starter feeding logic.
  - `sourdough_planner/timeline.py`: Generates the chronological schedule and temperature estimates.
  - `app.py`: Thin routing layer exposing the API and serving the frontend.
- **Frontend**: Vanilla HTML/CSS/JS
  - `templates/index.html`: The main user interface.
  - `static/css/style.css`: Custom styling with CSS variables.
  - `static/js/app.js`: Client-side logic for live updates and API interaction.

## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/vibinwithdave/sourdoughbread-planner.git
   cd sourdoughbread-planner
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://localhost:10000`

### Running Tests

The project includes a comprehensive test suite using `pytest`.

```bash
# Run all tests
pytest tests/

# Run tests with coverage report
pytest --cov=sourdough_planner tests/
```

## Deployment

This application is configured for deployment on platforms like Render or Heroku. It includes a `Procfile` specifying `gunicorn` as the WSGI HTTP Server.

```
web: gunicorn app:app
```
