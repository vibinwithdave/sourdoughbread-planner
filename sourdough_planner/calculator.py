"""
Ingredient calculator for sourdough bread planning.

Uses a starter-centric calculation model where flour, water, and salt
amounts are derived from the starter parameters, while also allowing
users to specify a desired total flour weight for scaling.
"""


class IngredientCalculator:
    """Calculate ingredient amounts based on starter parameters and desired flour weight."""

    # Feeding ratio definitions with peak time estimates
    FEEDING_RATIOS = {
        '1:1:1': {
            'starter_parts': 1,
            'flour_parts': 1,
            'water_parts': 1,
            'peak_hours': 5,
            'description': 'Fast (4-6 hours) - Same day baking'
        },
        '1:2:2': {
            'starter_parts': 1,
            'flour_parts': 2,
            'water_parts': 2,
            'peak_hours': 7,
            'description': 'Moderate (6-8 hours) - Balanced timing'
        },
        '1:3:3': {
            'starter_parts': 1,
            'flour_parts': 3,
            'water_parts': 3,
            'peak_hours': 9,
            'description': 'Standard (8-10 hours) - Daily maintenance'
        },
        '1:4:4': {
            'starter_parts': 1,
            'flour_parts': 4,
            'water_parts': 4,
            'peak_hours': 11,
            'description': 'Professional (10-12 hours) - Most common'
        },
        '1:5:5': {
            'starter_parts': 1,
            'flour_parts': 5,
            'water_parts': 5,
            'peak_hours': 12,
            'description': 'Overnight (12-14 hours) - Work schedule'
        },
        '1:10:10': {
            'starter_parts': 1,
            'flour_parts': 10,
            'water_parts': 10,
            'peak_hours': 20,
            'description': 'Extended (16-24 hours) - Weekend baking'
        }
    }

    # Default baker's percentages (relative to total flour weight)
    DEFAULT_HYDRATION = 75  # 75% hydration
    DEFAULT_SALT_PERCENT = 2.2  # 2.2% salt (approx 11g per 500g flour)
    DEFAULT_STARTER_PERCENT = 20  # 20% starter (100g per 500g flour)

    def __init__(self):
        pass

    def get_feeding_ratios(self):
        """Return available feeding ratios for frontend display."""
        return {k: v['description'] for k, v in self.FEEDING_RATIOS.items()}

    def calculate_starter_feeding(self, existing_starter_amount, feeding_ratio, starter_needed_for_recipe):
        """
        Calculate how to feed the starter to produce enough for the recipe
        while retaining some for future bakes.

        Args:
            existing_starter_amount: Grams of existing starter to feed
            feeding_ratio: String like '1:4:4'
            starter_needed_for_recipe: Grams of active starter needed for the dough

        Returns:
            dict with feeding amounts and totals
        """
        ratio_info = self.FEEDING_RATIOS[feeding_ratio]

        starter_used = existing_starter_amount
        flour_needed = existing_starter_amount * ratio_info['flour_parts']
        water_needed = existing_starter_amount * ratio_info['water_parts']
        total_after_feeding = starter_used + flour_needed + water_needed

        # Calculate how much starter remains after taking what's needed for the recipe
        starter_remaining = max(0, total_after_feeding - starter_needed_for_recipe)

        return {
            'existing_starter_used': round(starter_used, 1),
            'flour_to_add': round(flour_needed, 1),
            'water_to_add': round(water_needed, 1),
            'total_after_feeding': round(total_after_feeding, 1),
            'starter_for_recipe': round(min(starter_needed_for_recipe, total_after_feeding), 1),
            'starter_remaining': round(starter_remaining, 1),
            'peak_hours': ratio_info['peak_hours'],
            'sufficient': total_after_feeding >= starter_needed_for_recipe
        }

    def calculate_ingredients(self, total_flour_weight, hydration, salt_percent,
                              starter_percent, existing_starter_amount, feeding_ratio):
        """
        Calculate all ingredient amounts using a starter-centric model
        with user-specified total flour weight.

        The starter contributes both flour and water to the total dough.
        Additional flour and water are calculated to meet the target
        total flour weight and hydration percentage.

        Args:
            total_flour_weight: Desired total flour in the final dough (grams)
            hydration: Target hydration percentage (e.g., 75 for 75%)
            salt_percent: Salt as percentage of total flour (e.g., 2.2)
            starter_percent: Starter as percentage of total flour (e.g., 20)
            existing_starter_amount: Grams of existing starter to feed
            feeding_ratio: String like '1:4:4'

        Returns:
            dict with all ingredient amounts and feeding info
        """
        # Calculate starter amount needed for recipe
        starter_for_recipe = total_flour_weight * (starter_percent / 100)

        # Calculate starter feeding
        starter_feeding = self.calculate_starter_feeding(
            existing_starter_amount, feeding_ratio, starter_for_recipe
        )

        # Starter is typically 100% hydration (equal parts flour and water)
        # So starter contributes half its weight as flour and half as water
        starter_flour_contribution = starter_for_recipe / 2
        starter_water_contribution = starter_for_recipe / 2

        # Calculate additional flour and water needed
        additional_flour = total_flour_weight - starter_flour_contribution
        total_water_needed = total_flour_weight * (hydration / 100)
        additional_water = total_water_needed - starter_water_contribution

        # Salt calculation
        salt = total_flour_weight * (salt_percent / 100)

        # Total dough weight
        total_dough_weight = total_flour_weight + total_water_needed + salt + starter_for_recipe

        # Actual final hydration (accounting for starter contribution)
        actual_hydration = (total_water_needed / total_flour_weight) * 100

        return {
            'total_flour_weight': round(total_flour_weight, 1),
            'starter_for_recipe': round(starter_for_recipe, 1),
            'additional_flour': round(additional_flour, 1),
            'additional_water': round(additional_water, 1),
            'salt': round(salt, 1),
            'total_water': round(total_water_needed, 1),
            'total_dough_weight': round(total_dough_weight, 1),
            'actual_hydration': round(actual_hydration, 1),
            'starter_feeding': starter_feeding,
            'starter_percent': starter_percent,
            'hydration_percent': hydration,
            'salt_percent': salt_percent
        }
