from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, ARRAY
from sqlalchemy import Computed
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
    CheckConstraint,
    JSON,
    func,
)


Base = declarative_base()


class UserModel(Base):  # noqa: D101
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    picture_url = Column(String(512), nullable=True)
    google_sub = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Onboarding fields
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime, nullable=True)
    needs_nutritional_plan = Column(Boolean, nullable=True)
    sex = Column(String(10), nullable=True)  # 'male', 'female', 'other'
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    activity_level = Column(String(20), nullable=True)  # 'sedentary', 'light', 'moderate', 'active', 'very_active'
    sport = Column(String(100), nullable=True)
    goals = Column(JSON, nullable=True)  # Array of strings
    available_foods = Column(JSON, nullable=True)  # Array of strings
    target_calories = Column(Integer, nullable=True)


class RefreshTokenModel(Base):  # noqa: D101
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    jti = Column(String(64), unique=True, index=True)
    revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class EmailTokenModel(Base):  # noqa: D101
    __tablename__ = "email_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token = Column(String(128), unique=True, index=True)
    purpose = Column(String(32))  # confirm_email | reset_password
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# Food

class FoodTypeEnum(str, PyEnum):
    SIMPLE = "simple"
    COMPOSITE = "composite"
    VARIANT = "variant"


class QtyUnitEnum(str, PyEnum):
    G = "g"
    ML = "ml"
    PORTION = "portion"


class JobStatusEnum(str, PyEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class RowStatusEnum(str, PyEnum):
    IMPORTED = "imported"
    SKIPPED = "skipped"
    ERROR = "error"


class MealTypeEnum(str, PyEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    OTHER = "other"


FoodType = SAEnum(FoodTypeEnum, name="food_type_enum", values_callable=lambda e: [m.value for m in e])
QtyUnit  = SAEnum(QtyUnitEnum,  name="qty_unit_enum", values_callable=lambda e: [m.value for m in e])
MealType = SAEnum(MealTypeEnum, name="meal_type_enum", values_callable=lambda e: [m.value for m in e])
JobStatus = SAEnum(JobStatusEnum, name="job_status_enum", values_callable=lambda e: [m.value for m in e])
RowStatus = SAEnum(RowStatusEnum, name="row_status_enum",values_callable=lambda e: [m.value for m in e])


class Foods(Base):
    __tablename__ = "foods"
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    type = Column(FoodType, nullable=False, default=FoodTypeEnum.SIMPLE)
    parent_food_id = Column(Integer, ForeignKey("foods.id", ondelete="RESTRICT"))
    kcal_per_100g = Column(Numeric(10, 2), CheckConstraint("kcal_per_100g >= 0"))
    carbs_g_per_100g = Column(Numeric(10, 3), CheckConstraint("carbs_g_per_100g >= 0"))
    protein_g_per_100g = Column(Numeric(10, 3), CheckConstraint("protein_g_per_100g >= 0"))
    fat_g_per_100g = Column(Numeric(10, 3), CheckConstraint("fat_g_per_100g >= 0"))
    fiber_g_per_100g = Column(Numeric(10, 3), CheckConstraint("fiber_g_per_100g >= 0"))
    sodium_mg_per_100g = Column(Numeric(10, 2), CheckConstraint("sodium_mg_per_100g >= 0"))
    kcal_per_100ml = Column(Numeric(10, 2), CheckConstraint("kcal_per_100ml >= 0"))
    carbs_g_per_100ml = Column(Numeric(10, 3), CheckConstraint("carbs_g_per_100ml >= 0"))
    protein_g_per_100ml = Column(Numeric(10, 3), CheckConstraint("protein_g_per_100ml >= 0"))
    fat_g_per_100ml = Column(Numeric(10, 3), CheckConstraint("fat_g_per_100ml >= 0"))
    fiber_g_per_100ml = Column(Numeric(10, 3), CheckConstraint("fiber_g_per_100ml >= 0"))
    sodium_mg_per_100ml = Column(Numeric(10, 2), CheckConstraint("sodium_mg_per_100ml >= 0"))
    extra_nutrients = Column(JSON)
    created_by = Column(Integer, ForeignKey("users.id"))
    version = Column(Integer, nullable=False, server_default="1")
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"))
    search_vector = Column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(description,''))",
            persisted=True,
        ),
        nullable=False,
    )
    
    
    __table_args__ = (
        Index("idx_foods_name", "name"),
        # plain GIN on tsvector works without pg_trgm
        Index("idx_foods_search_gin", search_vector, postgresql_using="gin"),
    )

