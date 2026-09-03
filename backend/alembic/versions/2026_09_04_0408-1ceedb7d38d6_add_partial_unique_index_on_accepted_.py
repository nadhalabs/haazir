"""add_partial_unique_index_on_accepted_assignment

Revision ID: 1ceedb7d38d6
Revises: 753e58c432b9
Create Date: 2026-09-04 04:08:42.127813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ceedb7d38d6'
down_revision: Union[str, None] = '753e58c432b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Partial unique index: only ONE assignment per booking may have status = 'ACCEPTED'
    op.execute(
        """
        CREATE UNIQUE INDEX uq_booking_single_accepted_assignment
        ON booking_assignments (booking_id)
        WHERE (status = 'ACCEPTED');
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_booking_single_accepted_assignment;")
