"""empty message

Revision ID: a2f0c41bf38a
Revises: 1ee8f2cc58c0
Create Date: 2022-09-28 17:32:12.314857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2f0c41bf38a'
down_revision = '1ee8f2cc58c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invalid_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('jwt', sa.String(), nullable=False),
    sa.Column('date', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('invalid_tokens')
    # ### end Alembic commands ###