class FoodAliases(Base):
    __tablename__ = "food_aliases"
    
    id = Column(Integer, primary_key=True)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    alias = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("uq_food_aliases_food_lower_alias", food_id, func.lower(alias), unique=True),
        Index("idx_food_alias", alias),
    )


class FoodPortions(Base):
    __tablename__ = "food_portions"
    
    id = Column(Integer, primary_key=True)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    label = Column(Text, nullable=False)
    grams_equivalent = Column(Numeric(10, 3))
    ml_equivalent = Column(Numeric(10, 3))
    is_default = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("uq_food_portions_food_lower_label", food_id, func.lower(label), unique=True),
        Index("idx_food_portions_food", food_id),
        Index("uq_food_portions_one_default_per_food", food_id, unique=True, postgresql_where=text("is_default")),
    )



class UserCustomFoods(Base):
    __tablename__ = "user_custom_foods"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    kcal_per_100g = Column(Numeric(10, 2))
    carbs_g_per_100g = Column(Numeric(10, 3))
    protein_g_per_100g = Column(Numeric(10, 3))
    fat_g_per_100g = Column(Numeric(10, 3))
    fiber_g_per_100g = Column(Numeric(10, 3))
    sodium_mg_per_100g = Column(Numeric(10, 2))
    kcal_per_100ml = Column(Numeric(10, 2))
    carbs_g_per_100ml = Column(Numeric(10, 3))
    protein_g_per_100ml = Column(Numeric(10, 3))
    fat_g_per_100ml = Column(Numeric(10, 3))
    fiber_g_per_100ml = Column(Numeric(10, 3))
    sodium_mg_per_100ml = Column(Numeric(10, 2))
    extra_nutrients = Column(JSON)
    is_temporary = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    __table_args__ = (
        Index("idx_ucf_user", "user_id"),
        Index("idx_ucf_name", "name"),
        # Index("idx_ucf_name_trgm", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
    )


