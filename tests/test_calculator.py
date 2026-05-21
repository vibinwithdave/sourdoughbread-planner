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
        assert result['existing_starter_used'] == 25
        assert result['flour_to_add'] == 125
        assert result['water_to_add'] == 125
        assert result['total_after_feeding'] == 275

    def test_sufficient_starter_flag(self, calc):
        # 50g at 1:5:5 = 550g total, need 100g -> sufficient
        result = calc.calculate_starter_feeding(50, '1:5:5', 100)
        assert result['sufficient'] is True
        assert result['starter_for_recipe'] == 100
        assert result['starter_remaining'] == 450

    def test_insufficient_starter_flag(self, calc):
        # 5g at 1:1:1 = 15g total, need 100g -> insufficient
        result = calc.calculate_starter_feeding(5, '1:1:1', 100)
        assert result['sufficient'] is False
        assert result['starter_for_recipe'] == 15  # Can only provide what's available
        assert result['starter_remaining'] == 0

    def test_peak_hours_returned(self, calc):
        result = calc.calculate_starter_feeding(50, '1:4:4', 100)
        assert result['peak_hours'] == 11

    def test_rounding(self, calc):
        result = calc.calculate_starter_feeding(33, '1:3:3', 100)
        # All values should be rounded to 1 decimal
        assert result['flour_to_add'] == 99.0
        assert result['water_to_add'] == 99.0
        assert result['total_after_feeding'] == 231.0


class TestIngredientCalculation:
    """Tests for full ingredient calculations."""

    def test_alexandra_cooks_recipe_approximation(self, calc):
        """Test that we can approximate the Alexandra Cooks recipe:
        500g flour, 375g water (75%), 100g starter (20%), 11g salt (2.2%)
        """
        result = calc.calculate_ingredients(
            total_flour_weight=500,
            hydration=75,
            salt_percent=2.2,
            starter_percent=20,
            existing_starter_amount=50,
            feeding_ratio='1:5:5'
        )

        assert result['total_flour_weight'] == 500
        assert result['starter_for_recipe'] == 100  # 20% of 500
        assert result['salt'] == 11.0  # 2.2% of 500
        assert result['total_water'] == 375.0  # 75% of 500
        assert result['actual_hydration'] == 75.0

    def test_additional_flour_accounts_for_starter(self, calc):
        """Starter contributes flour, so additional flour should be less than total."""
        result = calc.calculate_ingredients(
            total_flour_weight=500,
            hydration=75,
            salt_percent=2.0,
            starter_percent=20,
            existing_starter_amount=50,
            feeding_ratio='1:5:5'
        )

        # Starter (100g at 100% hydration) contributes 50g flour
        assert result['additional_flour'] == 450.0  # 500 - 50

    def test_additional_water_accounts_for_starter(self, calc):
        """Starter contributes water, so additional water should be less than total."""
        result = calc.calculate_ingredients(
            total_flour_weight=500,
            hydration=75,
            salt_percent=2.0,
            starter_percent=20,
            existing_starter_amount=50,
            feeding_ratio='1:5:5'
        )

        # Total water = 375g, starter contributes 50g water
        assert result['additional_water'] == 325.0  # 375 - 50

    def test_total_dough_weight(self, calc):
        result = calc.calculate_ingredients(
            total_flour_weight=500,
            hydration=75,
            salt_percent=2.2,
            starter_percent=20,
            existing_starter_amount=50,
            feeding_ratio='1:5:5'
        )

        # Total = flour(500) + water(375) + salt(11) + starter(100)
        expected_total = 500 + 375 + 11 + 100
        assert result['total_dough_weight'] == expected_total

    def test_scaling_with_different_flour_weight(self, calc):
        """Doubling flour weight should double all ingredients proportionally."""
        result_500 = calc.calculate_ingredients(
            total_flour_weight=500, hydration=75, salt_percent=2.0,
            starter_percent=20, existing_starter_amount=50, feeding_ratio='1:5:5'
        )
        result_1000 = calc.calculate_ingredients(
            total_flour_weight=1000, hydration=75, salt_percent=2.0,
            starter_percent=20, existing_starter_amount=100, feeding_ratio='1:5:5'
        )

        assert result_1000['starter_for_recipe'] == 2 * result_500['starter_for_recipe']
        assert result_1000['additional_flour'] == 2 * result_500['additional_flour']
        assert result_1000['salt'] == 2 * result_500['salt']

    def test_high_hydration(self, calc):
        result = calc.calculate_ingredients(
            total_flour_weight=500, hydration=85, salt_percent=2.0,
            starter_percent=20, existing_starter_amount=50, feeding_ratio='1:5:5'
        )
        assert result['actual_hydration'] == 85.0
        assert result['total_water'] == 425.0

    def test_low_hydration(self, calc):
        result = calc.calculate_ingredients(
            total_flour_weight=500, hydration=65, salt_percent=2.0,
            starter_percent=20, existing_starter_amount=50, feeding_ratio='1:5:5'
        )
        assert result['actual_hydration'] == 65.0
        assert result['total_water'] == 325.0

    def test_starter_feeding_info_included(self, calc):
        result = calc.calculate_ingredients(
            total_flour_weight=500, hydration=75, salt_percent=2.0,
            starter_percent=20, existing_starter_amount=50, feeding_ratio='1:5:5'
        )
        assert 'starter_feeding' in result
        assert result['starter_feeding']['existing_starter_used'] == 50
