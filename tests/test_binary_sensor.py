"""Tests for the binary_sensor platform."""
from unittest.mock import MagicMock

import pytest

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStatus,
    DhcpStatus,
)
from custom_components.adguard_home_extended.binary_sensor import (
    BINARY_SENSOR_TYPES,
    AdGuardHomeBinarySensor,
    async_setup_entry,
)
from custom_components.adguard_home_extended.const import DOMAIN
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData


class TestBinarySensorEntityDescriptions:
    """Test binary sensor entity descriptions."""

    def test_running_sensor_is_on(self):
        """Test running binary sensor when running."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus.from_dict({"running": True})

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "running")
        assert description.is_on_fn(data) is True

    def test_running_sensor_is_off(self):
        """Test running binary sensor when not running."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus.from_dict({"running": False})

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "running")
        assert description.is_on_fn(data) is False

    def test_protection_enabled_sensor_is_on(self):
        """Test protection_enabled binary sensor when enabled."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus.from_dict({"protection_enabled": True})

        description = next(
            d for d in BINARY_SENSOR_TYPES if d.key == "protection_enabled"
        )
        assert description.is_on_fn(data) is True

    def test_protection_enabled_sensor_is_off(self):
        """Test protection_enabled binary sensor when disabled."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus.from_dict({"protection_enabled": False})

        description = next(
            d for d in BINARY_SENSOR_TYPES if d.key == "protection_enabled"
        )
        assert description.is_on_fn(data) is False

    def test_dhcp_enabled_sensor_is_on(self):
        """Test dhcp_enabled binary sensor when enabled."""
        data = AdGuardHomeData()
        data.dhcp = DhcpStatus.from_dict({"enabled": True})

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "dhcp_enabled")
        assert description.is_on_fn(data) is True

    def test_dhcp_enabled_sensor_is_off(self):
        """Test dhcp_enabled binary sensor when disabled."""
        data = AdGuardHomeData()
        data.dhcp = DhcpStatus.from_dict({"enabled": False})

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "dhcp_enabled")
        assert description.is_on_fn(data) is False

    def test_all_sensors_have_required_fields(self):
        """Test all binary sensor descriptions have required fields."""
        for description in BINARY_SENSOR_TYPES:
            assert description.key is not None
            assert description.translation_key is not None
            assert description.icon is not None
            assert description.is_on_fn is not None
            assert callable(description.is_on_fn)


class TestBinarySensorNoneHandling:
    """Test binary sensor handling of None data."""

    def test_running_sensor_none_status(self):
        """Test running sensor returns None when status is None."""
        data = AdGuardHomeData()

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "running")
        assert description.is_on_fn(data) is None

    def test_protection_enabled_sensor_none_status(self):
        """Test protection_enabled sensor returns None when status is None."""
        data = AdGuardHomeData()

        description = next(
            d for d in BINARY_SENSOR_TYPES if d.key == "protection_enabled"
        )
        assert description.is_on_fn(data) is None

    def test_dhcp_enabled_sensor_none_dhcp(self):
        """Test dhcp_enabled sensor returns None when dhcp is None."""
        data = AdGuardHomeData()

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "dhcp_enabled")
        assert description.is_on_fn(data) is None


class TestAdGuardHomeBinarySensor:
    """Test the AdGuardHomeBinarySensor class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_123"
        coordinator.device_info = {
            "identifiers": {(DOMAIN, "test_entry_123")},
            "name": "AdGuard Home",
        }
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus.from_dict(
            {
                "running": True,
                "protection_enabled": True,
            }
        )
        coordinator.data = data
        return coordinator

    def test_sensor_init(self, mock_coordinator):
        """Test binary sensor initialization."""
        description = BINARY_SENSOR_TYPES[0]  # running sensor
        sensor = AdGuardHomeBinarySensor(mock_coordinator, description)

        assert sensor.entity_description == description
        assert sensor._attr_unique_id == "test_entry_123_running"
        assert sensor._attr_device_info == mock_coordinator.device_info
        assert sensor._attr_has_entity_name is True

    def test_sensor_is_on_true(self, mock_coordinator):
        """Test binary sensor is_on returns True."""
        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "running")
        sensor = AdGuardHomeBinarySensor(mock_coordinator, description)

        assert sensor.is_on is True

    def test_sensor_is_on_false(self, mock_coordinator):
        """Test binary sensor is_on returns False."""
        # Set running to False
        mock_coordinator.data.status = AdGuardHomeStatus.from_dict({"running": False})

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "running")
        sensor = AdGuardHomeBinarySensor(mock_coordinator, description)

        assert sensor.is_on is False

    def test_sensor_is_on_none(self, mock_coordinator):
        """Test binary sensor is_on returns None when data unavailable."""
        mock_coordinator.data = AdGuardHomeData()  # No status

        description = next(d for d in BINARY_SENSOR_TYPES if d.key == "running")
        sensor = AdGuardHomeBinarySensor(mock_coordinator, description)

        assert sensor.is_on is None


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        return hass

    @pytest.fixture
    def mock_entry(self):
        """Create a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_456"
        return entry

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_456"
        coordinator.device_info = {
            "identifiers": {(DOMAIN, "test_entry_456")},
        }
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus.from_dict({"running": True})
        coordinator.data = data
        return coordinator

    @pytest.mark.asyncio
    async def test_setup_creates_entities(
        self, mock_hass, mock_entry, mock_coordinator
    ):
        """Test that setup creates all binary sensor entities."""
        mock_hass.data = {DOMAIN: {mock_entry.entry_id: mock_coordinator}}

        entities_added = []

        def capture_entities(entities):
            entities_added.extend(list(entities))

        await async_setup_entry(mock_hass, mock_entry, capture_entities)

        # Should create one entity per description
        assert len(entities_added) == len(BINARY_SENSOR_TYPES)

    @pytest.mark.asyncio
    async def test_setup_creates_correct_entity_types(
        self, mock_hass, mock_entry, mock_coordinator
    ):
        """Test that setup creates correct entity types."""
        mock_hass.data = {DOMAIN: {mock_entry.entry_id: mock_coordinator}}

        entities_added = []

        def capture_entities(entities):
            entities_added.extend(list(entities))

        await async_setup_entry(mock_hass, mock_entry, capture_entities)

        for entity in entities_added:
            assert isinstance(entity, AdGuardHomeBinarySensor)

    @pytest.mark.asyncio
    async def test_setup_creates_entities_with_correct_keys(
        self, mock_hass, mock_entry, mock_coordinator
    ):
        """Test that setup creates entities with correct keys."""
        mock_hass.data = {DOMAIN: {mock_entry.entry_id: mock_coordinator}}

        entities_added = []

        def capture_entities(entities):
            entities_added.extend(list(entities))

        await async_setup_entry(mock_hass, mock_entry, capture_entities)

        entity_keys = {e.entity_description.key for e in entities_added}
        expected_keys = {"running", "protection_enabled", "dhcp_enabled"}

        assert entity_keys == expected_keys
