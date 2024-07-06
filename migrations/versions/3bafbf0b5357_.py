"""empty message

Revision ID: 3bafbf0b5357
Revises: d687ce1b0e03
Create Date: 2024-07-07 00:39:48.934368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bafbf0b5357'
down_revision: Union[str, None] = 'd687ce1b0e03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('car_camera', sa.Column('car_id', sa.Uuid(), nullable=False))
    op.drop_constraint('car_camera_vehicle_id_fkey', 'car_camera', type_='foreignkey')
    op.create_foreign_key(None, 'car_camera', 'car', ['car_id'], ['id'])
    op.drop_column('car_camera', 'vehicle_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('car_camera', sa.Column('vehicle_id', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'car_camera', type_='foreignkey')
    op.create_foreign_key('car_camera_vehicle_id_fkey', 'car_camera', 'car', ['vehicle_id'], ['id'])
    op.drop_column('car_camera', 'car_id')
    # ### end Alembic commands ###