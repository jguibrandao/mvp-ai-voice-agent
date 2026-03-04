import asyncio
import re
from datetime import datetime, timedelta

from livekit.agents import function_tool, RunContext

MOCK_APPOINTMENTS: dict[str, list[dict]] = {}

WEEKDAY_HOURS = (8, 18)
SATURDAY_HOURS = (9, 14)

_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def _normalize_time(raw: str) -> str:
    raw = raw.strip()
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p"):
        try:
            return datetime.strptime(raw, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return raw


def _resolve_date(raw: str) -> str:
    clean = raw.strip().lower()
    today = datetime.now().date()

    if clean == "today":
        return today.strftime("%Y-%m-%d")
    if clean in ("tomorrow", "tmrw"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    next_match = re.match(r"next\s+(\w+)", clean)
    if next_match:
        day_name = next_match.group(1)
        if day_name in _WEEKDAYS:
            target = _WEEKDAYS[day_name]
            days_ahead = (target - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    for day_name, day_num in _WEEKDAYS.items():
        if clean == day_name:
            days_ahead = (day_num - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    return raw


def _generate_slots(date_str: str) -> list[str]:
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return []

    weekday = parsed.weekday()

    if weekday == 6:
        return []

    if weekday == 5:
        start_h, end_h = SATURDAY_HOURS
    else:
        start_h, end_h = WEEKDAY_HOURS

    booked = {appt["time"] for appt in MOCK_APPOINTMENTS.get(date_str, [])}
    all_slots = [f"{h:02d}:00" for h in range(start_h, end_h)]
    return [s for s in all_slots if s not in booked]


def _format_slot_12h(slot_24h: str) -> str:
    result = datetime.strptime(slot_24h, "%H:%M").strftime("%I:%M %p")
    if result.startswith("0"):
        result = result[1:]
    return result


def _day_label(date_str: str) -> str:
    parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    return parsed.strftime("%A, %B %d, %Y")


@function_tool()
async def check_availability(
    context: RunContext,
    date: str,
) -> dict:
    """Check available appointment slots for a given date.

    Args:
        date: The date to check. Accepts YYYY-MM-DD, or relative like "today", "tomorrow", "next Monday", "Friday".
    """
    date = _resolve_date(date)
    try:
        parsed = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "available": False,
            "reason": "I couldn't understand that date. Could you give me the date in a format like 2026-03-10?",
        }

    today = datetime.now().date()

    if parsed < today:
        return {
            "available": False,
            "reason": f"That date ({_day_label(date)}) is in the past. Could you pick a future date?",
        }

    if parsed > today + timedelta(days=60):
        return {
            "available": False,
            "reason": "We can only schedule up to 60 days out. Could you pick a closer date?",
        }

    if parsed.weekday() == 6:
        return {
            "available": False,
            "reason": f"{_day_label(date)} is a Sunday and the clinic is closed. We're open Monday through Saturday.",
        }

    slots = _generate_slots(date)
    if not slots:
        return {
            "date": date,
            "day": _day_label(date),
            "available": False,
            "reason": "All slots are booked for that day. Would you like to try another date?",
        }

    display_slots = [_format_slot_12h(s) for s in slots]
    hours = "8 AM to 6 PM" if parsed.weekday() < 5 else "9 AM to 2 PM"

    return {
        "date": date,
        "day": _day_label(date),
        "available": True,
        "clinic_hours": hours,
        "slots": display_slots,
        "total_open": len(display_slots),
    }


@function_tool()
async def book_appointment(
    context: RunContext,
    patient_name: str,
    date: str,
    time: str,
    procedure: str,
) -> dict:
    """Book a dental appointment for a patient. Always call check_availability first.

    Args:
        patient_name: Full name of the patient.
        date: Appointment date. Accepts YYYY-MM-DD, or relative like "today", "tomorrow", "next Monday".
        time: Appointment time in HH:MM 24-hour format (e.g. 09:00, 14:00).
        procedure: Type of procedure (cleaning, checkup, filling, extraction, whitening, consultation).
    """
    date = _resolve_date(date)
    normalized_time = _normalize_time(time)

    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "booked": False,
            "reason": "I couldn't understand that date. Could you say it again?",
        }

    if parsed_date < datetime.now().date():
        return {
            "booked": False,
            "reason": "That date is in the past. Let's pick a future date.",
        }

    if parsed_date.weekday() == 6:
        return {
            "booked": False,
            "reason": "The clinic is closed on Sundays.",
        }

    available = _generate_slots(date)
    if normalized_time not in available:
        display_available = [_format_slot_12h(s) for s in available[:5]]
        if available:
            return {
                "booked": False,
                "reason": f"That time slot isn't available on {_day_label(date)}. "
                          f"Open slots include: {', '.join(display_available)}.",
            }
        return {
            "booked": False,
            "reason": f"There are no slots available on {_day_label(date)}. Would you like to try another day?",
        }

    confirmation_id = f"SLD-{len(MOCK_APPOINTMENTS.get(date, [])) + 1:04d}"

    appointment = {
        "patient_name": patient_name,
        "date": date,
        "time": normalized_time,
        "procedure": procedure,
        "confirmation_id": confirmation_id,
    }

    MOCK_APPOINTMENTS.setdefault(date, []).append(appointment)

    display_time = _format_slot_12h(normalized_time)
    return {
        "booked": True,
        "confirmation_id": confirmation_id,
        "patient_name": patient_name,
        "date": _day_label(date),
        "time": display_time,
        "procedure": procedure,
    }


CLINIC_INFO = {
    "hours": "Monday to Friday 8:00 AM to 6:00 PM, Saturday 9:00 AM to 2:00 PM. Closed on Sundays.",
    "location": "123 Bright Smile Avenue, Suite 200, Downtown. Free parking available in the building garage.",
    "services": "General dentistry, cleanings, fillings, extractions, teeth whitening, root canals, crowns, veneers, and orthodontic consultations.",
    "insurance": "We accept Delta Dental, Cigna, Aetna, MetLife, and most major PPO plans. We also offer a self-pay discount of 15%.",
    "pricing": "Cleanings start at $120, consultations at $80. We offer payment plans for procedures over $500.",
    "emergency": "For dental emergencies during business hours, call us and press 1. After hours, call our emergency line at 555-0199.",
}


@function_tool()
async def get_clinic_info(
    context: RunContext,
    topic: str,
) -> dict:
    """Get information about SmileLine Dental Clinic.

    Args:
        topic: The topic to get info about (hours, location, services, insurance, pricing, emergency).
    """
    topic_lower = topic.lower().strip()

    for key, value in CLINIC_INFO.items():
        if key in topic_lower or topic_lower in key:
            return {"topic": key, "info": value}

    return {
        "topic": topic,
        "info": "I can help with information about our hours, location, services, insurance, pricing, or emergency procedures. Which would you like to know about?",
    }


async def _end_session_after_farewell(session, delay: float = 10.0) -> None:
    await asyncio.sleep(delay)
    await session.aclose()


@function_tool()
async def transfer_call(
    context: RunContext,
    department: str,
    reason: str,
) -> dict:
    """Transfer the call to a specific department. This ends the current conversation.

    Args:
        department: Department to transfer to (front_desk, dentist, billing, manager).
        reason: Brief reason for the transfer.
    """
    departments = {
        "front_desk": "Front Desk - ext. 100",
        "dentist": "Dr. Williams' Office - ext. 201",
        "billing": "Billing Department - ext. 300",
        "manager": "Office Manager - ext. 400",
    }

    dept_key = department.lower().strip().replace(" ", "_")
    dest = departments.get(dept_key)

    if not dest:
        return {
            "transferred": False,
            "reason": f"I'm not sure which department you mean by '{department}'. I can transfer you to the front desk, dentist, billing, or manager.",
        }

    asyncio.create_task(_end_session_after_farewell(context.session))

    return {
        "transferred": True,
        "destination": dest,
        "reason": reason,
        "instructions": "Say a warm farewell. Tell the caller you are transferring them now, they may hear a brief silence, and thank them for calling SmileLine Dental.",
    }


@function_tool()
async def end_call(
    context: RunContext,
    reason: str,
) -> dict:
    """End the call politely. Use when the caller confirms they don't need anything else.

    Args:
        reason: Brief reason the call is ending (e.g. "caller is done", "all questions answered").
    """
    asyncio.create_task(_end_session_after_farewell(context.session))

    return {
        "ending": True,
        "reason": reason,
        "instructions": "Say a warm goodbye. Thank them for calling SmileLine Dental and wish them a great day. Do NOT ask any more questions.",
    }
