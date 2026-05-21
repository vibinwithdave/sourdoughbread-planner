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


class TestDeriveFlourWeight:
    """Tests for deriving total flour from starter amount and percentage."""

    def test_100g_at_20_percent(self, calc):
        """100g starter at 20% = 500g total flour."""
        flour = calc.derive_flour_weight(100, 20)
        assert flour == 500.0

    def test_50g_at_10_percent(self, calc):
        """50g starter at 10% = 500g total flour."""
        flour = calc.derive_flour_weight(50, 10)
        assert flour == 500.0

    def test_200g_at_20_percent(self, calc):
        """200g starter at 20% = 1000g total flour."""
        flour = calc.derive_flour_weight(200, 20)
        assert flour == 1000.0

    def test_75g_at_15_percent(self, calc):
        """75g starter at 15% = 500g total flour."""
        flour = calc.derive_flour_weight(75, 15)
        assert flour == 500.0

    def test_zero_percent_raises(self, calc):
        with pytest.raises(ValueError):
            calc.derive_flour_weight(100, 0)

    def test_negative_percent_raises(self, calc):
        with pytest.raises(ValueError):
            calc.derive_flour_weight(100, -5)


class TestDeriveRecipeFromStarter:
    """Tests for the live preview calculation."""

    def test_standard_recipe(self, calc):
        """100g starter, 20%, 75% hydration, 2.2% salt."""
        recipe = calc.derive_recipe_from_starter(100, 20, 75, 2.2)
        assert recipe['total_flour'] == 500.0
        assert recipe['total_water'] == 375.0
        assert recipe['salt'] == 11.0
        assert recipe['starter_amount'] == 100.0
        assert recipe['additional_flour'] == 450.0  # 500 - 50 (starter flour)
        assert recipe['additional_water'] == 325.0  # 375 - 50 (starter water)

    def test_total_dough_weight(self, calc):
        recipe = calc.derive_recipe_from_starter(100, 20, 75, 2.2)
        # total = flour(500) + water(375) + salt(11) + starter(100) = 986
        assert recipe['total_dough_weight'] == 986.0

    def test_high_hydration(self, calc):
        recipe = calc.derive_recipe_from_starter(100, 20, 85, 2.0)
        assert recipe['total_flour'] == 500.0
        assert recipe['total_water'] == 425.0  # 85% of 500

    def test_small_starter_amount(self, calc):
        """50g starter at 20% = 250g flour."""
        recipe = calc.derive_recipe_from_starter(50, 20, 75, 2.2)
        assert recipe['total_flour'] == 250.0
        assert recipe['total_water'] == 187.5
        assert recipe['salt'] == 5.5

    def test_large_starter_percent(self, calc):
        """100g starter at 40% = 250g flour."""
        recipe = calc.derive_recipe_from_starter(100, 40, 75, 2.0)
        assert recipe['total_flour'] == 250.0
        assert recipe['total_water'] == 187.5

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
        assert result['starter_for_recipe'] == 15
        assert result['starter_remaining'] == 0

    def test_peak_hours_returned(self, calc):
        result = calc.calculate_starter_feeding(50, '1:4:4', 100)
        assert result['peak_hours'] == 11


class TestIngredientCalculation:
    """Tests for the full calculate_ingredients method (starter-amount-driven)."""

    def test_alexandra_cooks_recipe(self, calc):
        """100g starter at 20% = 500g flour, 75% hydration, 2.2% salt."""
        result = calc.calculate_ingredients(
            starter_amount=100,
            starter_percent=20,
            hydration=75,
            salt_percent=2.2,
            existing_starter_amount=50,
            feeding_ratio='1:5:5'
        )

        assert result['starter_amount'] == 100.0
        assert result['total_flour_weight'] == 500.0
        assert result['total_water'] == 375.0
        assert result['salt'] == 11.0
        assert result['additional_flour'] == 450.0
        assert result['additional_water'] == 325.0
        assert result['actual_hydration'] == 75.0

    def test_starter_feeding_info_included(self, calc):
        result = calc.calculate_ingredients(
            starter_amount=100,
            starter_percent=20,
            hydration=75,
            salt_percent=2.0,
            existing_starter_amount=50,
            feeding_ratio='1:5:5'
        )
        assert 'starter_feeding' in result
        assert result['starter_feeding']['existing_starter_used'] == 50

    def test_scaling_with_different_starter_amount(self, calc):
        """Doubling starter amount should double all recipe weights."""
        result_100 = calc.calculate_ingredients(
            starter_amount=100, starter_percent=20, hydration=75,
            salt_percent=2.0, existing_starter_amount=50, feeding_ratio='1:5:5'
        )
        result_200 = calc.calculate_ingredients(
            starter_amount=200, starter_percent=20, hydration=75,
            salt_percent=2.0, existing_starter_amount=100, feeding_ratio='1:5:5'
        )

        assert result_200['total_flour_weight'] == 2 * result_100['total_flour_weight']
        assert result_200['total_water'] == 2 * result_100['total_water']
        assert result_200['salt'] == 2 * result_100['salt']

    def test_changing_starter_percent_changes_flour(self, calc):
        """Same starter amount at different % should give different flour weights."""
        result_20 = calc.calculate_ingredients(
            starter_amount=100, starter_percent=20, hydration=75,
            salt_percent=2.0, existing_starter_amount=50, feeding_ratio='1:5:5'
        )
        result_10 = calc.calculate_ingredients(
            starter_amount=100, starter_percent=10, hydration=75,
            salt_percent=2.0, existing_starter_amount=50, feeding_ratio='1:5:5'
        )

        # 100g at 20% = 500g flour; 100g at 10% = 1000g flour
        assert result_20['total_flour_weight'] == 500.0
        assert result_10['total_flour_weight'] == 1000.0

    def test_total_dough_weight(self, calc):
        result = calc.calculate_ingredients(
            starter_amount=100, starter_percent=20, hydration=75,
            salt_percent=2.2, existing_starter_amount=50, feeding_ratio='1:5:5'
        )
        # 500 + 375 + 11 + 100 = 986
        assert result['total_dough_weight'] == 986.0