class UserConsumptions(Base):
    __tablename__ = "user_consumptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    occurred_at = Column(DateTime, nullable=False)
    local_date = Column(Date, nullable=False)
    meal = Column(MealType, nullable=False)
    note = Column(Text)
    total_kcal = Column(Integer, nullable=False, server_default="0")
    total_carbs_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_protein_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_fat_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_fiber_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_sodium_mg = Column(Numeric(12, 0), nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    __table_args__ = (
        Index("idx_uc_user_date", "user_id", "local_date"),
        Index("idx_uc_user_time", "user_id", "occurred_at"),
    )


class ConsumptionItems(Base):
    __tablename__ = "consumption_items"
    
    id = Column(Integer, primary_key=True)
    consumption_id = Column(Integer, ForeignKey("user_consumptions.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="RESTRICT"))
    custom_food_id = Column(Integer, ForeignKey("user_custom_foods.id", ondelete="RESTRICT"))
    original_name = Column(Text)
    quantity = Column(Numeric(12, 5))
    unit = Column(QtyUnit)
    portion_id = Column(Integer, ForeignKey("food_portions.id", ondelete="SET NULL"))
    original_portion_label = Column(Text)
    grams = Column(Numeric(12, 3))
    ml = Column(Numeric(12, 3))
    using_food_version = Column(Integer)
    kcal = Column(Integer, nullable=False)
    carbs_g = Column(Numeric(10, 1), nullable=False)
    protein_g = Column(Numeric(10, 1), nullable=False)
    fat_g = Column(Numeric(10, 1), nullable=False)
    fiber_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    sodium_mg = Column(Numeric(12, 0), nullable=False, server_default="0")
    position = Column(Integer)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    __table_args__ = (
        CheckConstraint("(food_id IS NOT NULL) <> (custom_food_id IS NOT NULL)", name="ck_item_food_or_custom"),
        CheckConstraint("unit IS DISTINCT FROM 'portion' OR portion_id IS NOT NULL", name="ck_item_portion_requires_id"),
        Index("idx_ci_consumption", "consumption_id"),
        Index("idx_ci_food", "food_id"),
        Index("idx_ci_custom", "custom_food_id"),
    )


class DailySummaries(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    local_date = Column(Date, nullable=False)
    meals_count = Column(Integer, nullable=False, server_default="0")
    items_count = Column(Integer, nullable=False, server_default="0")
    total_kcal = Column(Integer, nullable=False, server_default="0")
    total_carbs_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_protein_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_fat_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_fiber_g = Column(Numeric(10, 1), nullable=False, server_default="0")
    total_sodium_mg = Column(Numeric(12, 0), nullable=False, server_default="0")
    pct_kcal_carbs = Column(Numeric(5, 2))
    pct_kcal_protein = Column(Numeric(5, 2))
    pct_kcal_fat = Column(Numeric(5, 2))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    __table_args__ = (
        UniqueConstraint("user_id", "local_date"),
        Index("idx_ds_user_date", "user_id", "local_date"),
    )


class FoodComponents(Base):
    __tablename__ = "food_components"
    
    id = Column(Integer, primary_key=True)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(Integer, ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(12, 5), nullable=False)
    unit = Column(QtyUnit, nullable=False)
    portion_id = Column(Integer, ForeignKey("food_portions.id", ondelete="SET NULL"))
    note = Column(Text)
    position = Column(Integer)
    
    __table_args__ = (
        UniqueConstraint("food_id", "component_id", "portion_id", "unit"),
        Index("idx_components_parent", "food_id"),
        Index("idx_components_child", "component_id"),
    )


class FoodModifierGroups(Base):
    __tablename__ = "food_modifier_groups"
    
    id = Column(Integer, primary_key=True)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    is_exclusive = Column(Boolean, nullable=False, server_default="false")
    min_select = Column(Integer, nullable=False, server_default="0")
    max_select = Column(Integer)
    position = Column(Integer)
    
    __table_args__ = (
        Index("uq_food_modifier_groups_food_lower_name", food_id, func.lower(name), unique=True),
    )


class FoodModifiers(Base):
    __tablename__ = "food_modifiers"
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("food_modifier_groups.id", ondelete="CASCADE"), nullable=False)
    modifier_food_id = Column(Integer, ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False)
    position = Column(Integer)

    __table_args__ = (
        UniqueConstraint("group_id", "modifier_food_id", name="uq_food_modifiers_group_modifier"),
    )


class UnitConversions(Base):
    __tablename__ = "unit_conversions"
    
    id = Column(Integer, primary_key=True)
    from_unit = Column(Text, nullable=False)
    to_unit = Column(Text, nullable=False)
    factor = Column(Numeric(20, 10), nullable=False)
    
    __table_args__ = (
        Index(
            "uq_unit_conversions_from_to_lower",
            func.lower(from_unit),
            func.lower(to_unit),
            unique=True,
        ),
    )


class ExternalSources(Base):
    __tablename__ = "external_sources"
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    base_url = Column(Text)
    kind = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))


class ImportJobs(Base):
    __tablename__ = "import_jobs"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("external_sources.id", ondelete="SET NULL"))
    started_by = Column(Integer, ForeignKey("users.id"))
    source_uri = Column(Text)
    status = Column(JobStatus, nullable=False, server_default="queued")
    imported_count = Column(Integer, nullable=False, server_default="0")
    skipped_count = Column(Integer, nullable=False, server_default="0")
    error_count = Column(Integer, nullable=False, server_default="0")
    started_at = Column(DateTime, nullable=False, server_default=text("now()"))
    finished_at = Column(DateTime)
    
    __table_args__ = (Index("idx_import_jobs_source", "source_id"),)


class ImportJobItems(Base):
    __tablename__ = "import_job_items"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False)
    line_no = Column(Integer)
    raw_payload = Column(JSON)
    status = Column(JobStatus)
    error_message = Column(Text)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    __table_args__ = (Index("idx_import_items_job", "job_id"),)


class ExternalFoodMap(Base):
    __tablename__ = "external_food_map"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("external_sources.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(Text, nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    
    __table_args__ = (UniqueConstraint("source_id", "external_id"),)


class AuditLogs(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(Text, nullable=False)
    diff = Column(JSON)
    ts = Column(DateTime, nullable=False, server_default=text("now()"))
    
    __table_args__ = (Index("idx_audit_entity", "entity_type", "entity_id", "ts"),)


class FoodVersions(Base):
    __tablename__ = "food_versions"
    
    id = Column(Integer, primary_key=True)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    __table_args__ = (UniqueConstraint("food_id", "version"),)


