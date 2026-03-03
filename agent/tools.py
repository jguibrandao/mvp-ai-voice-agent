from datetime import datetime, timedelta

from livekit.agents import function_tool, RunContext

MOCK_APPOINTMENTS: dict[str, list[dict]] = {}


def _generate_slots(date_str: str) -> list[str]:
    booked = {
        appt["time"]
        for appt in MOCK_APPOINTMENTS.get(date_str, [])
    }
    all_slots = [f"{h}:00" for h in range(9, 17)]
    return [s for s in all_slots if s not in booked]


@function_tool()
async def check_availability(
    context: RunContext,
    date: str,
) -> dict:
    """Check available appointment slots for a given date.

    Args:
        date: The date to check in YYYY-MM-DD format.
    """
    try:
        parsed = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}

    if parsed < datetime.now().date():
        return {"error": "Cannot check availability for past dates."}

    if parsed > datetime.now().date() + timedelta(days=60):
        return {"error": "Cannot book more than 60 days in advance."}

    slots = _generate_slots(date)
    if not slots:
        return {"date": date, "available_slots": [], "message": "No slots available."}

    return {"date": date, "available_slots": slots}


@function_tool()
async def book_appointment(
    context: RunContext,
    patient_name: str,
    date: str,
    time: str,
    procedure: str,
) -> dict:
    """Book a dental appointment for a patient.

    Args:
        patient_name: Full name of the patient.
        date: Appointment date in YYYY-MM-DD format.
        time: Appointment time in HH:MM format.
        procedure: Type of procedure (cleaning, checkup, filling, extraction, whitening, consultation).
    """
    available = _generate_slots(date)
    if time not in available:
        return {"error": f"Time slot {time} is not available on {date}."}

    appointment = {
        "patient_name": patient_name,
        "date": date,
        "time": time,
        "procedure": procedure,
        "confirmation_id": f"SLD-{len(MOCK_APPOINTMENTS.get(date, [])) + 1:04d}",
    }

    MOCK_APPOINTMENTS.setdefault(date, []).append(appointment)

    return {
        "status": "confirmed",
        "confirmation_id": appointment["confirmation_id"],
        "message": f"Appointment booked for {patient_name} on {date} at {time} for {procedure}.",
    }


CLINIC_INFO = {
    "hours": "Monday to Friday 8:00 AM - 6:00 PM, Saturday 9:00 AM - 2:00 PM. Closed on Sundays.",
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


@function_tool()
async def transfer_call(
    context: RunContext,
    department: str,
    reason: str,
) -> dict:
    """Transfer the call to a specific department.

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
            "error": f"Unknown department '{department}'. Available: front desk, dentist, billing, manager."
        }

    return {
        "status": "transferring",
        "destination": dest,
        "reason": reason,
        "message": f"Transferring you to {dest}. Please hold.",
    }
