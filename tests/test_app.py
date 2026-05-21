"""Tests for the Flask application routes."""

import pytest
import json
from app import app


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthAndInfo:
    """Tests for informational endpoints."""

    def test_health_check(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'

    def test_index_page_loads(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Sourdough Bread Planner' in response.data

    def test_ratios_endpoint(self, client):
        response = client.get('/api/ratios')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert '1:5:5' in data['ratios']

    def test_steps_endpoint(self, client):
        response = client.get('/api/steps')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'feed_starter' in data['steps']


class TestPreviewEndpoint:
    """Tests for the live recipe preview endpoint."""

    def test_preview_speed_regular(self, client):
        """Regular speed with 75g starter should give 500g flour, 375g water."""
        response = client.post('/api/preview', json={
            'starter_amount': 75,
            'fermentation_speed': 'regular',
            'salt_percent': 2.2
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['recipe']['total_flour'] == 500.0
        assert data['recipe']['total_water'] == 375.0
        assert data['recipe']['salt'] == 11.0

    def test_preview_speed_slow(self, client):
        """Slow speed with 25g starter should scale to 250g flour, 187.5g water."""
        response = client.post('/api/preview', json={
            'starter_amount': 25,
            'fermentation_speed': 'slow',
            'salt_percent': 2.2
        })
        data = response.get_json()
        assert data['recipe']['total_flour'] == 250.0
        assert data['recipe']['total_water'] == 187.5

    def test_preview_speed_fast(self, client):
        """Fast speed with 100g starter should give 500g flour, 375g water."""
        response = client.post('/api/preview', json={
            'starter_amount': 100,
            'fermentation_speed': 'fast',
            'salt_percent': 2.2
        })
        data = response.get_json()
        assert data['recipe']['total_flour'] == 500.0
        assert data['recipe']['total_water'] == 375.0

    def test_preview_custom_mode(self, client):
        """Custom mode should use starter_percent and hydration."""
        response = client.post('/api/preview', json={
            'starter_amount': 100,
            'fermentation_speed': 'custom',
            'starter_percent': 20,
            'hydration': 80,
            'salt_percent': 2.0
        })
        data = response.get_json()
        assert data['recipe']['total_flour'] == 500.0
        assert data['recipe']['total_water'] == 400.0

    def test_preview_custom_invalid_percent(self, client):
        """Custom mode with 0% starter should return 400."""
        response = client.post('/api/preview', json={
            'starter_amount': 100,
            'fermentation_speed': 'custom',
            'starter_percent': 0,
            'hydration': 75,
            'salt_percent': 2.0
        })
        assert response.status_code == 400


class TestBulkEstimate:
    """Tests for the bulk fermentation estimate endpoint."""

    def test_estimate_at_70f(self, client):
        response = client.post('/api/estimate-bulk',
                               json={'temperature_f': 70})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['estimated_hours'] == 9.0

    def test_estimate_at_78f(self, client):
        response = client.post('/api/estimate-bulk',
                               json={'temperature_f': 78})
        data = response.get_json()
        assert data['estimated_hours'] == 6.0


class TestGenerateSchedule:
    """Tests for the main schedule generation endpoint."""

    def test_generate_with_defaults(self, client):
        response = client.post('/api/generate', json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'ingredients' in data
        assert 'timeline' in data
        assert 'settings' in data

    def test_generate_speed_slow(self, client):
        """Slow speed with 50g starter should produce 500g flour, 375g water."""
        response = client.post('/api/generate', json={
            'starter_amount': 50,
            'fermentation_speed': 'slow',
            'salt_percent': 2.2,
            'existing_starter_amount': 50,
            'feeding_ratio': '1:5:5',
            'start_time': '8:00 PM',
            'temperature_f': 70,
            'cold_proof_hours': 24
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['ingredients']['total_flour_weight'] == 500.0
        assert data['ingredients']['total_water'] == 375.0
        assert data['settings']['fermentation_speed'] == 'slow'

    def test_generate_speed_fast(self, client):
        """Fast speed with 100g starter should produce 500g flour, 375g water."""
        response = client.post('/api/generate', json={
            'starter_amount': 100,
            'fermentation_speed': 'fast',
            'salt_percent': 2.2,
            'existing_starter_amount': 50,
            'feeding_ratio': '1:5:5',
            'start_time': '8:00 PM',
            'temperature_f': 70,
            'cold_proof_hours': 24
        })
        data = response.get_json()
        assert data['ingredients']['total_flour_weight'] == 500.0
        assert data['ingredients']['total_water'] == 375.0
        assert data['settings']['fermentation_speed'] == 'fast'

    def test_generate_custom_mode(self, client):
        """Custom mode should use starter_percent and hydration."""
        response = client.post('/api/generate', json={
            'starter_amount': 100,
            'fermentation_speed': 'custom',
            'starter_percent': 20,
            'hydration': 75,
            'salt_percent': 2.2,
            'existing_starter_amount': 50,
            'feeding_ratio': '1:5:5',
            'start_time': '8:00 PM',
            'temperature_f': 70,
            'cold_proof_hours': 24
        })
        data = response.get_json()
        assert data['ingredients']['total_flour_weight'] == 500.0
        assert data['ingredients']['total_water'] == 375.0
        assert data['settings']['fermentation_speed'] == 'custom'

    def test_generate_scaled_recipe(self, client):
        """25g starter at slow speed should scale to 250g flour."""
        response = client.post('/api/generate', json={
            'starter_amount': 25,
            'fermentation_speed': 'slow',
            'salt_percent': 2.2,
            'existing_starter_amount': 25,
            'feeding_ratio': '1:5:5',
            'start_time': '8:00 PM',
            'temperature_f': 70,
            'cold_proof_hours': 24
        })
        data = response.get_json()
        assert data['ingredients']['total_flour_weight'] == 250.0
        assert data['ingredients']['total_water'] == 187.5

    def test_generate_with_invalid_ratio(self, client):
        response = client.post('/api/generate', json={
            'feeding_ratio': '1:99:99'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_generate_timeline_has_days(self, client):
        response = client.post('/api/generate', json={
            'start_time': '8:00 PM',
            'cold_proof_hours': 24
        })
        data = response.get_json()
        assert len(data['timeline']) >= 2

    def test_generate_settings_returned(self, client):
        response = client.post('/api/generate', json={
            'starter_amount': 100,
            'fermentation_speed': 'fast',
            'temperature_f': 75,
            'cold_proof_hours': 36,
            'feeding_ratio': '1:4:4'
        })
        data = response.get_json()
        settings = data['settings']
        assert settings['temperature_f'] == 75
        assert settings['cold_proof_hours'] == 36
        assert settings['feeding_ratio'] == '1:4:4'
        assert settings['fermentation_speed'] == 'fast'
