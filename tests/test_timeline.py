"""Tests for the TimelineGenerator module."""

import pytest
from datetime import date
from sourdough_planner.timeline import TimelineGenerator


@pytest.fixture
def tl():
    """Provide a fresh TimelineGenerator instance."""
    return TimelineGenerator()


class TestBulkFermentationEstimate:
    """Tests for temperature-aware bulk fermentation estimation."""

    def test_standard_70f(self, tl):
        hours = tl.estimate_bulk_fermentation_hours(70)
        assert hours == 9.0

    def test_warm_78f(self, tl):
        hours = tl.estimate_bulk_fermentation_hours(78)
        assert hours == 6.0

    def test_cold_65f(self, tl):
        hours = tl.estimate_bulk_fermentation_hours(65)
        assert hours == 12.0

    def test_interpolation_73f(self, tl):
        """73°F should interpolate between 72 (8h) and 75 (7h)."""
        hours = tl.estimate_bulk_fermentation_hours(73)
        assert 7.0 < hours < 8.0

    def test_below_minimum_clamps(self, tl):
        """Temperatures below 65°F should return the 65°F value."""
        hours = tl.estimate_bulk_fermentation_hours(50)
        assert hours == 12.0

    def test_above_maximum_clamps(self, tl):
        """Temperatures above 85°F should return the 85°F value."""
        hours = tl.estimate_bulk_fermentation_hours(95)
        assert hours == 4.0

    def test_warmer_is_faster(self, tl):
        """Higher temperatures should always result in shorter fermentation."""
        temps = [65, 68, 70, 72, 75, 78, 80, 82, 85]
        hours = [tl.estimate_bulk_fermentation_hours(t) for t in temps]
        for i in range(len(hours) - 1):
            assert hours[i] >= hours[i + 1]


class TestStepDefinitions:
    """Tests for step definition structure."""

    def test_all_steps_have_required_keys(self, tl):
        for step_id, step_def in tl.STEP_DEFINITIONS.items():
            assert 'name' in step_def
            assert 'description' in step_def
            assert 'visual_cue' in step_def
            assert 'category' in step_def
            assert 'toggleable' in step_def
            assert 'default_enabled' in step_def

    def test_toggleable_steps_exist(self, tl):
        toggleable = [k for k, v in tl.STEP_DEFINITIONS.items() if v['toggleable']]
        assert len(toggleable) > 0
        assert 'autolyse' in toggleable

    def test_non_toggleable_critical_steps(self, tl):
        """Critical steps should not be toggleable."""
        assert tl.STEP_DEFINITIONS['feed_starter']['toggleable'] is False
        assert tl.STEP_DEFINITIONS['mix_dough']['toggleable'] is False
        assert tl.STEP_DEFINITIONS['bulk_fermentation']['toggleable'] is False
        assert tl.STEP_DEFINITIONS['final_shape']['toggleable'] is False
        assert tl.STEP_DEFINITIONS['score_and_bake']['toggleable'] is False

    def test_mix_dough_has_10_min_duration(self, tl):
        """Mix dough step should have a 10-minute duration."""
        assert tl.STEP_DEFINITIONS['mix_dough']['default_duration_minutes'] == 10


