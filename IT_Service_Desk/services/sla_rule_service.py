from dao.sla_rule_dao import SLARuleDAO
from models.sla_rule import SLARule
from dao.user_dao import UserDAO


class SLARuleService:

    DEFAULT_RULES = {
        "LOW": {
            "response_time_minutes": 1440,
            "resolution_time_minutes": 4320,
        },
        "MEDIUM": {
            "response_time_minutes": 480,
            "resolution_time_minutes": 2880,
        },
        "HIGH": {
            "response_time_minutes": 240,
            "resolution_time_minutes": 1440,
        },
        "CRITICAL": {
            "response_time_minutes": 60,
            "resolution_time_minutes": 240,
        },
    }

    VALID_PRIORITIES = set(DEFAULT_RULES.keys())

    @staticmethod
    def _get_admin(admin_id):
        user = UserDAO.get_by_id(admin_id)
        if not user:
            raise ValueError("User not found.")
        if not user.is_active:
            raise PermissionError("User account is inactive.")
        if not user.role or user.role.name != "ADMIN":
            raise PermissionError("Only administrators can manage SLA rules.")
        return user

    @staticmethod
    def ensure_default_rules():
        """Seed baseline rules only when the SLA table is completely empty."""
        existing_rules = SLARuleDAO.get_all()
        if existing_rules:
            return existing_rules

        rules = []
        for priority, values in SLARuleService.DEFAULT_RULES.items():
            rule = SLARule(
                priority=priority,
                response_time_minutes=values["response_time_minutes"],
                resolution_time_minutes=values["resolution_time_minutes"],
            )
            rules.append(SLARuleDAO.create(rule))

        return rules

    @staticmethod
    def get_all_rules(admin_id=None):
        if admin_id is not None:
            SLARuleService._get_admin(admin_id)
        return SLARuleDAO.get_all()

    @staticmethod
    def get_rule_by_priority(priority):
        priority = (priority or "").strip().upper()
        if priority not in SLARuleService.VALID_PRIORITIES:
            raise ValueError("Invalid SLA priority.")
        return SLARuleDAO.get_by_priority(priority)

    @staticmethod
    def create_rule(
        admin_id,
        priority,
        response_time_minutes,
        resolution_time_minutes,
    ):
        SLARuleService._get_admin(admin_id)

        priority = (priority or "").strip().upper()
        if priority not in SLARuleService.VALID_PRIORITIES:
            raise ValueError("Invalid SLA priority.")

        try:
            response_time_minutes = int(response_time_minutes)
            resolution_time_minutes = int(resolution_time_minutes)
        except (TypeError, ValueError):
            raise ValueError("SLA times must be whole numbers in minutes.")

        if response_time_minutes <= 0 or resolution_time_minutes <= 0:
            raise ValueError("SLA times must be greater than zero.")

        if response_time_minutes > resolution_time_minutes:
            raise ValueError(
                "Response time cannot be greater than resolution time."
            )

        if SLARuleDAO.get_by_priority(priority):
            raise ValueError(f"An SLA rule for {priority} already exists.")

        return SLARuleDAO.create(
            SLARule(
                priority=priority,
                response_time_minutes=response_time_minutes,
                resolution_time_minutes=resolution_time_minutes,
            )
        )

    @staticmethod
    def update_rule(
        admin_id,
        rule_id,
        response_time_minutes,
        resolution_time_minutes,
    ):
        SLARuleService._get_admin(admin_id)
        rule = SLARuleDAO.get_by_id(rule_id)
        if not rule:
            raise ValueError("SLA rule not found.")

        try:
            response_time_minutes = int(response_time_minutes)
            resolution_time_minutes = int(resolution_time_minutes)
        except (TypeError, ValueError):
            raise ValueError("SLA times must be whole numbers in minutes.")

        if response_time_minutes <= 0 or resolution_time_minutes <= 0:
            raise ValueError("SLA times must be greater than zero.")

        if response_time_minutes > resolution_time_minutes:
            raise ValueError(
                "Response time cannot be greater than resolution time."
            )

        rule.response_time_minutes = response_time_minutes
        rule.resolution_time_minutes = resolution_time_minutes
        return SLARuleDAO.update(rule)

    @staticmethod
    def delete_rule(admin_id, rule_id):
        SLARuleService._get_admin(admin_id)
        rule = SLARuleDAO.get_by_id(rule_id)
        if not rule:
            raise ValueError("SLA rule not found.")
        return SLARuleDAO.delete(rule)
