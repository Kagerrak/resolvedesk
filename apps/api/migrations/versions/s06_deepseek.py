"""Enable the user-selected DeepSeek provider; retain historical provider labels."""

from alembic import op

revision = "s06_deepseek"
down_revision = "s06_generation"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("generation_run_mode_check", "generation_run")
    op.create_check_constraint(
        "generation_run_mode_check", "generation_run", "mode IN ('fixture','openai','deepseek')"
    )


def downgrade():
    # Refuse to mislabel or delete DeepSeek history during downgrade.
    op.drop_constraint("generation_run_mode_check", "generation_run")
    op.create_check_constraint(
        "generation_run_mode_check", "generation_run", "mode IN ('fixture','openai')"
    )
