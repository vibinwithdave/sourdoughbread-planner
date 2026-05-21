"""
Timeline generator for sourdough bread planning.

Generates dynamic, temperature-aware baking schedules with modular,
toggleable steps. Users can enable/disable steps and customize durations.
"""

from datetime import datetime, timedelta


class TimelineGenerator:
    """Generate dynamic sourdough baking timelines with temperature awareness."""

    # Temperature-to-bulk-fermentation mapping (hours at given temp in °F)
    # Based on common sourdough baking experience and the Alexandra Cooks method
    BULK_FERMENTATION_HOURS = {
        65: 12.0,   # Cold kitchen - very slow fermentation
        68: 10.0,   # Cool kitchen
        70: 9.0,    # Standard room temp (Alexandra Cooks baseline)
        72: 8.0,    # Slightly warm
        75: 7.0,    # Warm kitchen
        78: 6.0,    # Hot kitchen (Alexandra Cooks summer note)
        80: 5.0,    # Very warm
        82: 4.5,    # Very hot
        85: 4.0,    # Extremely warm
    }

    # Step definitions with metadata
    STEP_DEFINITIONS = {
        'feed_starter': {
            'name': 'Feed Starter',
            'description': 'Add flour and water to your existing starter at the specified ratio.',
            'visual_cue': 'Mark the level with a rubber band to track growth.',
            'category': 'preparation',
            'toggleable': False,
            'default_enabled': True
        },
        'starter_at_peak': {
            'name': 'Starter at Peak',
            'description': 'Starter should be bubbly, domed, and at peak activity.',
            'visual_cue': 'Look for the starter to have doubled in volume and show lots of bubbles on the surface and sides.',
            'category': 'preparation',
            'toggleable': False,
            'default_enabled': True
        },
        'autolyse': {
            'name': 'Autolyse',
            'description': 'Mix flour and water only (no starter or salt). Let rest to hydrate flour and develop gluten.',
            'visual_cue': 'Dough should feel smoother and more cohesive after resting.',
            'category': 'mixing',
            'toggleable': True,
            'default_enabled': False,
            'default_duration_minutes': 30
        },
        'mix_dough': {
            'name': 'Mix Dough',
            'description': 'Whisk starter and water together, then add flour and salt. Mix to form a rough, shaggy dough.',
            'visual_cue': 'All flour should be incorporated. Dough will be sticky and rough — this is normal.',
            'category': 'mixing',
            'toggleable': False,
            'default_enabled': True,
            'default_duration_minutes': 10
        },
        'rest_after_mix': {
            'name': 'Rest After Mixing',
            'description': 'Cover dough and let it rest before beginning stretch and folds.',
            'visual_cue': 'Dough will relax and become slightly smoother.',
            'category': 'mixing',
            'toggleable': True,
            'default_enabled': True,
            'default_duration_minutes': 30
        },
        'stretch_fold_1': {
            'name': 'Stretch & Fold #1',
            'description': 'Grab a corner of the dough, pull it up and fold into the center. Repeat 4-5 times around the dough.',
            'visual_cue': 'Dough will feel tighter and more elastic after folding.',
            'category': 'development',
            'toggleable': True,
            'default_enabled': True
        },
        'stretch_fold_2': {
            'name': 'Stretch & Fold #2',
            'description': 'Second set of stretch and folds. Dough should be getting noticeably stronger.',
            'visual_cue': 'Dough resists stretching more than the first set.',
            'category': 'development',
            'toggleable': True,
            'default_enabled': True
        },
        'stretch_fold_3': {
            'name': 'Stretch & Fold #3',
            'description': 'Third set of stretch and folds.',
            'visual_cue': 'Dough should feel smooth and hold its shape better.',
            'category': 'development',
            'toggleable': True,
            'default_enabled': True
        },
        'stretch_fold_4': {
            'name': 'Stretch & Fold #4',
            'description': 'Final set of stretch and folds. Dough should be strong and elastic.',
            'visual_cue': 'Dough should be noticeably smoother, stronger, and more billowy than when you started.',
            'category': 'development',
            'toggleable': True,
            'default_enabled': True
        },
        'bulk_fermentation': {
            'name': 'Bulk Fermentation',
            'description': 'Cover dough and let it rise at room temperature. Time varies by temperature.',
            'visual_cue': 'Look for a 50-75% increase in volume. Dough should have bubbles on the surface and jiggle when you move the container.',
            'category': 'fermentation',
            'toggleable': False,
            'default_enabled': True
        },
        'pre_shape': {
            'name': 'Pre-shape',
            'description': 'Gently turn dough onto a lightly floured surface. Shape into a loose round using a bench scraper.',
            'visual_cue': 'Dough should hold a rough round shape but will spread slightly.',
            'category': 'shaping',
            'toggleable': True,
            'default_enabled': True
        },
        'bench_rest': {
            'name': 'Bench Rest',
            'description': 'Let the pre-shaped dough rest uncovered on the counter.',
            'visual_cue': 'Dough will relax and spread slightly. It should still hold a general round shape.',
            'category': 'shaping',
            'toggleable': True,
            'default_enabled': True,
            'default_duration_minutes': 30
        },
        'final_shape': {
            'name': 'Final Shape',
            'description': 'Shape dough into final form (round or batard) and place seam-side up in a floured banneton or lined bowl.',
            'visual_cue': 'Dough should feel taut with good surface tension.',
            'category': 'shaping',
            'toggleable': False,
            'default_enabled': True
        },
        'cold_proof': {
            'name': 'Cold Proof (Retard)',
            'description': 'Cover and refrigerate the shaped dough. Longer proofing develops more flavor and a lighter crumb.',
            'visual_cue': 'After 24+ hours, dough should be slightly puffed but still hold its shape when poked.',
            'category': 'proofing',
            'toggleable': False,
            'default_enabled': True,
            'default_duration_hours': 24,
            'min_duration_hours': 1,
            'max_duration_hours': 48
        },
        'preheat_oven': {
            'name': 'Preheat Oven & Dutch Oven',
            'description': 'Place Dutch oven inside and preheat to 550°F (290°C). Allow at least 30 minutes for the Dutch oven to fully heat.',
            'visual_cue': 'Oven should be at full temperature for at least 30 minutes before baking.',
            'category': 'baking',
            'toggleable': False,
            'default_enabled': True,
            'default_duration_minutes': 45
        },
        'score_and_bake': {
            'name': 'Score & Bake (Covered)',
            'description': 'Turn dough onto parchment, score with a razor blade or sharp knife. Transfer to preheated Dutch oven. Lower oven to 450°F (230°C). Bake covered for 30 minutes.',
            'visual_cue': 'Bread should spring up dramatically in the first 15 minutes (oven spring).',
            'category': 'baking',
            'toggleable': False,
            'default_enabled': True,
            'default_duration_minutes': 30
        },
        'bake_uncovered': {
            'name': 'Bake (Uncovered)',
            'description': 'Remove lid, lower temperature to 400°F (200°C). Bake for 10-15 minutes until deep golden brown.',
            'visual_cue': 'Crust should be deep golden to dark brown. Internal temperature should reach 205-210°F.',
            'category': 'baking',
            'toggleable': False,
            'default_enabled': True,
            'default_duration_minutes': 15
        },
        'cooling': {
            'name': 'Cool Before Slicing',
            'description': 'Remove from Dutch oven and cool on a wire rack. Resist cutting for at least 1 hour — the bread is still baking inside!',
            'visual_cue': 'Bread will crackle as it cools (the "singing" of fresh bread). Wait until it feels warm but not hot.',
            'category': 'finishing',
            'toggleable': False,
            'default_enabled': True,
            'default_duration_minutes': 60
        }
    }

    def __init__(self):
        pass

    def estimate_bulk_fermentation_hours(self, temperature_f):
        """
        Estimate bulk fermentation time based on ambient kitchen temperature.

        Uses linear interpolation between known data points.

        Args:
            temperature_f: Kitchen temperature in Fahrenheit

        Returns:
            Estimated hours for bulk fermentation
        """
        temps = sorted(self.BULK_FERMENTATION_HOURS.keys())

        # Clamp to known range
        if temperature_f <= temps[0]:
            return self.BULK_FERMENTATION_HOURS[temps[0]]
        if temperature_f >= temps[-1]:
            return self.BULK_FERMENTATION_HOURS[temps[-1]]

        # Find bracketing temperatures and interpolate
        for i in range(len(temps) - 1):
            if temps[i] <= temperature_f <= temps[i + 1]:
                t_low, t_high = temps[i], temps[i + 1]
                h_low = self.BULK_FERMENTATION_HOURS[t_low]
                h_high = self.BULK_FERMENTATION_HOURS[t_high]
                # Linear interpolation
                fraction = (temperature_f - t_low) / (t_high - t_low)
                return round(h_low + fraction * (h_high - h_low), 1)

        return 9.0  # Fallback

    def get_step_definitions(self):
        """Return all step definitions for frontend configuration."""
        return self.STEP_DEFINITIONS

    def generate_timeline(self, start_time_str, feeding_ratio_peak_hours,
                          temperature_f=70, cold_proof_hours=24,
                          enabled_steps=None, custom_durations=None,
                          start_date=None, fold_interval_minutes=30):
        """
        Generate a complete baking timeline.

        Args:
            start_time_str: Time to feed starter (e.g., "8:00 AM")
            feeding_ratio_peak_hours: Hours for starter to reach peak
            temperature_f: Ambient kitchen temperature in °F
            cold_proof_hours: Duration of cold proof in hours (1-48)
            enabled_steps: Dict of step_id -> bool for toggleable steps
            custom_durations: Dict of step_id -> minutes for customizable steps
            start_date: Date to start (defaults to today)
            fold_interval_minutes: Minutes between stretch and fold sets

        Returns:
            List of timeline entries with datetime, step info, and visual cues
        """
        if start_date is None:
            start_date = datetime.now().date()

        if enabled_steps is None:
            enabled_steps = {}

        if custom_durations is None:
            custom_durations = {}

        # Parse start time
        start_time = self._parse_time(start_time_str)
        current_dt = datetime.combine(start_date, start_time)

        # Calculate bulk fermentation time based on temperature
        bulk_hours = self.estimate_bulk_fermentation_hours(temperature_f)

        # Clamp cold proof hours
        cold_proof_hours = max(1, min(48, cold_proof_hours))

        timeline = []

        # Helper to check if a step is enabled
        def is_enabled(step_id):
            step_def = self.STEP_DEFINITIONS[step_id]
            if not step_def['toggleable']:
                return step_def['default_enabled']
            return enabled_steps.get(step_id, step_def['default_enabled'])

        # Helper to get duration
        def get_duration(step_id, default_key='default_duration_minutes'):
            if step_id in custom_durations:
                return custom_durations[step_id]
            return self.STEP_DEFINITIONS[step_id].get(default_key, 0)

        # --- Build Timeline ---

        # 1. Feed Starter
        timeline.append(self._make_entry('feed_starter', current_dt))

        # 2. Starter at Peak
        current_dt += timedelta(hours=feeding_ratio_peak_hours)
        timeline.append(self._make_entry('starter_at_peak', current_dt))

        # 3. Autolyse (optional - can be started before starter peaks)
        if is_enabled('autolyse'):
            autolyse_duration = get_duration('autolyse')
            # Autolyse starts before starter is ready so it's done when starter peaks
            autolyse_start = current_dt - timedelta(minutes=autolyse_duration)
            timeline.append(self._make_entry('autolyse', autolyse_start,
                                             note=f'Start {autolyse_duration} min before starter peaks'))

        # 4. Mix Dough (takes ~10 minutes)
        timeline.append(self._make_entry('mix_dough', current_dt))
        mix_duration = get_duration('mix_dough')
        current_dt += timedelta(minutes=mix_duration)

        # 5. Rest After Mixing (starts after mix is complete)
        if is_enabled('rest_after_mix'):
            rest_duration = get_duration('rest_after_mix')
            timeline.append(self._make_entry('rest_after_mix', current_dt,
                                             note=f'{rest_duration} min rest'))
            current_dt += timedelta(minutes=rest_duration)

        # 6-9. Stretch and Folds
        # First fold happens immediately after rest ends.
        # Subsequent folds are spaced by fold_interval_minutes.
        fold_steps = ['stretch_fold_1', 'stretch_fold_2', 'stretch_fold_3', 'stretch_fold_4']
        first_fold = True
        for fold_step in fold_steps:
            if is_enabled(fold_step):
                if first_fold:
                    first_fold = False
                else:
                    current_dt += timedelta(minutes=fold_interval_minutes)
                timeline.append(self._make_entry(fold_step, current_dt))

        # 10. Bulk Fermentation
        # Bulk fermentation starts after the last fold and continues
        bulk_start = current_dt
        current_dt += timedelta(hours=bulk_hours)
        timeline.append(self._make_entry('bulk_fermentation', current_dt,
                                         note=f'~{bulk_hours} hours at {temperature_f}°F. '
                                              f'Look for 50-75% volume increase.'))

        # 11. Pre-shape
        if is_enabled('pre_shape'):
            timeline.append(self._make_entry('pre_shape', current_dt))

        # 12. Bench Rest
        if is_enabled('bench_rest'):
            bench_duration = get_duration('bench_rest')
            current_dt += timedelta(minutes=bench_duration)
            timeline.append(self._make_entry('bench_rest', current_dt,
                                             note=f'{bench_duration} min rest'))

        # 13. Final Shape
        timeline.append(self._make_entry('final_shape', current_dt))

        # 14. Cold Proof
        cold_proof_start = current_dt
        current_dt += timedelta(hours=cold_proof_hours)
        timeline.append(self._make_entry('cold_proof', current_dt,
                                         note=f'{cold_proof_hours} hours in fridge. '
                                              f'Longer = more flavor and lighter crumb.'))

        # 15. Preheat Oven
        preheat_duration = get_duration('preheat_oven')
        # Preheat starts before baking time
        preheat_start = current_dt - timedelta(minutes=preheat_duration)
        timeline.append(self._make_entry('preheat_oven', preheat_start,
                                         note=f'Start {preheat_duration} min before baking. '
                                              f'Preheat to 550°F with Dutch oven inside.'))

        # 16. Score and Bake (covered)
        timeline.append(self._make_entry('score_and_bake', current_dt,
                                         note='Lower to 450°F. Bake covered 30 min.'))
        bake_covered_duration = get_duration('score_and_bake')
        current_dt += timedelta(minutes=bake_covered_duration)

        # 17. Bake Uncovered
        timeline.append(self._make_entry('bake_uncovered', current_dt,
                                         note='Remove lid. Lower to 400°F. Bake 10-15 min.'))
        bake_uncovered_duration = get_duration('bake_uncovered')
        current_dt += timedelta(minutes=bake_uncovered_duration)

        # 18. Cooling
        timeline.append(self._make_entry('cooling', current_dt,
                                         note='Cool at least 1 hour before slicing.'))
        cooling_duration = get_duration('cooling')
        current_dt += timedelta(minutes=cooling_duration)

        # Add final "ready to eat" marker
        timeline.append({
            'step_id': 'ready',
            'name': 'Ready to Eat!',
            'datetime': current_dt.isoformat(),
            'time_display': current_dt.strftime('%I:%M %p').lstrip('0'),
            'date_display': current_dt.strftime('%A, %B %d'),
            'description': 'Your sourdough bread is ready to enjoy!',
            'visual_cue': 'Bread should sound hollow when tapped on the bottom.',
            'category': 'finishing',
            'note': ''
        })

        return self._group_by_day(timeline)

    def _make_entry(self, step_id, dt, note=''):
        """Create a timeline entry dict."""
        step_def = self.STEP_DEFINITIONS[step_id]
        return {
            'step_id': step_id,
            'name': step_def['name'],
            'datetime': dt.isoformat(),
            'time_display': dt.strftime('%I:%M %p').lstrip('0'),
            'date_display': dt.strftime('%A, %B %d'),
            'description': step_def['description'],
            'visual_cue': step_def['visual_cue'],
            'category': step_def['category'],
            'note': note
        }

    def _group_by_day(self, timeline):
        """Group timeline entries by date."""
        days = {}
        for entry in timeline:
            dt = datetime.fromisoformat(entry['datetime'])
            date_key = dt.strftime('%A, %B %d')
            if date_key not in days:
                days[date_key] = {
                    'date': date_key,
                    'date_sort': dt.date().isoformat(),
                    'steps': []
                }
            days[date_key]['steps'].append(entry)

        # Sort by date and return as list
        sorted_days = sorted(days.values(), key=lambda d: d['date_sort'])
        return sorted_days

    def _parse_time(self, time_str):
        """Parse time string in 12-hour format."""
        time_str = time_str.strip().upper()

        if not ('AM' in time_str or 'PM' in time_str):
            hour = int(time_str.split(':')[0])
            if 6 <= hour <= 11:
                time_str += ' AM'
            else:
                time_str += ' PM'

        try:
            return datetime.strptime(time_str, '%I:%M %p').time()
        except ValueError:
            try:
                return datetime.strptime(time_str, '%I %p').time()
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}. Use format like '8:00 AM'")
