"""Tests for the IngredientCalculator module."""

import pytest
from sourdough_planner.calculator import IngredientCalculator


@pytest.fixture
def calc():
    """Provide a fresh IngredientCalculator instance."""
    return IngredientCalculator()


class TestFeedingRatios:
    """Tests for feeding ratio definitions and retrieval."""

    def test_get_feeding_ratios_returns_all(self, calc):
        ratios = calc.get_feeding_ratios()
        assert len(ratios) == 6
        assert '1:1:1' in ratios
        assert '1:5:5' in ratios
        assert '1:10:10' in ratios

    def test_feeding_ratios_have_descriptions(self, calc):
        ratios = calc.get_feeding_ratios()
        for key, desc in ratios.items():
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_feeding_ratio_details_have_required_keys(self, calc):
        for key, info in calc.FEEDING_RATIOS.items():
            assert 'starter_parts' in info
            assert 'flour_parts' in info
            assert 'water_parts' in info
            assert 'peak_hours' in info
            assert 'description' in info


class TestSpeedRatios:
    """Tests for the speed-based recipe derivation (primary calculation mode)."""

    def test_slow_base_ratio(self, calc):
        """Slow with 50g starter should give exactly 500g flour to add, 375g water to add."""
        result = calc.derive_recipe_from_speed(50, 'slow')
        assert result['flour_to_add'] == 500.0
        assert result['water_to_add'] == 375.0
        assert result['starter_amount'] == 50.0
        # True totals include starter contribution
        assert result['total_flour'] == 525.0  # 500 + 25 from starter
        assert result['total_water'] == 400.0  # 375 + 25 from starter

    def test_regular_base_ratio(self, calc):
        """Regular with 75g starter should give exactly 500g flour to add, 375g water to add."""
        result = calc.derive_recipe_from_speed(75, 'regular')
        assert result['flour_to_add'] == 500.0
        assert result['water_to_add'] == 375.0
        assert result['starter_amount'] == 75.0
        # True totals include starter contribution
        assert result['total_flour'] == 537.5  # 500 + 37.5 from starter
        assert result['total_water'] == 412.5  # 375 + 37.5 from starter

    def test_fast_base_ratio(self, calc):
        """Fast with 100g starter should give exactly 500g flour to add, 375g water to add."""
        result = calc.derive_recipe_from_speed(100, 'fast')
        assert result['flour_to_add'] == 500.0
        assert result['water_to_add'] == 375.0
        assert result['starter_amount'] == 100.0
        # True totals include starter contribution
        assert result['total_flour'] == 550.0  # 500 + 50 from starter
        assert result['total_water'] == 425.0  # 375 + 50 from starter

    def test_slow_scaled_down(self, calc):
        """Slow with 25g starter should scale proportionally (0.5x)."""
        result = calc.derive_recipe_from_speed(25, 'slow')
        assert result['flour_to_add'] == 250.0
        assert result['water_to_add'] == 187.5

    def test_regular_scaled_down(self, calc):
        """Regular with 25g starter should scale proportionally."""
        result = calc.derive_recipe_from_speed(25, 'regular')
        # 25 / 75 = 0.333... scale factor
        assert abs(result['flour_to_add'] - 166.7) < 0.1
        assert abs(result['water_to_add'] - 125.0) < 0.1

    def test_fast_scaled_up(self, calc):
        """Fast with 200g starter should scale proportionally (2x)."""
        result = calc.derive_recipe_from_speed(200, 'fast')
        assert result['flour_to_add'] == 1000.0
        assert result['water_to_add'] == 750.0

    def test_slow_scaled_up(self, calc):
        """Slow with 150g starter should scale proportionally (3x)."""
        result = calc.derive_recipe_from_speed(150, 'slow')
        assert result['flour_to_add'] == 1500.0
        assert result['water_to_add'] == 1125.0

    def test_hydration_is_true_hydration(self, calc):
        """Hydration should be true hydration: total_water / total_flour."""
        result = calc.derive_recipe_from_speed(100, 'fast')
        # total_water = 425, total_flour = 550 -> 77.3%
        expected = (425.0 / 550.0) * 100
        assert abs(result['hydration'] - expected) < 0.1

    def test_salt_calculation(self, calc):
        """Salt should be calculated as percentage of flour added to dough."""
        result = calc.derive_recipe_from_speed(50, 'slow', salt_percent=2.2)
        # 500g flour_to_add * 2.2% = 11g
        assert result['salt'] == 11.0

    def test_total_dough_weight(self, calc):
        """Total dough weight = starter + flour_to_add + water_to_add + salt."""
        result = calc.derive_recipe_from_speed(100, 'fast', salt_percent=2.2)
        expected = 100 + 500 + 375 + 11
        assert result['total_dough_weight'] == expected

    def test_invalid_speed_raises_error(self, calc):
        """Invalid speed should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid speed"):
            calc.derive_recipe_from_speed(100, 'turbo')

    def test_speed_field_in_result(self, calc):
        """Result should include the speed used."""
        result = calc.derive_recipe_from_speed(100, 'fast')
        assert result['speed'] == 'fast'


class TestDeriveFlourWeight:
    """Tests for deriving total flour from starter amount and percentage."""

    def test_100g_at_20_percent(self, calc):
        flour = calc.derive_flour_weight(100, 20)
        assert flour == 500.0

    def test_50g_at_10_percent(self, calc):
        flour = calc.derive_flour_weight(50, 10)
        assert flour == 500.0

    def test_200g_at_20_percent(self, calc):
        flour = calc.derive_flour_weight(200, 20)
        assert flour == 1000.0

    def test_zero_percent_raises(self, calc):
        with pytest.raises(ValueError):
            calc.derive_flour_weight(100, 0)

    def test_negative_percent_raises(self, calc):
        with pytest.raises(ValueError):
            calc.derive_flour_weight(100, -5)


class TestDeriveRecipeFromStarter:
    """Tests for the percentage-based calculation (custom mode)."""

    def test_standard_recipe(self, calc):
        """100g starter, 20%, 75% hydration, 2.2% salt."""
        recipe = calc.derive_recipe_from_starter(100, 20, 75, 2.2)
        assert recipe['total_flour'] == 500.0
        assert recipe['total_water'] == 375.0
        assert recipe['salt'] == 11.0
        assert recipe['additional_flour'] == 450.0
        assert recipe['additional_water'] == 325.0

    def test_total_dough_weight(self, calc):
        recipe = calc.derive_recipe_from_starter(100, 20, 75, 2.2)
        assert recipe['total_dough_weight'] == 986.0

    def test_high_hydration(self, calc):
        recipe = calc.derive_recipe_from_starter(100, 20, 85, 2.0)
        assert recipe['total_water'] == 425.0

    def test_zero_percent_raises(self, calc):
        with pytest.raises(ValueError):
            calc.derive_recipe_from_starter(100, 0, 75, 2.2)


class TestStarterFeeding:
    """Tests for starter feeding calculations."""

    def test_basic_1_to_1_feeding(self, calc):
        result = calc.calculate_starter_feeding(50, '1:1:1', 100)
        assert result['existing_starter_used'] == 50
        assert result['flour_to_add'] == 50
        assert result['water_to_add'] == 50
        assert result['total_after_feeding'] == 150

    def test_1_to_5_feeding(self, calc):
        result = calc.calculate_starter_feeding(25, '1:5:5', 100)
        assert result['total_after_feeding'] == 275

    def test_sufficient_starter_flag(self, calc):
        result = calc.calculate_starter_feeding(50, '1:5:5', 100)
        assert result['sufficient'] is True
        assert result['starter_remaining'] == 450

    def test_insufficient_starter_flag(self, calc):
        result = calc.calculate_starter_feeding(5, '1:1:1', 100)
        assert result['sufficient'] is False
        assert result['starter_remaining'] == 0


class TestCalculateIngredients:
    """Tests for the unified calculate_ingredients method."""

    def test_speed_mode_slow(self, calc):
        """Speed mode with 'slow' should use ratio-based calculation."""
        result = calc.calculate_ingredients(
            starter_amount=50,
            existing_starter_amount=50,
            feeding_ratio='1:5:5',
            speed='slow',
            salt_percent=2.2
        )
        assert result['flour_to_add'] == 500.0
        assert result['water_to_add'] == 375.0
        assert result['speed'] == 'slow'

    def test_speed_mode_regular(self, calc):
        """Speed mode with 'regular' should use ratio-based calculation."""
        result = calc.calculate_ingredients(
            starter_amount=75,
            existing_starter_amount=50,
            feeding_ratio='1:5:5',
            speed='regular',
            salt_percent=2.2
        )
        assert result['flour_to_add'] == 500.0
        assert result['water_to_add'] == 375.0
        assert result['speed'] == 'regular'

    def test_speed_mode_fast(self, calc):
        """Speed mode with 'fast' should use ratio-based calculation."""
        result = calc.calculate_ingredients(
            starter_amount=100,
            existing_starter_amount=50,
            feeding_ratio='1:5:5',
            speed='fast',
            salt_percent=2.2
        )
        assert result['flour_to_add'] == 500.0
        assert result['water_to_add'] == 375.0
        assert result['speed'] == 'fast'

    def test_custom_mode(self, calc):
        """Custom mode (speed=None) should use percentage-based calculation."""
        result = calc.calculate_ingredients(
            starter_amount=100,
            existing_starter_amount=50,
            feeding_ratio='1:5:5',
            speed=None,
            starter_percent=20,
            hydration=75,
            salt_percent=2.2
        )
        assert result['flour_to_add'] == 450.0
        assert result['water_to_add'] == 325.0
        assert result['speed'] == 'custom'

    def test_25g_starter_slow(self, calc):
        """25g starter at slow speed should scale to 250g flour to add, 187.5g water to add."""
        result = calc.calculate_ingredients(
            starter_amount=25,
            existing_starter_amount=25,
            feeding_ratio='1:5:5',
            speed='slow',
            salt_percent=2.2
        )
        assert result['flour_to_add'] == 250.0
        assert result['water_to_add'] == 187.5

    def test_includes_starter_feeding(self, calc):
        """Should include starter feeding calculations."""
        result = calc.calculate_ingredients(
            starter_amount=100,
            existing_starter_amount=50,
            feeding_ratio='1:5:5',
            speed='fast',
            salt_percent=2.2
        )
        assert 'starter_feeding' in result
        assert result['starter_feeding']['total_after_feeding'] == 550.0
        assert result['starter_feeding']['sufficient'] is True