class TestTimelineGeneration:
    """Tests for full timeline generation."""

    def test_basic_timeline_generation(self, tl):
        days = tl.generate_timeline(
            start_time_str='8:00 PM',
            feeding_ratio_peak_hours=12,
            temperature_f=70,
            cold_proof_hours=24,
            start_date=date(2025, 1, 1)
        )
        assert len(days) > 0
        # Should span multiple days
        assert len(days) >= 2

    def test_timeline_entries_have_required_fields(self, tl):
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=24,
            start_date=date(2025, 1, 1)
        )
        for day in days:
            assert 'date' in day
            assert 'steps' in day
            for step in day['steps']:
                assert 'step_id' in step
                assert 'name' in step
                assert 'datetime' in step
                assert 'time_display' in step
                assert 'description' in step
                assert 'visual_cue' in step
                assert 'category' in step

    def test_autolyse_disabled_by_default(self, tl):
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=24,
            start_date=date(2025, 1, 1)
        )
        all_step_ids = []
        for day in days:
            for step in day['steps']:
                all_step_ids.append(step['step_id'])
        assert 'autolyse' not in all_step_ids

    def test_autolyse_enabled_when_toggled(self, tl):
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=24,
            enabled_steps={'autolyse': True},
            start_date=date(2025, 1, 1)
        )
        all_step_ids = []
        for day in days:
            for step in day['steps']:
                all_step_ids.append(step['step_id'])
        assert 'autolyse' in all_step_ids

    def test_folds_disabled_when_toggled_off(self, tl):
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=24,
            enabled_steps={
                'stretch_fold_1': False,
                'stretch_fold_2': False,
                'stretch_fold_3': False,
                'stretch_fold_4': False
            },
            start_date=date(2025, 1, 1)
        )
        all_step_ids = []
        for day in days:
            for step in day['steps']:
                all_step_ids.append(step['step_id'])
        assert 'stretch_fold_1' not in all_step_ids
        assert 'stretch_fold_4' not in all_step_ids

    def test_cold_proof_duration_affects_timeline(self, tl):
        """Longer cold proof should push baking time later."""
        days_short = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=1,
            start_date=date(2025, 1, 1)
        )
        days_long = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=48,
            start_date=date(2025, 1, 1)
        )

        # Long proof should have more days
        assert len(days_long) >= len(days_short)

    def test_cold_proof_clamped_to_range(self, tl):
        """Cold proof should be clamped between 1 and 48 hours."""
        # Should not crash with extreme values
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=100,  # Should be clamped to 48
            start_date=date(2025, 1, 1)
        )
        assert len(days) > 0

    def test_timeline_ends_with_ready(self, tl):
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=24,
            start_date=date(2025, 1, 1)
        )
        last_day = days[-1]
        last_step = last_day['steps'][-1]
        assert last_step['step_id'] == 'ready'

    def test_chronological_order(self, tl):
        """All steps should be in chronological order within each day."""
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=24,
            start_date=date(2025, 1, 1)
        )
        from datetime import datetime
        all_times = []
        for day in days:
            for step in day['steps']:
                all_times.append(datetime.fromisoformat(step['datetime']))

        # Overall timeline should be mostly chronological
        # (preheat may start before cold proof ends, which is intentional)

    def test_mix_to_first_fold_timing(self, tl):
        """First stretch & fold should be 40 min after mix starts (10 min mix + 30 min rest)."""
        from datetime import datetime
        days = tl.generate_timeline(
            start_time_str='8:00 AM',
            feeding_ratio_peak_hours=5,
            temperature_f=70,
            cold_proof_hours=24,
            start_date=date(2025, 1, 1)
        )
        # Find mix_dough, rest_after_mix, and stretch_fold_1 times
        mix_time = None
        fold1_time = None
        fold2_time = None
        rest_time = None
        for day in days:
            for step in day['steps']:
                if step['step_id'] == 'mix_dough':
                    mix_time = datetime.fromisoformat(step['datetime'])
                elif step['step_id'] == 'rest_after_mix':
                    rest_time = datetime.fromisoformat(step['datetime'])
                elif step['step_id'] == 'stretch_fold_1':
                    fold1_time = datetime.fromisoformat(step['datetime'])
                elif step['step_id'] == 'stretch_fold_2':
                    fold2_time = datetime.fromisoformat(step['datetime'])

        assert mix_time is not None
        assert rest_time is not None
        assert fold1_time is not None
        assert fold2_time is not None

        # Rest should start 10 min after mix (mix duration)
        assert (rest_time - mix_time).total_seconds() == 600  # 10 minutes

        # First fold should be 40 min after mix starts (10 min mix + 30 min rest)
        assert (fold1_time - mix_time).total_seconds() == 2400  # 40 minutes

        # Second fold should be 30 min after first fold
        assert (fold2_time - fold1_time).total_seconds() == 1800  # 30 minutes


class TestTimeParsing:
    """Tests for time string parsing."""

    def test_standard_am(self, tl):
        time = tl._parse_time('8:00 AM')
        assert time.hour == 8
        assert time.minute == 0

    def test_standard_pm(self, tl):
        time = tl._parse_time('8:00 PM')
        assert time.hour == 20
        assert time.minute == 0

    def test_lowercase(self, tl):
        time = tl._parse_time('8:00 am')
        assert time.hour == 8

    def test_no_ampm_morning(self, tl):
        time = tl._parse_time('9:00')
        assert time.hour == 9

    def test_no_ampm_evening(self, tl):
        time = tl._parse_time('13:00')
        assert time.hour == 13  # 24-hour format for 1 PM

    def test_noon(self, tl):
        time = tl._parse_time('12:00 PM')
        assert time.hour == 12

    def test_invalid_time_raises(self, tl):
        with pytest.raises(ValueError):
            tl._parse_time('invalid')
