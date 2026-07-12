"""extend_models_for_datasets

Revision ID: 24b5ed693f92
Revises: 001_initial
Create Date: 2026-07-12 04:48:24.425505
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '24b5ed693f92'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend applications table
    op.add_column('applications', sa.Column('app_id', sa.String(50), nullable=True))
    op.add_column('applications', sa.Column('language', sa.String(50), nullable=True))
    op.add_column('applications', sa.Column('criticality', sa.String(50), nullable=True))
    op.add_column('applications', sa.Column('license_model', sa.String(50), nullable=True))
    op.add_column('applications', sa.Column('business_owner', sa.String(100), nullable=True))
    op.add_column('applications', sa.Column('department', sa.String(100), nullable=True))
    op.add_column('applications', sa.Column('deployment', sa.String(50), nullable=True))
    op.create_index('idx_applications_app_id', 'applications', ['app_id'])

    # 2. Create license_rules table
    op.create_table(
        'license_rules',
        sa.Column('license', sa.String(100), primary_key=True),
        sa.Column('spdx', sa.String(100), nullable=True),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('compatible_with_proprietary', sa.Boolean(), nullable=False),
        sa.Column('viral', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    # 3. Create reference_vulnerabilities table
    op.create_table(
        'reference_vulnerabilities',
        sa.Column('cve_id', sa.String(50), primary_key=True),
        sa.Column('library', sa.String(255), nullable=False),
        sa.Column('affected_versions', sa.JSON(), nullable=True),
        sa.Column('fixed_version', sa.String(100), nullable=True),
        sa.Column('cvss_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('severity', sa.String(50), nullable=True),
        sa.Column('exploitability', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('patch_available', sa.Boolean(), nullable=True),
        sa.Column('published_date', sa.Date(), nullable=True),
    )
    op.create_index('idx_ref_vuln_library', 'reference_vulnerabilities', ['library'])

    # 4. Create reference_dependency_labels table
    op.create_table(
        'reference_dependency_labels',
        sa.Column('dep_id', sa.String(50), primary_key=True),
        sa.Column('application_id', sa.String(50), nullable=False),
        sa.Column('library', sa.String(255), nullable=False),
        sa.Column('version', sa.String(100), nullable=False),
        sa.Column('is_risky', sa.Boolean(), nullable=False),
        sa.Column('risk_type', sa.String(100), nullable=True),
        sa.Column('severity', sa.String(50), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
    )
    op.create_index('idx_ref_dep_labels_app_id', 'reference_dependency_labels', ['application_id'])

    # 5. Create reference_sbom_dependencies table
    op.create_table(
        'reference_sbom_dependencies',
        sa.Column('dep_id', sa.String(50), primary_key=True),
        sa.Column('application_id', sa.String(50), nullable=False),
        sa.Column('application_name', sa.String(255), nullable=False),
        sa.Column('library', sa.String(255), nullable=False),
        sa.Column('version', sa.String(100), nullable=False),
        sa.Column('license', sa.String(100), nullable=True),
        sa.Column('dependency_type', sa.String(50), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.Column('transitive_deps', sa.Text(), nullable=True),
    )
    op.create_index('idx_ref_sbom_deps_app_id', 'reference_sbom_dependencies', ['application_id'])

    # 6. Create reference_transitive_dependencies table
    op.create_table(
        'reference_transitive_dependencies',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('parent_library', sa.String(255), nullable=False),
        sa.Column('parent_version', sa.String(100), nullable=False),
        sa.Column('child_library', sa.String(255), nullable=False),
        sa.Column('child_version', sa.String(100), nullable=False),
        sa.Column('application_id', sa.String(50), nullable=False),
    )
    op.create_index('idx_ref_trans_deps_app_id', 'reference_transitive_dependencies', ['application_id'])


def downgrade() -> None:
    op.drop_table('reference_transitive_dependencies')
    op.drop_table('reference_sbom_dependencies')
    op.drop_table('reference_dependency_labels')
    op.drop_table('reference_vulnerabilities')
    op.drop_table('license_rules')
    
    op.drop_index('idx_applications_app_id', 'applications')
    op.drop_column('applications', 'deployment')
    op.drop_column('applications', 'department')
    op.drop_column('applications', 'business_owner')
    op.drop_column('applications', 'license_model')
    op.drop_column('applications', 'criticality')
    op.drop_column('applications', 'language')
    op.drop_column('applications', 'app_id')
