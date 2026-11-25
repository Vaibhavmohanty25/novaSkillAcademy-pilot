
from datetime import (
    datetime,
    timedelta,
    timezone,
    time
)

from uuid import uuid5, NAMESPACE_URL

from backend.database import SessionLocal, init_db
from backend.models import AppointmentSlot


IST = timezone(timedelta(hours=5, minutes=30))

COUNSELLOR = "Admissions Counsellor"

HOURS = [10, 11, 12, 14, 15, 16]


def main():

    init_db()

    db = SessionLocal()

    created = 0

    try:

        today = datetime.now(IST).date()

        for offset in range(7):

            day = today + timedelta(days=offset)

            for hour in HOURS:

                local_time = datetime.combine(
                    day,
                    time(hour=hour),
                    tzinfo=IST
                )

                if local_time <= datetime.now(IST):
                    continue

                utc_time = local_time.astimezone(
                    timezone.utc
                ).replace(tzinfo=None)

                slot_id = str(
                    uuid5(
                        NAMESPACE_URL,
                        f"{COUNSELLOR}:{utc_time.isoformat()}"
                    )
                )

                if db.get(AppointmentSlot, slot_id):
                    continue

                slot = AppointmentSlot(
                    id=slot_id,
                    counsellor=COUNSELLOR,
                    start_time=utc_time
                )

                db.add(slot)

                created += 1

        db.commit()

        print(
            f"Successfully created "
            f"{created} appointment slots."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
