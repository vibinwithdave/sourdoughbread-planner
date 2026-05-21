"""
Sourdough Bread Planner - Flask Application

A web-based tool for generating detailed sourdough baking schedules
with precise timing, temperature-aware fermentation estimates, and
ingredient calculations driven by the starter amount.
"""

from flask import Flask, render_template, request, jsonify
import os

from sourdough_planner.calculator import IngredientCalculator
from sourdough_planner.timeline import TimelineGenerator

# Create Flask app
app = Flask(__name__)

# Initialize modules
calculator = IngredientCalculator()
timeline_gen = TimelineGenerator()


@app.route('/')
def index():
    """Serve the main planner page."""
    try:
        feeding_ratios = calculator.get_feeding_ratios()
        step_definitions = timeline_gen.get_step_definitions()
        return render_template('index.html',
                               feeding_ratios=feeding_ratios,
                               step_definitions=step_definitions)
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms."""
    return jsonify({'status': 'healthy', 'version': '2.1.0'})


@app.route('/api/ratios')
def get_ratios():
    """Return available feeding ratios."""
    try:
        return jsonify({
            'success': True,
            'ratios': calculator.get_feeding_ratios(),
            'details': calculator.FEEDING_RATIOS
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/steps')
def get_steps():
    """Return step definitions for frontend configuration."""
    try:
        return jsonify({
            'success': True,
            'steps': timeline_gen.get_step_definitions()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/preview', methods=['POST'])
def preview_recipe():
    """
    Live preview endpoint: derive flour, water, salt from starter amount
    and fermentation speed (or custom percentages).
    """
    try:
        data = request.json or {}
        starter_amount = float(data.get('starter_amount', 100))
        speed = data.get('fermentation_speed', 'fast')
        salt_percent = float(data.get('salt_percent', 2.2))

        if speed and speed != 'custom' and speed in calculator.SPEED_RATIOS:
            recipe = calculator.derive_recipe_from_speed(
                starter_amount=starter_amount,
                speed=speed,
                salt_percent=salt_percent
            )
        else:
            starter_percent = float(data.get('starter_percent', 20))
            hydration = float(data.get('hydration', 75))
            recipe = calculator.derive_recipe_from_starter(
                starter_amount=starter_amount,
                starter_percent=starter_percent,
                hydration=hydration,
                salt_percent=salt_percent
            )
        return jsonify({'success': True, 'recipe': recipe})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/estimate-bulk', methods=['POST'])
def estimate_bulk():
    """Estimate bulk fermentation time for a given temperature."""
    try:
        data = request.json or {}
        temperature_f = float(data.get('temperature_f', 70))
        hours = timeline_gen.estimate_bulk_fermentation_hours(temperature_f)
        return jsonify({
            'success': True,
            'temperature_f': temperature_f,
            'estimated_hours': hours
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate_schedule():
    """Generate a complete baking schedule with ingredients and timeline."""
    try:
        data = request.json if request.is_json else request.form.to_dict()

        # Primary inputs: starter amount + speed drives the recipe
        starter_amount = float(data.get('starter_amount', 100))
        speed = data.get('fermentation_speed', 'fast')
        salt_percent = float(data.get('salt_percent', 2.2))
        # Custom mode fallbacks
        starter_percent = float(data.get('starter_percent', 20)) if speed == 'custom' else None
        hydration = float(data.get('hydration', 75)) if speed == 'custom' else None
        existing_starter_amount = float(data.get('existing_starter_amount', 50))
        feeding_ratio = data.get('feeding_ratio', '1:1:1')
        start_time = data.get('start_time', '8:00 PM')
        temperature_f = float(data.get('temperature_f', 70))
        cold_proof_hours = float(data.get('cold_proof_hours', 24))
        flour_type = data.get('flour_type', 'bread flour')

        # Parse enabled steps (toggleable steps)
        enabled_steps = {}
        if 'enabled_steps' in data:
            enabled_steps = data['enabled_steps']
            if isinstance(enabled_steps, str):
                import json
                enabled_steps = json.loads(enabled_steps)

        # Parse custom durations
        custom_durations = {}
        if 'custom_durations' in data:
            custom_durations = data['custom_durations']
            if isinstance(custom_durations, str):
                import json
                custom_durations = json.loads(custom_durations)

        # Validate feeding ratio
        if feeding_ratio not in calculator.FEEDING_RATIOS:
            return jsonify({'success': False,
                            'error': f'Invalid feeding ratio: {feeding_ratio}'}), 400

        # Calculate ingredients (starter-amount + speed driven)
        ingredients = calculator.calculate_ingredients(
            starter_amount=starter_amount,
            existing_starter_amount=existing_starter_amount,
            feeding_ratio=feeding_ratio,
            speed=speed if speed != 'custom' else None,
            starter_percent=starter_percent,
            hydration=hydration,
            salt_percent=salt_percent
        )

        # Get peak hours for the feeding ratio
        peak_hours = calculator.FEEDING_RATIOS[feeding_ratio]['peak_hours']

        # Generate timeline
        timeline_days = timeline_gen.generate_timeline(
            start_time_str=start_time,
            feeding_ratio_peak_hours=peak_hours,
            temperature_f=temperature_f,
            cold_proof_hours=cold_proof_hours,
            enabled_steps=enabled_steps,
            custom_durations=custom_durations
        )

        # Estimate bulk fermentation for display
        bulk_estimate = timeline_gen.estimate_bulk_fermentation_hours(temperature_f)

        return jsonify({
            'success': True,
            'ingredients': ingredients,
            'timeline': timeline_days,
            'settings': {
                'flour_type': flour_type,
                'feeding_ratio': feeding_ratio,
                'feeding_ratio_description': calculator.FEEDING_RATIOS[feeding_ratio]['description'],
                'temperature_f': temperature_f,
                'bulk_fermentation_estimate': bulk_estimate,
                'cold_proof_hours': cold_proof_hours,
                'hydration': ingredients['actual_hydration'],
                'fermentation_speed': speed
            }
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
