"""convert experiment_id from auto-increment to fixed length

Revision ID: 6dca653c92e6
Revises: 97727af70f4d
Create Date: 2022-10-06 15:47:21.228666

This migration converts the primary key `experiment_id` within the Experiments table from an
auto-incrementing primary key to a non-nullable unique-constrained Integer column. This is to
support concurrent experiment creation and avoid collisions.
"""
from alembic import op
import sqlalchemy as sa
import logging

from sqlalchemy import UniqueConstraint, PrimaryKeyConstraint, ForeignKeyConstraint

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

# revision identifiers, used by Alembic.
revision = "6dca653c92e6"
down_revision = "97727af70f4d"
branch_labels = None
depends_on = None


def upgrade():
    # As part of MLflow 2.0 upgrade, the Experiment table's primary key `experiment_id`
    # has changed from an auto-incrementing column to a non-nullable unique-constrained Integer
    # column to support the uuid-based random id generation change.

    # NB: The foreign key on experiment_pk is unnamed. Using the naming_convention feature
    # to provide bound engine specific formatting rules to auto-generated constraints
    naming_convention = {
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
    with op.batch_alter_table(
        "experiment_tags",
        table_args=(
            PrimaryKeyConstraint("key", "experiment_id", name="experiment_tag_pk"),
            ForeignKeyConstraint(
                ["experiment_id", "experiment_pk"],
                ["experiments.experiment_id", "experiments.experiment_id"],
            ),
        ),
        naming_convention=naming_convention,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_experiment_tags_experiment_id_experiments_experiment_id", type_="foreignkey"
        )
        batch_op.alter_column(
            "experiment_id",
            existing_type=sa.Integer,
            type_=sa.BigInteger,
            existing_nullable=False,
            nullable=False,
            existing_autoincrement=True,
            autoincrement=False,
            existing_server_default=None,
            existing_comment=None,
        )

    with op.batch_alter_table("runs") as batch_op:
        batch_op.alter_column(
            "experiment_id",
            existing_type=sa.Integer,
            type_=sa.BigInteger,
            existing_nullable=True,
            nullable=True,
            existing_autoincrement=False,
            autoincrement=False,
            existing_server_default=None,
            existing_comment=None,
        )

    with op.batch_alter_table(
        "experiments",
        table_args=(
            PrimaryKeyConstraint("experiment_id", name="experiment_pk"),
            UniqueConstraint("experiment_id"),
        ),
    ) as batch_op:
        batch_op.alter_column(
            "experiment_id",
            existing_type=sa.Integer,
            type_=sa.BigInteger,
            existing_nullable=False,
            nullable=False,
            existing_autoincrement=True,
            autoincrement=False,
            existing_server_default=None,
            existing_comment=None,
        )

    # Recreate the foreign key and name it for future direct reference
    op.create_foreign_key(
        constraint_name="fk_experiment_tag",
        source_table="experiment_tags",
        referent_table="experiments",
        local_cols=["experiment_id"],
        remote_cols=["experiment_id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    _logger.info("Conversion of experiment_id from autoincrement complete!")


def downgrade():
    pass
