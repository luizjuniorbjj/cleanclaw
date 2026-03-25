"""Model validation tests."""
import pytest
from pydantic import ValidationError


# ============================================
# CleaningClientCreate
# ============================================

def test_client_create_minimal():
    """CleaningClientCreate only requires first_name."""
    from app.modules.cleaning.models.clients import CleaningClientCreate
    client = CleaningClientCreate(first_name="Jane")
    assert client.first_name == "Jane"
    assert client.last_name is None
    assert client.email is None
    assert client.source == "manual"  # default


def test_client_create_full_fields():
    """CleaningClientCreate accepts all enhanced S2.3 fields."""
    from app.modules.cleaning.models.clients import CleaningClientCreate
    client = CleaningClientCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="555-1234",
        preferred_contact="phone",
        has_pets=True,
        pet_details="Golden Retriever, friendly",
        tags=["vip", "recurring"],
        city="New Orleans",
        state="LA",
        zip_code="70115",
        property_type="house",
        bedrooms=3,
        bathrooms=2.0,
        source="booking_page",
    )
    assert client.first_name == "John"
    assert client.preferred_contact == "phone"
    assert client.has_pets is True
    assert client.tags == ["vip", "recurring"]
    assert client.source == "booking_page"


def test_client_create_rejects_missing_required():
    """CleaningClientCreate raises ValidationError when first_name is missing."""
    from app.modules.cleaning.models.clients import CleaningClientCreate
    with pytest.raises(ValidationError):
        CleaningClientCreate()  # first_name is required


def test_client_create_rejects_invalid_preferred_contact():
    """preferred_contact must be one of phone|email|text|whatsapp."""
    from app.modules.cleaning.models.clients import CleaningClientCreate
    with pytest.raises(ValidationError):
        CleaningClientCreate(first_name="Test", preferred_contact="telegram")


def test_client_create_rejects_invalid_property_type():
    """property_type must match the allowed pattern."""
    from app.modules.cleaning.models.clients import CleaningClientCreate
    with pytest.raises(ValidationError):
        CleaningClientCreate(first_name="Test", property_type="castle")


def test_client_create_rejects_invalid_source():
    """source must match allowed values."""
    from app.modules.cleaning.models.clients import CleaningClientCreate
    with pytest.raises(ValidationError):
        CleaningClientCreate(first_name="Test", source="unknown_source")


def test_client_create_default_country():
    """country defaults to US."""
    from app.modules.cleaning.models.clients import CleaningClientCreate
    client = CleaningClientCreate(first_name="Ana")
    assert client.country == "US"


# ============================================
# CleaningServiceCreate
# ============================================

def test_service_create_minimal():
    """CleaningServiceCreate requires only name."""
    from app.modules.cleaning.models.services import CleaningServiceCreate
    svc = CleaningServiceCreate(name="Deep Clean")
    assert svc.name == "Deep Clean"
    assert svc.category == "residential"  # default
    assert svc.price_unit == "flat"  # default
    assert svc.is_active is True


def test_service_create_rejects_invalid_category():
    """category must be one of residential|commercial|specialized|addon."""
    from app.modules.cleaning.models.services import CleaningServiceCreate
    with pytest.raises(ValidationError):
        CleaningServiceCreate(name="X", category="industrial")


def test_service_create_rejects_negative_price():
    """base_price must be >= 0."""
    from app.modules.cleaning.models.services import CleaningServiceCreate
    with pytest.raises(ValidationError):
        CleaningServiceCreate(name="X", base_price=-10)


# ============================================
# BookingCreate
# ============================================

def test_booking_create_requires_fields():
    """BookingCreate requires client_id, service_id, scheduled_date, scheduled_start."""
    from app.modules.cleaning.models.bookings import BookingCreate
    booking = BookingCreate(
        client_id="client-uuid",
        service_id="service-uuid",
        scheduled_date="2026-04-01",
        scheduled_start="09:00",
    )
    assert booking.client_id == "client-uuid"
    assert booking.source == "manual"  # default
    assert booking.assigned_team == []
    assert booking.discount_amount == 0.0


def test_booking_create_rejects_invalid_source():
    """source must match the allowed booking sources."""
    from app.modules.cleaning.models.bookings import BookingCreate
    with pytest.raises(ValidationError):
        BookingCreate(
            client_id="c",
            service_id="s",
            scheduled_date="2026-04-01",
            scheduled_start="09:00",
            source="walk_in",  # not in the allowed set
        )
