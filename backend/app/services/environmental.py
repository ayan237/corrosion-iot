"""
Environmental Context Service.

The DHT11 sensor provides temperature and humidity.  These values are
contextual — they modify inspection PRIORITY, not the detection itself.

The system must NOT claim that temperature or humidity alone predicts
corrosion. See PRD sections 12 and 30.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.config import get_settings


@dataclass
class EnvironmentalContext:
    temperature: float | None
    humidity: float | None
    note: str           # human-readable contextual statement
    priority_modifier: float  # additive factor for severity engine (−10 to +10)


def assess_environment(
    temperature: float | None,
    humidity: float | None,
) -> EnvironmentalContext:
    """
    Produce an environmental context note and a small priority modifier.

    Rules (prototype — see PRD section 12):
    - Elevated humidity (>= threshold) → slight priority increase
    - High temperature (>= threshold)  → slight priority increase
    - Both elevated                    → moderate priority increase
    - Normal or missing readings       → no effect
    """
    settings = get_settings()

    if temperature is None and humidity is None:
        return EnvironmentalContext(
            temperature=None,
            humidity=None,
            note="No environmental data provided.",
            priority_modifier=0.0,
        )

    notes: list[str] = []
    modifier = 0.0

    if humidity is not None:
        if humidity >= settings.humidity_elevated_threshold:
            notes.append(
                f"Elevated humidity ({humidity:.0f}%) may increase corrosion risk "
                f"and maintenance priority."
            )
            modifier += 4.0
        else:
            notes.append(f"Humidity within normal range ({humidity:.0f}%).")

    if temperature is not None:
        if temperature >= settings.temp_high_threshold:
            notes.append(
                f"High temperature ({temperature:.1f}°C) may accelerate "
                f"corrosion processes."
            )
            modifier += 3.0
        else:
            notes.append(f"Temperature within normal range ({temperature:.1f}°C).")

    if modifier >= 6.0:
        notes.append(
            "Combined elevated temperature and humidity conditions suggest "
            "increased inspection priority."
        )

    return EnvironmentalContext(
        temperature=temperature,
        humidity=humidity,
        note=" ".join(notes),
        priority_modifier=min(modifier, 10.0),
    )


def validate_sensor_values(
    temperature: float | None,
    humidity: float | None,
) -> list[str]:
    """
    Return a list of validation error messages.
    Returns empty list if all provided values are valid.
    """
    settings = get_settings()
    errors: list[str] = []

    if temperature is not None:
        if not (settings.temp_min <= temperature <= settings.temp_max):
            errors.append(
                f"Temperature {temperature}°C is outside valid range "
                f"({settings.temp_min}–{settings.temp_max}°C)."
            )

    if humidity is not None:
        if not (settings.humidity_min <= humidity <= settings.humidity_max):
            errors.append(
                f"Humidity {humidity}% is outside valid range "
                f"({settings.humidity_min}–{settings.humidity_max}%)."
            )

    return errors
