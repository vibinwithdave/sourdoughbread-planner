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
            'description': 'Let the pre-shaped dough rest seam-side up, uncovered on the counter.',
            'visual_cue': 'Dough will relax and spread slightly. Seam-side should be facing up. It should still hold a general round shape.',
            'category': 'shaping',
            'toggleable': True,
            'default_enabled': True,
            'default_duration_minutes': 30
        },
        'final_shape': {
            'name': 'Final Shape',
            'description': 'Shape dough into final form (round or batard) and place seam-side up in a floured banneton or lined bowl.',
            'visual_cue': 'Dough should feel taut with good surface tension. Seam-side faces up in the banneton.',
            'category': 'shaping',
            'toggleable': False,
            'default_enabled': True,
            'default_duration_minutes': 5
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
        'remove_from_fridge': {
            'name': 'Remove from Fridge',
            'description': 'Take the cold-proofed dough out of the refrigerator. You can bake it straight from the fridge — no need to warm up.',
            'visual_cue': 'Dough should be slightly puffed and hold its shape. It will feel firm and cold.',
            'category': 'proofing',
            'toggleable': False,
            'default_enabled': True
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
                          start_date=None, fold_interval_minutes=30,
                          start_from='feed_starter'):
        """
        Generate a complete baking timeline.

        Args:
            start_time_str: The user's start time (e.g., "8:00 AM")
            feeding_ratio_peak_hours: Hours for starter to reach peak
            temperature_f: Ambient kitchen temperature in °F
            cold_proof_hours: Duration of cold proof in hours (1-48)
            enabled_steps: Dict of step_id -> bool for toggleable steps
            custom_durations: Dict of step_id -> minutes for customizable steps
            start_date: Date to start (defaults to today)
            fold_interval_minutes: Minutes between stretch and fold sets
            start_from: Either 'feed_starter' or 'mix_dough'. If 'mix_dough',
                        the start_time_str is when the user wants to mix, and
                        the feeding time is back-calculated from peak_hours.

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
        user_dt = datetime.combine(start_date, start_time)

        # Determine the feed_starter datetime based on start_from mode
        if start_from == 'mix_dough':
            # User provided the time they want to mix dough.
            # Mix happens when starter is at peak, so feed time = mix_time - peak_hours
            current_dt = user_dt - timedelta(hours=feeding_ratio_peak_hours)
        else:
            # Default: user provided the time they will feed the starter
            current_dt = user_dt

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
        # Bulk fermentation starts 30 min after the last fold.
        # The displayed time is when bulk fermentation BEGINS.
        current_dt += timedelta(minutes=fold_interval_minutes)
        timeline.append(self._make_entry('bulk_fermentation', current_dt,
                                         note=f'~{bulk_hours} hours at {temperature_f}°F. '
                                              f'Look for 50-75% volume increase.'))

        # 11. Pre-shape happens after bulk fermentation duration elapses
        current_dt += timedelta(hours=bulk_hours)
        if is_enabled('pre_shape'):
            timeline.append(self._make_entry('pre_shape', current_dt))

        # 12. Bench Rest (5 min after pre-shape, lasts 30 min)
        if is_enabled('bench_rest'):
            current_dt += timedelta(minutes=5)
            bench_duration = get_duration('bench_rest')
            timeline.append(self._make_entry('bench_rest', current_dt,
                                             note=f'{bench_duration} min rest, seam-side up'))
            current_dt += timedelta(minutes=bench_duration)

        # 13. Final Shape (starts after bench rest completes)
        timeline.append(self._make_entry('final_shape', current_dt))
        final_shape_duration = get_duration('final_shape')
        current_dt += timedelta(minutes=final_shape_duration)

        # 14. Cold Proof (starts 5 min after final shape begins — time to place in fridge)
        timeline.append(self._make_entry('cold_proof', current_dt,
                                         note=f'{cold_proof_hours} hours in fridge. '
                                              f'Longer = more flavor and lighter crumb.'))

        # 15. Preheat Oven (starts 45 min before cold proof ends)
        preheat_duration = get_duration('preheat_oven')
        cold_proof_end = current_dt + timedelta(hours=cold_proof_hours)
        preheat_start = cold_proof_end - timedelta(minutes=preheat_duration)
        timeline.append(self._make_entry('preheat_oven', preheat_start,
                                         note=f'Start {preheat_duration} min before baking. '
                                              f'Preheat to 550°F with Dutch oven inside.'))

        # 16. Remove from Fridge (after cold proof hours elapse)
        current_dt = cold_proof_end
        timeline.append(self._make_entry('remove_from_fridge', current_dt,
                                         note='Bake straight from fridge — no need to warm up.'))

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

    def recalculate_from_step(self, timeline_flat, edited_step_index, new_datetime_str,
                              temperature_f=70, cold_proof_hours=24,
                              enabled_steps=None, custom_durations=None,
                              fold_interval_minutes=30):
        """
        Recalculate the timeline from an edited step onward.

        Takes the flat timeline (list of step dicts), the index of the edited step,
        and the new datetime for that step. All subsequent steps are recalculated
        using the default timing offsets.

        Args:
            timeline_flat: List of step dicts (flat, not grouped by day)
            edited_step_index: Index of the step that was edited
            new_datetime_str: New ISO datetime string for the edited step
            temperature_f: Kitchen temperature for bulk fermentation calc
            cold_proof_hours: Cold proof duration
            enabled_steps: Dict of toggleable step states
            custom_durations: Dict of custom durations
            fold_interval_minutes: Minutes between folds

        Returns:
            Updated timeline grouped by day
        """
        if enabled_steps is None:
            enabled_steps = {}
        if custom_durations is None:
            custom_durations = {}

        bulk_hours = self.estimate_bulk_fermentation_hours(temperature_f)
        cold_proof_hours = max(1, min(48, cold_proof_hours))

        def get_duration(step_id, default_key='default_duration_minutes'):
            if step_id in custom_durations:
                return custom_durations[step_id]
            return self.STEP_DEFINITIONS[step_id].get(default_key, 0)

        # Keep all steps up to and including the edited one unchanged
        # Update the edited step's time
        new_dt = datetime.fromisoformat(new_datetime_str)
        timeline_flat[edited_step_index]['datetime'] = new_dt.isoformat()
        timeline_flat[edited_step_index]['time_display'] = new_dt.strftime('%I:%M %p').lstrip('0')
        timeline_flat[edited_step_index]['date_display'] = new_dt.strftime('%A, %B %d')

        # Recalculate all steps after the edited one
        current_dt = new_dt
        edited_step_id = timeline_flat[edited_step_index]['step_id']

        # Define the offset rules for each step transition
        # Each step knows how much time passes before the NEXT step
        for i in range(edited_step_index + 1, len(timeline_flat)):
            prev_step_id = timeline_flat[i - 1]['step_id']
            curr_step_id = timeline_flat[i]['step_id']

            # Calculate the offset from the previous step
            offset = self._get_offset_between_steps(
                prev_step_id, curr_step_id,
                get_duration=get_duration,
                bulk_hours=bulk_hours,
                cold_proof_hours=cold_proof_hours,
                fold_interval_minutes=fold_interval_minutes,
                temperature_f=temperature_f
            )

            current_dt = current_dt + timedelta(minutes=offset)

            # Special case: preheat_oven is calculated relative to cold_proof end
            if curr_step_id == 'preheat_oven':
                # Find the cold_proof step to calculate preheat relative to it
                cold_proof_entry = None
                for j in range(i):
                    if timeline_flat[j]['step_id'] == 'cold_proof':
                        cold_proof_entry = timeline_flat[j]
                if cold_proof_entry:
                    cold_proof_start = datetime.fromisoformat(cold_proof_entry['datetime'])
                    cold_proof_end = cold_proof_start + timedelta(hours=cold_proof_hours)
                    preheat_duration = get_duration('preheat_oven')
                    current_dt = cold_proof_end - timedelta(minutes=preheat_duration)

            timeline_flat[i]['datetime'] = current_dt.isoformat()
            timeline_flat[i]['time_display'] = current_dt.strftime('%I:%M %p').lstrip('0')
            timeline_flat[i]['date_display'] = current_dt.strftime('%A, %B %d')

        return self._group_by_day(timeline_flat)

    def _get_offset_between_steps(self, prev_step_id, curr_step_id,
                                   get_duration, bulk_hours, cold_proof_hours,
                                   fold_interval_minutes, temperature_f):
        """
        Return the offset in minutes between two consecutive steps.
        This encodes the same timing logic as generate_timeline.
        """
        # Feed starter -> Starter at peak: peak_hours (handled by caller)
        # Starter at peak -> Mix dough: 0 (immediate)
        if prev_step_id == 'starter_at_peak' and curr_step_id == 'mix_dough':
            return 0
        # Mix dough -> Rest after mix: mix duration (10 min)
        if prev_step_id == 'mix_dough' and curr_step_id == 'rest_after_mix':
            return get_duration('mix_dough')
        # Rest after mix -> Stretch fold 1: rest duration (30 min)
        if prev_step_id == 'rest_after_mix' and curr_step_id == 'stretch_fold_1':
            return get_duration('rest_after_mix')
        # Mix dough -> Stretch fold 1 (if rest is disabled): mix duration
        if prev_step_id == 'mix_dough' and curr_step_id == 'stretch_fold_1':
            return get_duration('mix_dough')
        # Fold -> Fold: fold_interval
        if 'stretch_fold' in prev_step_id and 'stretch_fold' in curr_step_id:
            return fold_interval_minutes
        # Last fold -> Bulk fermentation: fold_interval (30 min)
        if 'stretch_fold' in prev_step_id and curr_step_id == 'bulk_fermentation':
            return fold_interval_minutes
        # Bulk fermentation -> Pre-shape: bulk_hours
        if prev_step_id == 'bulk_fermentation' and curr_step_id == 'pre_shape':
            return int(bulk_hours * 60)
        # Pre-shape -> Bench rest: 5 min
        if prev_step_id == 'pre_shape' and curr_step_id == 'bench_rest':
            return 5
        # Bench rest -> Final shape: bench duration (30 min)
        if prev_step_id == 'bench_rest' and curr_step_id == 'final_shape':
            return get_duration('bench_rest')
        # Final shape -> Cold proof: final_shape duration (5 min)
        if prev_step_id == 'final_shape' and curr_step_id == 'cold_proof':
            return get_duration('final_shape')
        # Cold proof -> Preheat oven: handled specially above
        if prev_step_id == 'cold_proof' and curr_step_id == 'preheat_oven':
            return 0  # Will be overridden by special case
        # Preheat oven -> Remove from fridge: preheat_duration
        if prev_step_id == 'preheat_oven' and curr_step_id == 'remove_from_fridge':
            return get_duration('preheat_oven')
        # Remove from fridge -> Score and bake: 0 (immediate)
        if prev_step_id == 'remove_from_fridge' and curr_step_id == 'score_and_bake':
            return 0
        # Score and bake -> Bake uncovered: 30 min
        if prev_step_id == 'score_and_bake' and curr_step_id == 'bake_uncovered':
            return get_duration('score_and_bake')
        # Bake uncovered -> Cooling: 15 min
        if prev_step_id == 'bake_uncovered' and curr_step_id == 'cooling':
            return get_duration('bake_uncovered')
        # Cooling -> Ready: 60 min
        if prev_step_id == 'cooling' and curr_step_id == 'ready':
            return get_duration('cooling')
        # Autolyse special case
        if curr_step_id == 'autolyse':
            return 0
        # Feed starter -> Starter at peak (use peak hours from feeding ratio)
        if prev_step_id == 'feed_starter' and curr_step_id == 'starter_at_peak':
            return 0  # This is handled by the caller providing the correct datetime

        # Default: 0 offset
        return 0

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
        """Parse time string in multiple formats: 24-hour (HH:MM), 12-hour with/without space."""
        time_str = time_str.strip()

        # Try 24-hour format first (HH:MM) - from <input type="time">
        if len(time_str) == 5 and time_str[2] == ':' and time_str[:2].isdigit() and time_str[3:].isdigit():
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                pass

        # Also try 24-hour without leading zero (e.g., "8:30")
        time_upper = time_str.upper()

        # Handle no AM/PM - try as 24-hour
        if 'AM' not in time_upper and 'PM' not in time_upper:
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                # Guess AM/PM based on hour
                hour = int(time_str.split(':')[0])
                if 6 <= hour <= 11:
                    time_upper = time_str + ' AM'
                else:
                    time_upper = time_str + ' PM'
        
        # Normalize: insert space before AM/PM if missing (e.g., "9:19AM" -> "9:19 AM")
        import re
        time_upper = re.sub(r'(\d)(AM|PM)', r'\1 \2', time_upper)

        # Try standard 12-hour formats
        for fmt in ['%I:%M %p', '%I %p', '%I:%M%p']:
            try:
                return datetime.strptime(time_upper, fmt).time()
            except ValueError:
                continue

        raise ValueError(f"Invalid time format: {time_str}. Use the time picker or format like '8:00 AM'")
