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

    def test_preview_standard(self, client):
        response = client.post('/api/preview', json={
            'starter_amount': 100,
            'starter_percent': 20,
            'hydration': 75,
            'salt_percent': 2.2
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['recipe']['total_flour'] == 500.0
        assert data['recipe']['total_water'] == 375.0
        assert data['recipe']['salt'] == 11.0

    def test_preview_with_different_starter(self, client):
        response = client.post('/api/preview', json={
            'starter_amount': 50,
            'starter_percent': 10,
            'hydration': 80,
            'salt_percent': 2.0
        })
        data = response.get_json()
        assert data['recipe']['total_flour'] == 500.0
        assert data['recipe']['total_water'] == 400.0

    def test_preview_invalid_percent(self, client):
        response = client.post('/api/preview', json={
            'starter_amount': 100,
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

    def test_generate_alexandra_cooks_style(self, client):
        """Test generating a schedule matching the Alexandra Cooks recipe."""
        response = client.post('/api/generate', json={
            'starter_amount': 100,
            'starter_percent': 20,
            'hydration': 75,
            'salt_percent': 2.2,
            'existing_starter_amount': 50,
            'feeding_ratio': '1:5:5',
            'start_time': '8:00 PM',
            'temperature_f': 70,
            'cold_proof_hours': 24,
            'flour_type': 'bread flour',
            'enabled_steps': {
                'autolyse': False,
                'rest_after_mix': True,
                'stretch_fold_1': True,
                'stretch_fold_2': True,
                'stretch_fold_3': True,
                'stretch_fold_4': True,
                'pre_shape': True,
                'bench_rest': True
            }
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify ingredients match expected
        ingredients = data['ingredients']
        assert ingredients['total_flour_weight'] == 500.0
        assert ingredients['starter_amount'] == 100.0
        assert ingredients['salt'] == 11.0
        assert ingredients['total_water'] == 375.0

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
            'temperature_f': 75,
            'cold_proof_hours': 36,
            'feeding_ratio': '1:4:4'
        })
        data = response.get_json()
        settings = data['settings']
        assert settings['temperature_f'] == 75
        assert settings['cold_proof_hours'] == 36
        assert settings['feeding_ratio'] == '1:4:4'
