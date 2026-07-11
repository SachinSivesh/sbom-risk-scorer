"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Applications
    op.create_table(
        'applications',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_applications_name', 'applications', ['name'])

    # SBOMs
    op.create_table(
        'sboms',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('application_id', sa.Uuid(), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename_stored', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('format', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='queued'),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('component_count', sa.Integer(), nullable=True),
        sa.Column('warnings', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_sboms_application_id', 'sboms', ['application_id'])
    op.create_index('idx_sboms_status', 'sboms', ['status'])

    # Dependencies
    op.create_table(
        'dependencies',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('sbom_id', sa.Uuid(), sa.ForeignKey('sboms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(100), nullable=False),
        sa.Column('ecosystem', sa.String(50), nullable=False, server_default='unknown'),
        sa.Column('purl', sa.String(500), nullable=True),
        sa.Column('license_id', sa.String(100), nullable=True),
        sa.Column('is_direct', sa.Boolean(), server_default='false'),
        sa.Column('repo_url', sa.String(500), nullable=True),
    )
    op.create_index('idx_dependencies_sbom_id', 'dependencies', ['sbom_id'])
    op.create_index('idx_dependencies_name_version', 'dependencies', ['name', 'version'])

    # Dependency Edges
    op.create_table(
        'dependency_edges',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('sbom_id', sa.Uuid(), sa.ForeignKey('sboms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_dependency_id', sa.Uuid(), sa.ForeignKey('dependencies.id'), nullable=False),
        sa.Column('to_dependency_id', sa.Uuid(), sa.ForeignKey('dependencies.id'), nullable=False),
        sa.UniqueConstraint('from_dependency_id', 'to_dependency_id', name='uq_edge_pair'),
    )
    op.create_index('idx_edges_sbom_id', 'dependency_edges', ['sbom_id'])

    # Vulnerabilities
    op.create_table(
        'vulnerabilities',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('dependency_id', sa.Uuid(), sa.ForeignKey('dependencies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vuln_id', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('fixed_version', sa.String(100), nullable=True),
        sa.Column('source', sa.String(20), nullable=False, server_default='osv'),
    )
    op.create_index('idx_vulnerabilities_dependency_id', 'vulnerabilities', ['dependency_id'])

    # Maintenance Signals
    op.create_table(
        'maintenance_signals',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('dependency_id', sa.Uuid(), sa.ForeignKey('dependencies.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('last_commit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), server_default='false'),
        sa.Column('release_frequency_days', sa.Integer(), nullable=True),
        sa.Column('maintenance_score', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='UNKNOWN'),
    )

    # Risk Reports
    op.create_table(
        'risk_reports',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('sbom_id', sa.Uuid(), sa.ForeignKey('sboms.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('application_id', sa.Uuid(), sa.ForeignKey('applications.id'), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('vulnerability_subscore', sa.Integer(), nullable=False),
        sa.Column('license_subscore', sa.Integer(), nullable=False),
        sa.Column('maintenance_subscore', sa.Integer(), nullable=False),
        sa.Column('breakdown_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_risk_reports_application_id_created_at', 'risk_reports', ['application_id', 'created_at'])

    # AI Reports
    op.create_table(
        'ai_reports',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('risk_report_id', sa.Uuid(), sa.ForeignKey('risk_reports.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('top_actions_json', sa.JSON(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('fallback_used', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('ai_reports')
    op.drop_table('risk_reports')
    op.drop_table('maintenance_signals')
    op.drop_table('vulnerabilities')
    op.drop_table('dependency_edges')
    op.drop_table('dependencies')
    op.drop_table('sboms')
    op.drop_table('applications')
