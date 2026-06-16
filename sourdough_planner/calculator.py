"""
Ingredient calculator for sourdough bread planning.

Uses a starter-amount-driven calculation model:
  - User inputs: starter amount (g), starter %, hydration %, salt %
  - Derived: total flour weight, total water, salt weight

The starter amount determines the scale of the entire recipe.
For example: 100g starter at 20% starter means total flour = 100 / 0.20 = 500g.
"""


class IngredientCalculator:
    """Calculate ingredient amounts driven by the starter amount and baker's percentages."""

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

    # Fermentation speed ratios (starter : water : flour)
    # Based on Alexandra Cooks recipe: varying starter with fixed water/flour ratio
    SPEED_RATIOS = {
        'slow':    {'starter': 50,  'water': 375, 'flour': 500},
        'regular': {'starter': 75,  'water': 375, 'flour': 500},
        'fast':    {'starter': 100, 'water': 375, 'flour': 500}
    }

    # Default baker's percentages
    DEFAULT_HYDRATION = 75
    DEFAULT_SALT_PERCENT = 2.2
    DEFAULT_STARTER_PERCENT = 20
    DEFAULT_STARTER_AMOUNT = 100  # grams

    def __init__(self):
        pass

    def get_feeding_ratios(self):
        """Return available feeding ratios for frontend display."""
        return {k: v['description'] for k, v in self.FEEDING_RATIOS.items()}

    def derive_recipe_from_speed(self, starter_amount, speed, salt_percent=2.2):
        """
        Derive flour and water from the starter amount and fermentation speed.

        The speed defines a ratio between starter, water, and flour.
        The flour and water in the ratio are the amounts ADDED DIRECTLY to the dough
        (not inclusive of what's inside the starter).

        For example, 'fast' ratio is 100:375:500. With 100g starter:
          - flour to add = 500g
          - water to add = 375g
          - salt = 500g * 2.2% = 11g
          - total dough = 100 + 500 + 375 + 11 = 986g

        If user inputs 50g starter at 'fast' (100:375:500):
          - flour to add = 50 * (500/100) = 250g
          - water to add = 50 * (375/100) = 187.5g

        Args:
            starter_amount: Grams of active starter the user wants to use
            speed: One of 'slow', 'regular', 'fast'
            salt_percent: Salt as % of flour added to dough (default 2.2)

        Returns:
            dict with flour, water (amounts to add), salt, totals, etc.
        """
        if speed not in self.SPEED_RATIOS:
            raise ValueError(f"Invalid speed: {speed}. Must be one of: {list(self.SPEED_RATIOS.keys())}")

        ratio = self.SPEED_RATIOS[speed]
        scale_factor = starter_amount / ratio['starter']

        # These are the amounts you ADD to the dough (not inclusive of starter)
        flour_to_add = ratio['flour'] * scale_factor
        water_to_add = ratio['water'] * scale_factor
        salt = flour_to_add * (salt_percent / 100)

        # True totals include what's inside the starter (assumes 100% hydration starter)
        starter_flour_contribution = starter_amount / 2
        starter_water_contribution = starter_amount / 2
        total_flour = flour_to_add + starter_flour_contribution
        total_water = water_to_add + starter_water_contribution

        total_dough_weight = starter_amount + flour_to_add + water_to_add + salt
        actual_hydration = (total_water / total_flour) * 100 if total_flour > 0 else 0

        return {
            'starter_amount': round(starter_amount, 1),
            'speed': speed,
            'flour_to_add': round(flour_to_add, 1),
            'water_to_add': round(water_to_add, 1),
            'total_flour': round(total_flour, 1),
            'total_water': round(total_water, 1),
            'salt': round(salt, 1),
            'hydration': round(actual_hydration, 1),
            'salt_percent': salt_percent,
            'total_dough_weight': round(total_dough_weight, 1)
        }

    def derive_flour_weight(self, starter_amount, starter_percent):
        """
        Derive the total flour weight from the starter amount and starter percentage.

        Formula: total_flour = starter_amount / (starter_percent / 100)

        Args:
            starter_amount: Grams of active starter to use in the recipe
            starter_percent: Starter as percentage of total flour (e.g., 20)

        Returns:
            Total flour weight in grams
        """
        if starter_percent <= 0:
            raise ValueError("Starter percentage must be greater than 0")
        return starter_amount / (starter_percent / 100)

    def derive_recipe_from_starter(self, starter_amount, starter_percent, hydration, salt_percent):
        """
        Derive all recipe weights from the starter amount and baker's percentages.

        This is the core calculation used for the live preview in the UI.

        Args:
            starter_amount: Grams of active starter (e.g., 100)
            starter_percent: Starter as % of total flour (e.g., 20)
            hydration: Water as % of total flour (e.g., 75)
            salt_percent: Salt as % of total flour (e.g., 2.2)

        Returns:
            dict with total_flour, total_water, salt, and total_dough_weight
        """
        if starter_percent <= 0:
            raise ValueError("Starter percentage must be greater than 0")

        total_flour = starter_amount / (starter_percent / 100)
        total_water = total_flour * (hydration / 100)
        salt = total_flour * (salt_percent / 100)

        # Starter contributes flour and water (assumes 100% hydration starter)
        starter_flour_contribution = starter_amount / 2
        starter_water_contribution = starter_amount / 2

        # Additional flour and water needed beyond what starter provides
        additional_flour = total_flour - starter_flour_contribution
        additional_water = total_water - starter_water_contribution

        total_dough_weight = total_flour + total_water + salt + starter_amount

        return {
            'starter_amount': round(starter_amount, 1),
            'starter_percent': starter_percent,
            'total_flour': round(total_flour, 1),
            'total_water': round(total_water, 1),
            'additional_flour': round(additional_flour, 1),
            'additional_water': round(additional_water, 1),
            'salt': round(salt, 1),
            'hydration': hydration,
            'salt_percent': salt_percent,
            'total_dough_weight': round(total_dough_weight, 1)
        }

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

    def calculate_ingredients(self, starter_amount, existing_starter_amount, feeding_ratio,
                              speed=None, starter_percent=None, hydration=None,
                              salt_percent=2.2):
        """
        Calculate all ingredient amounts driven by the starter amount.

        Two modes:
        1. Speed-based (primary): starter_amount + speed -> flour/water derived from ratio
        2. Percentage-based (custom): starter_amount + starter_percent + hydration

        Args:
            starter_amount: Grams of active starter to use in recipe (e.g., 100)
            existing_starter_amount: Grams of existing starter to feed
            feeding_ratio: String like '1:4:4'
            speed: Fermentation speed ('slow', 'regular', 'fast') or None for custom
            starter_percent: Starter as percentage of total flour (for custom mode)
            hydration: Target hydration percentage (for custom mode)
            salt_percent: Salt as percentage of total flour (e.g., 2.2)

        Returns:
            dict with all ingredient amounts and feeding info
        """
        # Derive recipe based on mode
        if speed and speed in self.SPEED_RATIOS:
            recipe = self.derive_recipe_from_speed(starter_amount, speed, salt_percent)
        else:
            # Custom / percentage-based fallback
            if starter_percent is None:
                starter_percent = self.DEFAULT_STARTER_PERCENT
            if hydration is None:
                hydration = self.DEFAULT_HYDRATION
            recipe = self.derive_recipe_from_starter(
                starter_amount, starter_percent, hydration, salt_percent
            )

        # Calculate starter feeding
        starter_feeding = self.calculate_starter_feeding(
            existing_starter_amount, feeding_ratio, starter_amount
        )

        # For speed-based mode, flour_to_add/water_to_add are the amounts added to dough
        # For custom mode, additional_flour/additional_water are the amounts added to dough
        if speed and speed in self.SPEED_RATIOS:
            flour_to_add = recipe['flour_to_add']
            water_to_add = recipe['water_to_add']
        else:
            flour_to_add = recipe['additional_flour']
            water_to_add = recipe['additional_water']

        return {
            'starter_amount': recipe['starter_amount'],
            'speed': recipe.get('speed', 'custom'),
            'flour_to_add': flour_to_add,
            'water_to_add': water_to_add,
            'total_flour': recipe['total_flour'],
            'total_water': recipe['total_water'],
            'salt': recipe['salt'],
            'hydration_percent': recipe['hydration'],
            'salt_percent': recipe['salt_percent'],
            'total_dough_weight': recipe['total_dough_weight'],
            'actual_hydration': recipe['hydration'],
            'starter_feeding': starter_feeding
        }
